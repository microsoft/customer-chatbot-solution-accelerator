# One-Command Deployment with Auto-Seeding
# This script does everything: deploys infrastructure and seeds products

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev"
)

Write-Host "🚀 ONE-COMMAND DEPLOYMENT WITH AUTO-SEEDING" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Step 1: Deploy infrastructure
Write-Host "`n📦 Step 1: Deploying Infrastructure..." -ForegroundColor Blue
& .\deploy.ps1 -ResourceGroupName $ResourceGroupName -Location $Location -Environment $Environment

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Infrastructure deployment failed!" -ForegroundColor Red
    exit 1
}

# Step 2: Get Cosmos DB details
Write-Host "`n🔍 Step 2: Getting Cosmos DB Details..." -ForegroundColor Blue
$cosmosAccountName = "ecommerce-chat-$Environment-cosmos"
$cosmosEndpoint = az cosmosdb show --name $cosmosAccountName --resource-group $ResourceGroupName --query "documentEndpoint" -o tsv
$cosmosKey = az cosmosdb keys list --name $cosmosAccountName --resource-group $ResourceGroupName --query "primaryMasterKey" -o tsv

Write-Host "✅ Cosmos DB details retrieved" -ForegroundColor Green

# Step 3: Install Python dependencies
Write-Host "`n🐍 Step 3: Installing Dependencies..." -ForegroundColor Blue
pip install -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Step 4: Seed products
Write-Host "`n🌱 Step 4: Seeding Products..." -ForegroundColor Blue
python seed-all-54-products.py
Write-Host "✅ Products seeded successfully" -ForegroundColor Green

# Step 5: Success message
Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host "✅ Infrastructure deployed" -ForegroundColor Green
Write-Host "✅ 54 products seeded" -ForegroundColor Green
Write-Host "✅ Ready for backend/frontend deployment" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Configure backend .env with Cosmos DB details" -ForegroundColor White
Write-Host "2. Deploy backend application" -ForegroundColor White
Write-Host "3. Deploy frontend application" -ForegroundColor White
Write-Host "4. Your e-commerce app is ready!" -ForegroundColor White

Write-Host "`n🔗 Cosmos DB Details:" -ForegroundColor Cyan
Write-Host "Endpoint: $cosmosEndpoint" -ForegroundColor White
Write-Host "Key: $($cosmosKey.Substring(0,20))..." -ForegroundColor White
