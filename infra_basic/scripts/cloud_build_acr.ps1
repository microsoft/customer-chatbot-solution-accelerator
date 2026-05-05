$ErrorActionPreference = 'Stop'
$tag = $env:AZURE_ENV_IMAGETAG
if ([string]::IsNullOrWhiteSpace($tag)) { $tag = 'latest_v2' }
$reg = $env:ACR_NAME
if ([string]::IsNullOrWhiteSpace($reg)) { throw 'ACR_NAME missing after provision.' }
$rg = $env:RESOURCE_GROUP_NAME
if ([string]::IsNullOrWhiteSpace($rg)) { throw 'RESOURCE_GROUP_NAME missing after provision.' }
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path

$rChatBe = $(if ([string]::IsNullOrWhiteSpace($env:AZURE_ENV_CHAT_BACKEND_IMAGE_REPO)) { 'ccsa-chat-backend' } else { $env:AZURE_ENV_CHAT_BACKEND_IMAGE_REPO })
$rChatFe = $(if ([string]::IsNullOrWhiteSpace($env:AZURE_ENV_CHAT_FRONTEND_IMAGE_REPO)) { 'ccsa-chat-frontend' } else { $env:AZURE_ENV_CHAT_FRONTEND_IMAGE_REPO })
$rEcomBe = $(if ([string]::IsNullOrWhiteSpace($env:AZURE_ENV_ECOMMERCE_BACKEND_IMAGE_REPO)) { 'ccsa-ecom-backend' } else { $env:AZURE_ENV_ECOMMERCE_BACKEND_IMAGE_REPO })
$rEcomFe = $(if ([string]::IsNullOrWhiteSpace($env:AZURE_ENV_ECOMMERCE_FRONTEND_IMAGE_REPO)) { 'ccsa-ecom-frontend' } else { $env:AZURE_ENV_ECOMMERCE_FRONTEND_IMAGE_REPO })

$builds = @(
  @{ Repo = $rChatBe; Ctx = (Join-Path $repoRoot 'chat-app' 'backend') }
  @{ Repo = $rChatFe; Ctx = (Join-Path $repoRoot 'chat-app' 'frontend') }
  @{ Repo = $rEcomBe; Ctx = (Join-Path $repoRoot 'ecommerce-app' 'backend') }
  @{ Repo = $rEcomFe; Ctx = (Join-Path $repoRoot 'ecommerce-app' 'frontend') }
)

foreach ($b in $builds) {
  $ctxFull = (Resolve-Path -LiteralPath $b.Ctx).Path
  $dockerfile = Join-Path $ctxFull 'Dockerfile'
  if (-not (Test-Path -LiteralPath $dockerfile)) {
    throw "Dockerfile not found: $dockerfile"
  }
  $imageRef = "$($b.Repo):$tag"
  Write-Host "az acr build (cwd=$ctxFull) --registry `"$reg`" --image `"$imageRef`" --file Dockerfile --platform linux ."
  Push-Location $ctxFull
  try {
    az acr build --registry "$reg" --image "$imageRef" --file Dockerfile --platform linux .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
  finally {
    Pop-Location
  }
}

@($env:CHAT_API_APP_NAME, $env:CHAT_WEB_APP_NAME, $env:ECOMMERCE_API_APP_NAME, $env:ECOMMERCE_WEB_APP_NAME) | ForEach-Object {
  if (-not [string]::IsNullOrWhiteSpace($_)) {
    az webapp restart --resource-group $rg --name $_
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
}
