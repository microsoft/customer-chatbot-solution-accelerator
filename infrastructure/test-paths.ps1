# Test script to verify paths are correct before deployment

Write-Host "🔍 Testing deployment paths..." -ForegroundColor Blue

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $projectRoot "modern-e-commerce-ch"

Write-Host "Script directory: $scriptDir" -ForegroundColor Gray
Write-Host "Project root: $projectRoot" -ForegroundColor Gray
Write-Host "Frontend directory: $frontendDir" -ForegroundColor Gray

# Test paths
if (Test-Path $frontendDir) {
    Write-Host "✅ Frontend directory found" -ForegroundColor Green
    
    $packageJsonPath = Join-Path $frontendDir "package.json"
    if (Test-Path $packageJsonPath) {
        Write-Host "✅ package.json found" -ForegroundColor Green
    } else {
        Write-Host "❌ package.json not found" -ForegroundColor Red
    }
    
    $srcPath = Join-Path $frontendDir "src"
    if (Test-Path $srcPath) {
        Write-Host "✅ src directory found" -ForegroundColor Green
    } else {
        Write-Host "❌ src directory not found" -ForegroundColor Red
    }
    
} else {
    Write-Host "❌ Frontend directory not found: $frontendDir" -ForegroundColor Red
    Write-Host "Current directory contents:" -ForegroundColor Yellow
    Get-ChildItem $projectRoot | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor Gray }
}

# Test Azure CLI
Write-Host "`n🔍 Testing Azure CLI..." -ForegroundColor Blue
$azCheck = az --version 2>$null
if ($azCheck) {
    Write-Host "✅ Azure CLI found" -ForegroundColor Green
    
    $account = az account show 2>$null | ConvertFrom-Json
    if ($account) {
        Write-Host "✅ Logged into Azure as: $($account.user.name)" -ForegroundColor Green
    } else {
        Write-Host "❌ Not logged into Azure. Run 'az login' first." -ForegroundColor Red
    }
} else {
    Write-Host "❌ Azure CLI not found" -ForegroundColor Red
}

Write-Host "`n✅ Path test complete!" -ForegroundColor Green

