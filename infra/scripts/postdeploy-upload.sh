#!/usr/bin/env bash
set -euo pipefail
# ---------------------------------------------
# Configuration & azd environment
# ---------------------------------------------
# If running under azd, AZD_ENV_NAME will be set; load the env file if present.
if [[ -n "${AZD_ENV_NAME:-}" && -f ".azure/${AZD_ENV_NAME}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source ".azure/${AZD_ENV_NAME}/.env"
  set +a
fi
# Inputs (from Bicep outputs via azd env, or exported manually)
SEARCH_ENDPOINT="${SEARCH_ENDPOINT:-${searchEndpoint:-}}"
SEARCH_API_KEY="${SEARCH_API_KEY:-${searchAdminKey:-}}"
INDEX_NAME="${INDEX_NAME:-company-policies}"

# Azure AI Search API version (change if you require newer features)
API_VERSION="${API_VERSION:-2023-11-01}"

if [[ -z "${SEARCH_ENDPOINT}" ]]; then
  echo "ERROR: SEARCH_ENDPOINT/searchEndpoint is not set. Ensure your Bicep outputs it and 'azd' has synced env." >&2
  exit 1
fi
# ---------------------------------------------
# Locate the data file (with spaces in name)
# ---------------------------------------------
# Resolve relative to repo root or current directory; handle script being nested under scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FILEPATH="${REPO_ROOT}/data/Return Policy.txt"
if [[ ! -f "${FILEPATH}" ]]; then
  # Fallback to CWD: ./data/Return Policy.txt
  if [[ -f "data/Return Policy.txt" ]]; then
    FILEPATH="data/Return Policy.txt"
  else
    echo "ERROR: File not found: data/Return Policy.txt (checked ${FILEPATH} too)" >&2
    exit 1
  fi
fi

# Read file content safely
# Note: if the file is very large, consider chunking or an indexer approach
CONTENT="$(cat "${FILEPATH}")"
FILENAME="$(basename "${FILEPATH}")"

# ---------------------------------------------
# Auth header: either API key or Entra ID token
# ---------------------------------------------
AUTH_HEADER=()
if [[ -n "${SEARCH_API_KEY:-}" ]]; then
  AUTH_HEADER=(-H "api-key: ${SEARCH_API_KEY}")
else
  # Attempt Entra ID (RBAC). Requires 'az' and appropriate role on the Search service.
  if command -v az >/dev/null 2>&1; then
    TOKEN="$(az account get-access-token --resource https://search.azure.com --query accessToken -o tsv 2>/dev/null || true)"
    if [[ -n "${TOKEN}" ]]; then
      AUTH_HEADER=(-H "Authorization: Bearer ${TOKEN}")
    else
      echo "ERROR: Neither SEARCH_API_KEY is set nor could we acquire an AAD token via 'az'." >&2
      exit 1
    fi
  else
    echo "ERROR: 'az' not found and SEARCH_API_KEY not set. Install Azure CLI or provide admin key." >&2
    exit 1
  fi
fi

# ---------------------------------------------
# Dependencies check for helper tools
# ---------------------------------------------
need_jq=false
if ! command -v jq >/dev/null 2>&1; then
  need_jq=true
fi

# uuid generator (platform differences)
gen_uuid() {
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen
  elif command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import uuid
print(uuid.uuid4())
PY
  else
    # Fallback (not cryptographically strong)
    date +%s%N | sha1sum | awk '{print $1}'
  fi
}

DOC_ID="$(gen_uuid)"

# ---------------------------------------------
# 1) Create or Update the index (idempotent)
# ---------------------------------------------
# We'll construct the index JSON. If jq is missing, we fallback to sed.
INDEX_JSON_TEMPLATE='{
  "name": "company-policies",
  "fields": [
    { "name": "id", "type": "Edm.String", "key": true },
    { "name": "title", "type": "Edm.String", "searchable": true },
    { "name": "content", "type": "Edm.String", "searchable": true }
  ]
}'

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "${INDEX_JSON_TEMPLATE}" > "${TMP_DIR}/index.json"

if [[ "${INDEX_NAME}" != "company-policies" ]]; then
  if [[ "${need_jq}" == "false" ]]; then
    jq --arg name "${INDEX_NAME}" '.name = $name' "${TMP_DIR}/index.json" > "${TMP_DIR}/index_named.json"
  else
    # crude fallback if jq isn't available
    sed "s/\"name\": \"company-policies\"/\"name\": \"${INDEX_NAME//\//\\/}\"/g" "${TMP_DIR}/index.json" > "${TMP_DIR}/index_named.json"
  fi
else
  cp "${TMP_DIR}/index.json" "${TMP_DIR}/index_named.json"
fi

curl -sS -X PUT \
  "${SEARCH_ENDPOINT}/indexes/${INDEX_NAME}?api-version=${API_VERSION}" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  --data-binary @"${TMP_DIR}/index_named.json" \
  >/dev/null

# ---------------------------------------------
# 2) Upload the document to the index
# ---------------------------------------------
# Build the payload safely. Prefer jq to handle escaping.
if [[ "${need_jq}" == "false" ]]; then
  jq -n \
    --arg id "${DOC_ID}" \
    --arg title "${FILENAME}" \
    --arg content "${CONTENT}" \
    '{ value: [ { "@search.action":"upload", id:$id, title:$title, content:$content } ] }' \
    > "${TMP_DIR}/docs.json"
else
  # Fallback without jq: best-effort escaping for quotes and backslashes
  esc() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
  }
  ESC_TITLE="$(esc "${FILENAME}")"
  ESC_CONTENT="$(esc "${CONTENT}")"
  cat > "${TMP_DIR}/docs.json" <<JSON
{
  "value": [
    {
      "@search.action": "upload",
      "id": "${DOC_ID}",
      "title": "${ESC_TITLE}",
      "content": "${ESC_CONTENT}"
    }
  ]
}
JSON
fi

curl -sS -X POST \
  "${SEARCH_ENDPOINT}/indexes/${INDEX_NAME}/docs/index?api-version=${API_VERSION}" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  --data-binary @"${TMP_DIR}/docs.json" \
  >/dev/null
echo "✅ Uploaded '${FILEPATH}' to Azure AI Search index '${INDEX_NAME}' (doc id: ${DOC_ID})."
