#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${REGISTRY:-${AZURE_ENV_ACR_NAME:-}}"
IMAGE_TAG="${IMAGE_TAG:-${AZURE_ENV_IMAGETAG:-latest_v2}}"
REPO="${REPO:-${AZURE_ENV_FRONTEND_IMAGE_REPO:-ccsa-ecom-frontend}}"

if [[ -z "$REGISTRY" && -n "${AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT:-}" ]]; then
  REGISTRY="${AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT%.azurecr.io}"
fi

if [[ -z "$REGISTRY" ]]; then
  echo "Set REGISTRY, or AZURE_ENV_ACR_NAME, or AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CTX="$APP_ROOT/frontend"
IMAGE_REF="${REPO}:${IMAGE_TAG}"

echo "az acr build --registry $REGISTRY --image $IMAGE_REF --file Dockerfile --platform linux $CTX"
az acr build --registry "$REGISTRY" --image "$IMAGE_REF" --file Dockerfile --platform linux "$CTX"

echo "Set AZURE_ENV_IMAGETAG=$IMAGE_TAG (and AZURE_ENV_FRONTEND_IMAGE_REPO=$REPO if non-default) then azd provision or update the web app."
