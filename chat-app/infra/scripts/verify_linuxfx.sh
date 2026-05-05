#!/usr/bin/env bash
set -euo pipefail

get_azd() {
  local k="$1"
  azd env get-value "$k" 2>/dev/null || true
}

RG="$(get_azd RESOURCE_GROUP_NAME)"
if [[ -z "$RG" ]]; then
  RG="$(get_azd AZURE_RESOURCE_GROUP)"
fi
if [[ -z "$RG" ]]; then
  echo "RESOURCE_GROUP_NAME or AZURE_RESOURCE_GROUP not in azd env." >&2
  exit 1
fi

SUFFIX="$(get_azd SOLUTION_NAME)"
if [[ -z "$SUFFIX" ]]; then
  echo "SOLUTION_NAME not in azd env." >&2
  exit 1
fi

FRONTEND_NAME="app-${SUFFIX}"
API_NAME="$(get_azd API_APP_NAME)"
if [[ -z "$API_NAME" ]]; then
  API_NAME="api-${SUFFIX}"
fi

FE="$(az webapp config show -g "$RG" -n "$FRONTEND_NAME" --query linuxFxVersion -o tsv 2>/dev/null || true)"
BE="$(az webapp config show -g "$RG" -n "$API_NAME" --query linuxFxVersion -o tsv 2>/dev/null || true)"

echo "Frontend ($FRONTEND_NAME) linuxFxVersion: $FE"
echo "Backend  ($API_NAME) linuxFxVersion: $BE"

URL="$(get_azd WEB_APP_URL)"
if [[ -n "$URL" ]]; then
  echo "WEB_APP_URL: $URL"
fi
