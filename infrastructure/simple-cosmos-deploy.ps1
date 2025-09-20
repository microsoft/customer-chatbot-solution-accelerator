# Simple Cosmos DB Deployment - Based on Working Script
# This uses direct Azure CLI commands instead of Bicep

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2"
)

Write-Host "🚀 SIMPLE COSMOS DB DEPLOYMENT" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

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
$cosmosAccountName = "ecommerce-chat-dev-cosmos-$timestamp"

# Deploy Cosmos DB
Write-Host "`n🏗️ Deploying Cosmos DB..." -ForegroundColor Blue
az cosmosdb create --name $cosmosAccountName --resource-group $ResourceGroupName --locations regionName=$Location --output none
Write-Host "✅ Cosmos DB created: $cosmosAccountName" -ForegroundColor Green

# Create database
Write-Host "`n🗄️ Creating Database..." -ForegroundColor Blue
az cosmosdb sql database create --account-name $cosmosAccountName --resource-group $ResourceGroupName --name "ecommerce_db" --output none
Write-Host "✅ Database created" -ForegroundColor Green

# Create containers with correct partition keys
Write-Host "`n📦 Creating Containers..." -ForegroundColor Blue

# Products container
az cosmosdb sql container create --account-name $cosmosAccountName --resource-group $ResourceGroupName --database-name "ecommerce_db" --name "products" --partition-key-path "/category" --output none
Write-Host "✅ Products container created" -ForegroundColor Green

# Users container
az cosmosdb sql container create --account-name $cosmosAccountName --resource-group $ResourceGroupName --database-name "ecommerce_db" --name "users" --partition-key-path "/email" --output none
Write-Host "✅ Users container created" -ForegroundColor Green

# Chat sessions container
az cosmosdb sql container create --account-name $cosmosAccountName --resource-group $ResourceGroupName --database-name "ecommerce_db" --name "chat_sessions" --partition-key-path "/user_id" --output none
Write-Host "✅ Chat sessions container created" -ForegroundColor Green

# Carts container
az cosmosdb sql container create --account-name $cosmosAccountName --resource-group $ResourceGroupName --database-name "ecommerce_db" --name "carts" --partition-key-path "/user_id" --output none
Write-Host "✅ Carts container created" -ForegroundColor Green

# Transactions container
az cosmosdb sql container create --account-name $cosmosAccountName --resource-group $ResourceGroupName --database-name "ecommerce_db" --name "transactions" --partition-key-path "/user_id" --output none
Write-Host "✅ Transactions container created" -ForegroundColor Green

# Get connection details
Write-Host "`n🔑 Getting Connection Details..." -ForegroundColor Blue
$cosmosEndpoint = az cosmosdb show --name $cosmosAccountName --resource-group $ResourceGroupName --query "documentEndpoint" -o tsv
$cosmosKey = az cosmosdb keys list --name $cosmosAccountName --resource-group $ResourceGroupName --query "primaryMasterKey" -o tsv

Write-Host "✅ Connection details retrieved" -ForegroundColor Green

# Save connection details
$connectionString = "AccountEndpoint=$cosmosEndpoint;AccountKey=$cosmosKey;"
$connectionString | Out-File -FilePath "cosmos-connection-string.txt" -Encoding UTF8
Write-Host "✅ Connection string saved to cosmos-connection-string.txt" -ForegroundColor Green

# Install Python dependencies
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
Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host "✅ Cosmos DB: $cosmosAccountName" -ForegroundColor Green
Write-Host "✅ Database: ecommerce_db" -ForegroundColor Green
Write-Host "✅ Containers: products, users, chat_sessions, carts, transactions" -ForegroundColor Green
Write-Host "✅ Data: Products and sample transactions seeded" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update your backend .env file with these details:" -ForegroundColor White
Write-Host "   COSMOS_DB_ENDPOINT=$cosmosEndpoint" -ForegroundColor Cyan
Write-Host "   COSMOS_DB_KEY=$($cosmosKey.Substring(0,20))..." -ForegroundColor Cyan
Write-Host "   COSMOS_DB_DATABASE_NAME=ecommerce_db" -ForegroundColor Cyan

Write-Host "`n🔧 Test your backend:" -ForegroundColor Yellow
Write-Host "   cd ..\backend" -ForegroundColor White
Write-Host "   python app/main.py" -ForegroundColor White

Write-Host "`n✨ Ready to go!" -ForegroundColor Green
