# Quick Deploy Cosmos DB Script
# Simple script to deploy Cosmos DB with seeded data

Write-Host "🚀 Quick Deploy: Cosmos DB with Seeded Data" -ForegroundColor Green
Write-Host "This will create a new Cosmos DB account in the ecommerce-chat-rg resource group" -ForegroundColor Yellow

# Check if user is logged in to Azure
try {
    $account = az account show --query "user.name" -o tsv 2>$null
    if (-not $account) {
        Write-Host "❌ Not logged in to Azure. Please run 'az login' first." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Logged in as: $account" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not available. Please install Azure CLI and run 'az login'" -ForegroundColor Red
    exit 1
}

# Run the main deployment script
$deployScript = Join-Path $PSScriptRoot "deploy-cosmos-with-data.ps1"
if (Test-Path $deployScript) {
    Write-Host "`n🏗️  Starting deployment..." -ForegroundColor Yellow
    & $deployScript
} else {
    Write-Host "❌ Deployment script not found: $deployScript" -ForegroundColor Red
    exit 1
}

Write-Host "`n✨ Quick deploy completed!" -ForegroundColor Green
