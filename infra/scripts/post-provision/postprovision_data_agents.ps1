$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..' '..')).Path
Set-Location $repoRoot

$isUploadDataScriptSuccess = $true
try {
  & (Join-Path $repoRoot 'infra/scripts/post-provision/data_scripts/run_upload_data_scripts.ps1')
  if ($LASTEXITCODE -ne 0) {
    $isUploadDataScriptSuccess = $false
    Write-Host "Upload data script failed with exit code $LASTEXITCODE" -ForegroundColor Red
  }
} catch {
  $isUploadDataScriptSuccess = $false
  Write-Host "Upload data script failed: $($_.Exception.Message)" -ForegroundColor Red
}

$isCreateAgentsScriptSuccess = $true
try {
  & (Join-Path $repoRoot 'infra/scripts/post-provision/agent_scripts/run_create_agents_scripts.ps1')
  if ($LASTEXITCODE -ne 0) {
    $isCreateAgentsScriptSuccess = $false
    Write-Host "Create agents script failed with exit code $LASTEXITCODE" -ForegroundColor Red
  }
} catch {
  $isCreateAgentsScriptSuccess = $false
  Write-Host "Create agents script failed: $($_.Exception.Message)" -ForegroundColor Red
}

if (-not $isUploadDataScriptSuccess -or -not $isCreateAgentsScriptSuccess) {
  Write-Host "One or more post-provision scripts failed. Please check the logs above for details." -ForegroundColor Red

  if (-not $isUploadDataScriptSuccess) {
    Write-Host "Upload data script failed." -ForegroundColor Red
    Write-Host "To retry the upload data script, run the following command:" -ForegroundColor Yellow
    Write-Host "`n    infra/scripts/post-provision/data_scripts/run_upload_data_scripts.ps1`n" -ForegroundColor Yellow
  }

  if (-not $isCreateAgentsScriptSuccess) {
    Write-Host "Create agents script failed." -ForegroundColor Red
    Write-Host "To retry the create agents script, run the following command:" -ForegroundColor Yellow
    Write-Host "`n    infra/scripts/post-provision/agent_scripts/run_create_agents_scripts.ps1`n" -ForegroundColor Yellow
  }

  exit 1
}

$CHAT_WEB_APP_URL = $(azd env get-value CHAT_WEB_APP_URL)
$SCENARIO_WEB_APP_URL = $(azd env get-value SCENARIO_WEB_APP_URL)

Write-Host "`nPost-Deployment scripts completed successfully." -ForegroundColor Green
Write-Host "`nYou can now access the Chat Web App and Scenario Web App using the following URLs:" -ForegroundColor Green
Write-Host "`n  Chat Web App URL: $CHAT_WEB_APP_URL"
Write-Host "  Scenario Web App URL: $SCENARIO_WEB_APP_URL`n"