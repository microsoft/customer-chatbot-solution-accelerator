# Phase 1: Cosmos DB Deployment
# This script deploys only the Cosmos DB infrastructure

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 1: COSMOS DB DEPLOYMENT" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if already logged in
Write-Host "`n🔍 Checking Azure status..." -ForegroundColor Blue
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($account) {
        Write-Host "✅ Already logged in as: $account" -ForegroundColor Green
    } else {
        Write-Host "❌ Not logged in. Please run 'az login' first." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Not logged in. Please run 'az login' first." -ForegroundColor Red
    exit 1
}

# Check if resource group exists
Write-Host "`n📦 Checking Resource Group..." -ForegroundColor Blue
$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "false") {
    Write-Host "Creating resource group..." -ForegroundColor Yellow
    az group create --name $ResourceGroupName --location $Location --output none
    Write-Host "✅ Resource group created" -ForegroundColor Green
} else {
    Write-Host "✅ Resource group exists" -ForegroundColor Green
}

# Generate unique Cosmos DB name
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$cosmosDbName = "$AppNamePrefix-$Environment-cosmos-$timestamp"

Write-Host "`n🏗️ Deploying Cosmos DB with Bicep..." -ForegroundColor Blue
Write-Host "Cosmos DB Name: $cosmosDbName" -ForegroundColor Cyan

# Deploy Cosmos DB using Bicep
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "cosmos-db.bicep" `
    --parameters cosmosDbName=$cosmosDbName `
    --parameters resourceGroupName=$ResourceGroupName `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --output table

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Cosmos DB deployment completed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Cosmos DB deployment failed" -ForegroundColor Red
    exit 1
}

# Get connection details
Write-Host "`n🔑 Getting Connection Details..." -ForegroundColor Blue
$cosmosEndpoint = az cosmosdb show --name $cosmosDbName --resource-group $ResourceGroupName --query "documentEndpoint" -o tsv
$cosmosKey = az cosmosdb keys list --name $cosmosDbName --resource-group $ResourceGroupName --query "primaryMasterKey" -o tsv

Write-Host "✅ Connection details retrieved" -ForegroundColor Green

# Save connection details
$connectionString = "AccountEndpoint=$cosmosEndpoint;AccountKey=$cosmosKey;"
$connectionString | Out-File -FilePath "cosmos-connection-string.txt" -Encoding UTF8
Write-Host "✅ Connection string saved to cosmos-connection-string.txt" -ForegroundColor Green

# Install Python dependencies for seeding
Write-Host "`n🐍 Installing Dependencies..." -ForegroundColor Blue
pip install azure-cosmos --quiet
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Set environment variables for seeding
$env:COSMOS_DB_ENDPOINT = $cosmosEndpoint
$env:COSMOS_DB_KEY = $cosmosKey
$env:COSMOS_DB_DATABASE_NAME = "ecommerce_db"

# Run the comprehensive seeding script
Write-Host "`n🌱 Seeding Data..." -ForegroundColor Blue
$seedScript = Join-Path $PSScriptRoot "seed-cosmos-data.py"
if (Test-Path $seedScript) {
    python $seedScript
    Write-Host "✅ Data seeding completed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Seeding script not found. Please run seeding manually." -ForegroundColor Yellow
}

# Success message
Write-Host "`n🎉 PHASE 1 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Cosmos DB: $cosmosDbName" -ForegroundColor Green
Write-Host "✅ Database: ecommerce_db" -ForegroundColor Green
Write-Host "✅ Containers: products, users, chat_sessions, carts, transactions" -ForegroundColor Green
Write-Host "✅ Data: Products and sample transactions seeded" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run Phase 2: Frontend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase2-frontend.ps1" -ForegroundColor Cyan

Write-Host "`n🔧 Test your Cosmos DB:" -ForegroundColor Yellow
Write-Host "   Connection String: $($cosmosKey.Substring(0,20))..." -ForegroundColor White

Write-Host "`n✨ Ready for Phase 2!" -ForegroundColor Green
