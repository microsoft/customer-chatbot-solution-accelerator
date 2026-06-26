$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $here '..' '..' '..')).Path
. (Join-Path $here 'sync_azd_hook_env.ps1')
Sync-AzdHookEnv -ProjectRoot $repoRoot
# & (Join-Path $repoRoot 'infra' 'scripts' 'pre-provision' 'preflight_scenario.ps1')
# if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $here 'cloud_build_acr.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
# & (Join-Path $here 'postprovision_data_agents.ps1')
# if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
