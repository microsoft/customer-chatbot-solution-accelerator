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
Write-Host "To deploy a different scenario, set AZURE_ENV_SCENARIO to one of: ecommerce, healthcare, banking before your first 'azd up' on this environment (default is ecommerce)."
