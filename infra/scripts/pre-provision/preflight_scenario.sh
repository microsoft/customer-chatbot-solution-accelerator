#!/usr/bin/env bash
set -euo pipefail

scenario="${AZURE_ENV_SCENARIO:-}"
if [[ -z "${scenario// }" ]]; then
    scenario="ecommerce"
fi
scenario="$(echo "$scenario" | xargs | tr '[:upper:]' '[:lower:]')"

case "$scenario" in
    ecommerce|healthcare|banking) ;;
    *) echo "ERROR: Invalid AZURE_ENV_SCENARIO '$scenario'. Use: ecommerce, healthcare, or banking." >&2; exit 1 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
MANIFEST_PATH="$REPO_ROOT/scenarios/$scenario/manifest.json"

if [[ ! -f "$MANIFEST_PATH" ]]; then
    echo "ERROR: Scenario pack not found: $MANIFEST_PATH" >&2
    exit 1
fi

echo "Deployment scenario: $scenario"
echo "To deploy a different scenario, set AZURE_ENV_SCENARIO to one of: ecommerce, healthcare, banking before your first 'azd up' on this environment (default is ecommerce)."
