# Simple Azure Deployment Script for Windows
# This script deploys resources one by one to avoid complex Bicep issues

param(
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "West US 2",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$AppNamePrefix = "ecommerce-chat"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Simple Azure Deployment..." -ForegroundColor Green
Write-Host "Subscription ID: $SubscriptionId" -ForegroundColor Yellow
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Yellow
Write-Host "Location: $Location" -ForegroundColor Yellow

# Set subscription
Write-Host "📋 Setting subscription..." -ForegroundColor Blue
az account set --subscription $SubscriptionId

# Create resource group
Write-Host "📦 Creating resource group..." -ForegroundColor Blue
az group create --name $ResourceGroupName --location $Location

# Create App Service Plan
Write-Host "🏗️ Creating App Service Plan..." -ForegroundColor Blue
$appServicePlanName = "$AppNamePrefix-$Environment-plan"
az appservice plan create --name $appServicePlanName --resource-group $ResourceGroupName --location $Location --sku B1 --is-linux

# Create Backend App Service
Write-Host "🔧 Creating Backend App Service..." -ForegroundColor Blue
$backendAppName = "$AppNamePrefix-$Environment-backend"
az webapp create --name $backendAppName --resource-group $ResourceGroupName --plan $appServicePlanName --runtime "PYTHON|3.11"

# Create Frontend App Service
Write-Host "🔧 Creating Frontend App Service..." -ForegroundColor Blue
$frontendAppName = "$AppNamePrefix-$Environment-frontend"
az webapp create --name $frontendAppName --resource-group $ResourceGroupName --plan $appServicePlanName --runtime "NODE|18-lts"

# Create Cosmos DB Account
Write-Host "🗄️ Creating Cosmos DB Account..." -ForegroundColor Blue
$cosmosDbName = "$AppNamePrefix-$Environment-cosmos"
az cosmosdb create --name $cosmosDbName --resource-group $ResourceGroupName --locations regionName=$Location

# Create Cosmos DB Database
Write-Host "🗄️ Creating Cosmos DB Database..." -ForegroundColor Blue
az cosmosdb sql database create --account-name $cosmosDbName --resource-group $ResourceGroupName --name "ecommerce-db"

# Create Cosmos DB Containers
Write-Host "📦 Creating Cosmos DB Containers..." -ForegroundColor Blue
az cosmosdb sql container create --account-name $cosmosDbName --resource-group $ResourceGroupName --database-name "ecommerce-db" --name "products" --partition-key-path "/id"
az cosmosdb sql container create --account-name $cosmosDbName --resource-group $ResourceGroupName --database-name "ecommerce-db" --name "users" --partition-key-path "/id"
az cosmosdb sql container create --account-name $cosmosDbName --resource-group $ResourceGroupName --database-name "ecommerce-db" --name "chat_sessions" --partition-key-path "/id"
az cosmosdb sql container create --account-name $cosmosDbName --resource-group $ResourceGroupName --database-name "ecommerce-db" --name "transactions" --partition-key-path "/id"

# Create Key Vault
Write-Host "🔑 Creating Key Vault..." -ForegroundColor Blue
$keyVaultName = "$AppNamePrefix-$Environment-kv"
az keyvault create --name $keyVaultName --resource-group $ResourceGroupName --location $Location

# Get Cosmos DB connection string
Write-Host "🔗 Getting Cosmos DB connection string..." -ForegroundColor Blue
$cosmosConnectionString = az cosmosdb keys list --name $cosmosDbName --resource-group $ResourceGroupName --type connection-strings --query "connectionStrings[0].connectionString" --output tsv

# Store Cosmos DB connection string in Key Vault
Write-Host "💾 Storing secrets in Key Vault..." -ForegroundColor Blue
az keyvault secret set --vault-name $keyVaultName --name "cosmos-db-connection-string" --value $cosmosConnectionString

# Display results
Write-Host "`n🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "`n📊 Resources Created:" -ForegroundColor Cyan
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "App Service Plan: $appServicePlanName" -ForegroundColor White
Write-Host "Backend App: $backendAppName" -ForegroundColor White
Write-Host "Frontend App: $frontendAppName" -ForegroundColor White
Write-Host "Cosmos DB: $cosmosDbName" -ForegroundColor White
Write-Host "Key Vault: $keyVaultName" -ForegroundColor White

Write-Host "`n🔗 URLs:" -ForegroundColor Cyan
Write-Host "Backend: https://$backendAppName.azurewebsites.net" -ForegroundColor Blue
Write-Host "Frontend: https://$frontendAppName.azurewebsites.net" -ForegroundColor Blue

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Deploy your application code to the App Services" -ForegroundColor White
Write-Host "2. Configure Azure OpenAI and add secrets to Key Vault" -ForegroundColor White
Write-Host "3. Test the application endpoints" -ForegroundColor White

Write-Host "`n✨ Happy coding!" -ForegroundColor Green
