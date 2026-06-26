$ErrorActionPreference = 'Stop'

$scenario = $env:AZURE_ENV_SCENARIO
if ([string]::IsNullOrWhiteSpace($scenario)) {
    $scenario = 'ecommerce'
}
$scenario = $scenario.Trim().ToLower()

$valid = @('ecommerce', 'healthcare', 'banking')
if ($valid -notcontains $scenario) {
    throw "Invalid AZURE_ENV_SCENARIO '$scenario'. Use: ecommerce, healthcare, or banking."
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..' '..')).Path
$manifestPath = Join-Path $repoRoot 'scenarios' $scenario 'manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Scenario pack not found: $manifestPath"
}

Write-Host "Deployment scenario: $scenario"
Write-Host "Set AZURE_ENV_SCENARIO before the first azd up on a new environment (default is ecommerce)."
