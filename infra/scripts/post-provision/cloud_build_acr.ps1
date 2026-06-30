$ErrorActionPreference = 'Stop'
$env:AZURE_CORE_NO_COLOR = 'true'
if (-not $env:PYTHONIOENCODING) {
  $env:PYTHONIOENCODING = 'utf-8'
}
if ([string]::IsNullOrWhiteSpace($env:RESOURCE_GROUP_NAME) -and -not [string]::IsNullOrWhiteSpace($env:AZURE_RESOURCE_GROUP)) {
    $env:RESOURCE_GROUP_NAME = $env:AZURE_RESOURCE_GROUP
}
if ([string]::IsNullOrWhiteSpace($env:AZURE_RESOURCE_GROUP) -and -not [string]::IsNullOrWhiteSpace($env:RESOURCE_GROUP_NAME)) {
    $env:AZURE_RESOURCE_GROUP = $env:RESOURCE_GROUP_NAME
}
$tag = $env:AZURE_ENV_IMAGE_TAG
if ([string]::IsNullOrWhiteSpace($tag)) { $tag = 'latest_v3' }
$scenario = $env:AZURE_ENV_SCENARIO
if ([string]::IsNullOrWhiteSpace($scenario)) { $scenario = 'ecommerce' }
$reg = $env:ACR_NAME
if ([string]::IsNullOrWhiteSpace($reg)) { throw 'ACR_NAME missing after provision.' }
$rg = $env:RESOURCE_GROUP_NAME
if ([string]::IsNullOrWhiteSpace($rg)) { throw 'RESOURCE_GROUP_NAME missing after provision.' }
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..' '..')).Path

$rChatBe = $(if ([string]::IsNullOrWhiteSpace($env:AZURE_ENV_CHAT_BACKEND_IMAGE_REPO)) { 'chat-backend' } else { $env:AZURE_ENV_CHAT_BACKEND_IMAGE_REPO })
$rChatFe = $(if ([string]::IsNullOrWhiteSpace($env:AZURE_ENV_CHAT_FRONTEND_IMAGE_REPO)) { 'chat-frontend' } else { $env:AZURE_ENV_CHAT_FRONTEND_IMAGE_REPO })
$rScenarioBe = $(if ([string]::IsNullOrWhiteSpace($env:AZURE_ENV_SCENARIO_BACKEND_IMAGE_REPO)) { 'scenario-backend' } else { $env:AZURE_ENV_SCENARIO_BACKEND_IMAGE_REPO })
$rScenarioFe = $(if ([string]::IsNullOrWhiteSpace($env:AZURE_ENV_SCENARIO_FRONTEND_IMAGE_REPO)) { 'scenario-frontend' } else { $env:AZURE_ENV_SCENARIO_FRONTEND_IMAGE_REPO })

$scenarioFeDockerfile = Join-Path $repoRoot 'scenario-app' 'frontend' 'Dockerfile'
$chatBeDockerfile = Join-Path $repoRoot 'chat-app' 'backend' 'Dockerfile'
$builds = @(
  @{ Repo = $rChatBe; Ctx = $repoRoot; Dockerfile = $chatBeDockerfile }
  @{ Repo = $rChatFe; Ctx = (Join-Path $repoRoot 'chat-app' 'frontend') }
  @{ Repo = $rScenarioBe; Ctx = (Join-Path $repoRoot 'scenario-app' 'backend') }
  @{ Repo = $rScenarioFe; Ctx = $repoRoot; Dockerfile = $scenarioFeDockerfile }
)

foreach ($b in $builds) {
  $ctxFull = (Resolve-Path -LiteralPath $b.Ctx).Path
  $dockerfile = if ($b.Dockerfile) { $b.Dockerfile } else { Join-Path $ctxFull 'Dockerfile' }
  if (-not (Test-Path -LiteralPath $dockerfile)) {
    throw "Dockerfile not found: $dockerfile"
  }
  $dockerfileArg = if ($b.Dockerfile) {
    (Resolve-Path -LiteralPath $dockerfile).Path.Substring($ctxFull.Length).TrimStart('\', '/')
  } else {
    'Dockerfile'
  }
  $imageRef = "$($b.Repo):$tag"
  $buildArgs = @()
  if ($b.Repo -eq $rScenarioFe) {
    $buildArgs = @('--build-arg', "VITE_SCENARIO=$scenario")
  }
  Write-Host "az acr build (cwd=$ctxFull) --registry `"$reg`" --image `"$imageRef`" --file $dockerfileArg --platform linux --no-logs ."
  Push-Location $ctxFull
  try {
    if ($buildArgs.Count -gt 0) {
      $buildResult = az acr build --registry "$reg" --image "$imageRef" --file "$dockerfileArg" --platform linux --no-logs @buildArgs . | ConvertFrom-Json
    } else {
      $buildResult = az acr build --registry "$reg" --image "$imageRef" --file "$dockerfileArg" --platform linux --no-logs . | ConvertFrom-Json
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $status = $buildResult.status
    $runId = $buildResult.runId
    Write-Host "ACR build $runId ($imageRef): $status"
    if ($status -ne 'Succeeded') {
      throw "ACR build failed for $imageRef (run $runId): $status"
    }
  }
  finally {
    Pop-Location
  }
}

@($env:CHAT_API_APP_NAME, $env:CHAT_WEB_APP_NAME, $env:SCENARIO_API_APP_NAME, $env:SCENARIO_WEB_APP_NAME) | ForEach-Object {
  if (-not [string]::IsNullOrWhiteSpace($_)) {
    az webapp restart --resource-group $rg --name $_
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
}
