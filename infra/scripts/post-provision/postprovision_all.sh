#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
chmod +x "$HERE/cloud_build_acr.sh" 2>/dev/null || true
chmod +x "$HERE/sync_azd_hook_env.sh" 2>/dev/null || true
chmod +x "$HERE/postprovision_data_agents.sh" 2>/dev/null || true
source "$HERE/sync_azd_hook_env.sh"
"$HERE/cloud_build_acr.sh"
# "$HERE/postprovision_data_agents.sh"
