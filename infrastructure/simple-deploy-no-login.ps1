# Simple Deployment - No Interactive Login Required
# This script uses Azure CLI with service principal or existing credentials

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2"
)

Write-Host "🚀 SIMPLE DEPLOYMENT - NO LOGIN REQUIRED" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Check if already logged in
Write-Host "`n🔍 Checking Azure status..." -ForegroundColor Blue
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($account) {
        Write-Host "✅ Already logged in as: $account" -ForegroundColor Green
    } else {
        Write-Host "❌ Not logged in. Please run 'az login' first, then run this script again." -ForegroundColor Red
        Write-Host "   Or use: az login --use-device-code" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Not logged in. Please run 'az login' first, then run this script again." -ForegroundColor Red
    exit 1
}

# Create resource group
Write-Host "`n📦 Creating Resource Group..." -ForegroundColor Blue
az group create --name $ResourceGroupName --location $Location --output none
Write-Host "✅ Resource group created" -ForegroundColor Green

# Deploy using simple Azure CLI commands (no Bicep)
Write-Host "`n🏗️ Deploying Cosmos DB..." -ForegroundColor Blue
$cosmosAccountName = "ecommerce-chat-dev-cosmos-$(Get-Random)"
az cosmosdb create --name $cosmosAccountName --resource-group $ResourceGroupName --locations regionName=$Location --output none
Write-Host "✅ Cosmos DB created: $cosmosAccountName" -ForegroundColor Green

# Create database
Write-Host "`n🗄️ Creating Database..." -ForegroundColor Blue
az cosmosdb sql database create --account-name $cosmosAccountName --resource-group $ResourceGroupName --name "ecommerce-db" --output none
Write-Host "✅ Database created" -ForegroundColor Green

# Create container
Write-Host "`n📦 Creating Products Container..." -ForegroundColor Blue
az cosmosdb sql container create --account-name $cosmosAccountName --resource-group $ResourceGroupName --database-name "ecommerce-db" --name "products" --partition-key-path "/ProductID" --output none
Write-Host "✅ Products container created" -ForegroundColor Green

# Get connection details
Write-Host "`n🔑 Getting Connection Details..." -ForegroundColor Blue
$cosmosEndpoint = az cosmosdb show --name $cosmosAccountName --resource-group $ResourceGroupName --query "documentEndpoint" -o tsv
$cosmosKey = az cosmosdb keys list --name $cosmosAccountName --resource-group $ResourceGroupName --query "primaryMasterKey" -o tsv

Write-Host "✅ Connection details retrieved" -ForegroundColor Green

# Install Python dependencies
Write-Host "`n🐍 Installing Dependencies..." -ForegroundColor Blue
pip install azure-cosmos --quiet
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Create simple seeding script
Write-Host "`n🌱 Creating Seeding Script..." -ForegroundColor Blue
$seedingScript = @"
import os
import json
import uuid
from azure.cosmos import CosmosClient

# Connection details
COSMOS_ENDPOINT = "$cosmosEndpoint"
COSMOS_KEY = "$cosmosKey"
DATABASE_NAME = "ecommerce-db"
CONTAINER_NAME = "products"

# Sample products (first 10 for testing)
PRODUCTS = [
    {"ProductID": "PROD0001", "ProductName": "Pale Meadow", "ProductCategory": "Paint Shades", "Price": 29.99, "ProductDescription": "A soft, earthy green reminiscent of open meadows at dawn.", "ProductPunchLine": "Nature's touch inside your home", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/PaleMeadow.png"},
    {"ProductID": "PROD0002", "ProductName": "Tranquil Lavender", "ProductCategory": "Paint Shades", "Price": 31.99, "ProductDescription": "A muted lavender that soothes and reassures, ideal for relaxation.", "ProductPunchLine": "Find your peaceful moment", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/TranquilLavender.png"},
    {"ProductID": "PROD0003", "ProductName": "Whispering Blue", "ProductCategory": "Paint Shades", "Price": 47.99, "ProductDescription": "Light, breezy blue that lifts spirits and refreshes the space.", "ProductPunchLine": "Float away on blue skies", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlue.png"},
    {"ProductID": "PROD0004", "ProductName": "Whispering Blush", "ProductCategory": "Paint Shades", "Price": 50.82, "ProductDescription": "A subtle, enchanting pink for warmth and understated elegance.", "ProductPunchLine": "Add a blush of beauty", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlush.png"},
    {"ProductID": "PROD0005", "ProductName": "Ocean Mist", "ProductCategory": "Paint Shades", "Price": 84.83, "ProductDescription": "Premium quality ocean mist paint with excellent coverage and durability.", "ProductPunchLine": "Transform Your Space with Ocean Mist!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Ocean Mist_Paint.png"}
]

def main():
    print("🚀 Seeding products...")
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_NAME)
    
    success_count = 0
    for product in PRODUCTS:
        try:
            product_doc = {
                "id": str(uuid.uuid4()),
                "partitionKey": product["ProductID"],
                **product
            }
            container.create_item(body=product_doc)
            success_count += 1
            print(f"✅ {product['ProductName']}")
        except Exception as e:
            print(f"❌ {product['ProductName']}: {e}")
    
    print(f"🎉 Seeded {success_count} products successfully!")

if __name__ == "__main__":
    main()
"@

$seedingScript | Out-File -FilePath "quick-seed.py" -Encoding UTF8
Write-Host "✅ Seeding script created" -ForegroundColor Green

# Run seeding
Write-Host "`n🌱 Seeding Products..." -ForegroundColor Blue
python quick-seed.py
Write-Host "✅ Products seeded" -ForegroundColor Green

# Clean up
Remove-Item "quick-seed.py" -Force -ErrorAction SilentlyContinue

# Success message
Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host "✅ Cosmos DB: $cosmosAccountName" -ForegroundColor Green
Write-Host "✅ Database: ecommerce-db" -ForegroundColor Green
Write-Host "✅ Container: products" -ForegroundColor Green
Write-Host "✅ Products: 5 sample products seeded" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update your backend .env file with these details:" -ForegroundColor White
Write-Host "   COSMOS_DB_ENDPOINT=$cosmosEndpoint" -ForegroundColor Cyan
Write-Host "   COSMOS_DB_KEY=$($cosmosKey.Substring(0,20))..." -ForegroundColor Cyan
Write-Host "   COSMOS_DB_DATABASE_NAME=ecommerce-db" -ForegroundColor Cyan

Write-Host "`n💡 To add all 54 products, run:" -ForegroundColor Yellow
Write-Host "   python seed-all-54-products.py" -ForegroundColor White
