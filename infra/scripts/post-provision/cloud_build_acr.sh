#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${RESOURCE_GROUP_NAME:-}" && -n "${AZURE_RESOURCE_GROUP:-}" ]]; then
  export RESOURCE_GROUP_NAME="$AZURE_RESOURCE_GROUP"
fi
if [[ -z "${AZURE_RESOURCE_GROUP:-}" && -n "${RESOURCE_GROUP_NAME:-}" ]]; then
  export AZURE_RESOURCE_GROUP="$RESOURCE_GROUP_NAME"
fi
TAG="${AZURE_ENV_IMAGETAG:-latest_v2}"
SCENARIO="${AZURE_ENV_SCENARIO:-ecommerce}"
REG="${ACR_NAME:?ACR_NAME missing after provision.}"
RG="${RESOURCE_GROUP_NAME:?RESOURCE_GROUP_NAME missing after provision.}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

R_CHAT_BE="${AZURE_ENV_CHAT_BACKEND_IMAGE_REPO:-chat-backend}"
R_CHAT_FE="${AZURE_ENV_CHAT_FRONTEND_IMAGE_REPO:-chat-frontend}"
R_SCENARIO_BE="${AZURE_ENV_SCENARIO_BACKEND_IMAGE_REPO:-scenario-backend}"
R_SCENARIO_FE="${AZURE_ENV_SCENARIO_FRONTEND_IMAGE_REPO:-scenario-frontend}"

run_build() {
  local repo_name="$1"
  local ctx="$2"
  local dockerfile="${3:-${ctx}/Dockerfile}"
  local extra_args=()
  if [ "${repo_name}" = "${R_SCENARIO_FE}" ]; then
    extra_args=(--build-arg "VITE_SCENARIO=${SCENARIO}")
  fi
  if [ ! -f "${dockerfile}" ]; then
    echo "Dockerfile not found: ${dockerfile}" >&2
    exit 1
  fi
  local dockerfile_arg="Dockerfile"
  if [ "${dockerfile}" != "${ctx}/Dockerfile" ]; then
    dockerfile_arg="${dockerfile#${ctx}/}"
  fi
  local image_ref="${repo_name}:${TAG}"
  echo "az acr build (cwd=${ctx}) --registry \"${REG}\" --image \"${image_ref}\" --file ${dockerfile_arg} --platform linux ."
  ( cd "${ctx}" && az acr build --registry "${REG}" --image "${image_ref}" --file "${dockerfile_arg}" --platform linux "${extra_args[@]}" . )
}

run_build "${R_CHAT_BE}" "${ROOT}" "${ROOT}/chat-app/backend/Dockerfile"
run_build "${R_CHAT_FE}" "${ROOT}/chat-app/frontend"
run_build "${R_SCENARIO_BE}" "${ROOT}/scenario-app/backend"
run_build "${R_SCENARIO_FE}" "${ROOT}" "${ROOT}/scenario-app/frontend/Dockerfile"

for app in "${CHAT_API_APP_NAME:-}" "${CHAT_WEB_APP_NAME:-}" "${SCENARIO_API_APP_NAME:-}" "${SCENARIO_WEB_APP_NAME:-}"; do
  if [ -n "${app}" ]; then
    az webapp restart --resource-group "${RG}" --name "${app}"
  fi
done
