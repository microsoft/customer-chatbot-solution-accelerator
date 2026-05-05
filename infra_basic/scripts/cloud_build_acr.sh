#!/usr/bin/env bash
set -euo pipefail
TAG="${AZURE_ENV_IMAGETAG:-latest_v2}"
REG="${ACR_NAME:?ACR_NAME missing after provision.}"
RG="${RESOURCE_GROUP_NAME:?RESOURCE_GROUP_NAME missing after provision.}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

R_CHAT_BE="${AZURE_ENV_CHAT_BACKEND_IMAGE_REPO:-ccsa-chat-backend}"
R_CHAT_FE="${AZURE_ENV_CHAT_FRONTEND_IMAGE_REPO:-ccsa-chat-frontend}"
R_ECOM_BE="${AZURE_ENV_ECOMMERCE_BACKEND_IMAGE_REPO:-ccsa-ecom-backend}"
R_ECOM_FE="${AZURE_ENV_ECOMMERCE_FRONTEND_IMAGE_REPO:-ccsa-ecom-frontend}"

run_build() {
  local repo_name="$1"
  local ctx="$2"
  local dockerfile="${ctx}/Dockerfile"
  if [ ! -f "${dockerfile}" ]; then
    echo "Dockerfile not found: ${dockerfile}" >&2
    exit 1
  fi
  local image_ref="${repo_name}:${TAG}"
  echo "az acr build (cwd=${ctx}) --registry \"${REG}\" --image \"${image_ref}\" --file Dockerfile --platform linux ."
  ( cd "${ctx}" && az acr build --registry "${REG}" --image "${image_ref}" --file Dockerfile --platform linux . )
}

run_build "${R_CHAT_BE}" "${ROOT}/chat-app/backend"
run_build "${R_CHAT_FE}" "${ROOT}/chat-app/frontend"
run_build "${R_ECOM_BE}" "${ROOT}/ecommerce-app/backend"
run_build "${R_ECOM_FE}" "${ROOT}/ecommerce-app/frontend"

for app in "${CHAT_API_APP_NAME:-}" "${CHAT_WEB_APP_NAME:-}" "${ECOMMERCE_API_APP_NAME:-}" "${ECOMMERCE_WEB_APP_NAME:-}"; do
  if [ -n "${app}" ]; then
    az webapp restart --resource-group "${RG}" --name "${app}"
  fi
done
