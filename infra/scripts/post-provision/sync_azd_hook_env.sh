#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
PY="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
if [[ -z "$PY" ]]; then
  echo "sync_azd_hook_env.sh: python not found" >&2
  exit 1
fi
eval "$(cd "$ROOT" && azd env get-values -o json | "$PY" -c "
import json, sys, shlex
for k, v in json.load(sys.stdin).items():
    if v is None:
        continue
    print('export ' + k + '=' + shlex.quote(str(v)))
")"
if [[ -n "${RESOURCE_GROUP_NAME:-}" && -z "${AZURE_RESOURCE_GROUP:-}" ]]; then
  export AZURE_RESOURCE_GROUP="$RESOURCE_GROUP_NAME"
fi
if [[ -n "${AZURE_RESOURCE_GROUP:-}" && -z "${RESOURCE_GROUP_NAME:-}" ]]; then
  export RESOURCE_GROUP_NAME="$AZURE_RESOURCE_GROUP"
fi
