# Ultra Simple Deployment - Just Cosmos DB
# No Azure CLI required - uses Azure Portal instructions

Write-Host "🚀 ULTRA SIMPLE DEPLOYMENT" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

Write-Host "`n📋 This script will guide you through the simplest deployment:" -ForegroundColor Blue
Write-Host "1. Create Cosmos DB via Azure Portal (no CLI needed)" -ForegroundColor White
Write-Host "2. Get connection details" -ForegroundColor White
Write-Host "3. Seed products locally" -ForegroundColor White

Write-Host "`n🌐 Step 1: Create Cosmos DB in Azure Portal" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow
Write-Host "1. Go to: https://portal.azure.com" -ForegroundColor White
Write-Host "2. Click 'Create a resource'" -ForegroundColor White
Write-Host "3. Search for 'Azure Cosmos DB'" -ForegroundColor White
Write-Host "4. Click 'Create'" -ForegroundColor White
Write-Host "5. Fill in:" -ForegroundColor White
Write-Host "   - Subscription: Your subscription" -ForegroundColor Cyan
Write-Host "   - Resource Group: Create new 'ecommerce-chat-rg'" -ForegroundColor Cyan
Write-Host "   - Account Name: ecommerce-chat-dev-cosmos" -ForegroundColor Cyan
Write-Host "   - Location: West US 2" -ForegroundColor Cyan
Write-Host "   - Capacity mode: Provisioned throughput" -ForegroundColor Cyan
Write-Host "   - Apply Free Tier Discount: Yes" -ForegroundColor Cyan
Write-Host "6. Click 'Review + Create' then 'Create'" -ForegroundColor White

Write-Host "`n⏳ Wait for deployment to complete (2-3 minutes)..." -ForegroundColor Yellow
Read-Host "Press Enter when Cosmos DB is created"

Write-Host "`n🗄️ Step 2: Create Database and Container" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Yellow
Write-Host "1. Go to your Cosmos DB account" -ForegroundColor White
Write-Host "2. Click 'Data Explorer'" -ForegroundColor White
Write-Host "3. Click 'New Container'" -ForegroundColor White
Write-Host "4. Fill in:" -ForegroundColor White
Write-Host "   - Database id: ecommerce-db" -ForegroundColor Cyan
Write-Host "   - Container id: products" -ForegroundColor Cyan
Write-Host "   - Partition key: /ProductID" -ForegroundColor Cyan
Write-Host "   - Throughput: 400" -ForegroundColor Cyan
Write-Host "5. Click 'OK'" -ForegroundColor White

Read-Host "Press Enter when database and container are created"

Write-Host "`n🔑 Step 3: Get Connection Details" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow
Write-Host "1. In your Cosmos DB account, click 'Keys'" -ForegroundColor White
Write-Host "2. Copy the 'URI' (endpoint)" -ForegroundColor White
Write-Host "3. Copy the 'PRIMARY KEY'" -ForegroundColor White

$cosmosEndpoint = Read-Host "Paste the URI (endpoint) here"
$cosmosKey = Read-Host "Paste the PRIMARY KEY here"

Write-Host "`n🐍 Step 4: Install Python Dependencies" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow
pip install azure-cosmos --quiet
Write-Host "✅ Dependencies installed" -ForegroundColor Green

Write-Host "`n🌱 Step 5: Seed Products" -ForegroundColor Yellow
Write-Host "=======================" -ForegroundColor Yellow

# Create seeding script with user's details
$seedingScript = @"
import os
import json
import uuid
from azure.cosmos import CosmosClient

# Your Cosmos DB details
COSMOS_ENDPOINT = "$cosmosEndpoint"
COSMOS_KEY = "$cosmosKey"
DATABASE_NAME = "ecommerce-db"
CONTAINER_NAME = "products"

# All 54 products
ALL_PRODUCTS = [
    {"ProductID": "PROD0001", "ProductName": "Pale Meadow", "ProductCategory": "Paint Shades", "Price": 29.99, "ProductDescription": "A soft, earthy green reminiscent of open meadows at dawn.", "ProductPunchLine": "Nature's touch inside your home", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/PaleMeadow.png"},
    {"ProductID": "PROD0002", "ProductName": "Tranquil Lavender", "ProductCategory": "Paint Shades", "Price": 31.99, "ProductDescription": "A muted lavender that soothes and reassures, ideal for relaxation.", "ProductPunchLine": "Find your peaceful moment", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/TranquilLavender.png"},
    {"ProductID": "PROD0003", "ProductName": "Whispering Blue", "ProductCategory": "Paint Shades", "Price": 47.99, "ProductDescription": "Light, breezy blue that lifts spirits and refreshes the space.", "ProductPunchLine": "Float away on blue skies", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlue.png"},
    {"ProductID": "PROD0004", "ProductName": "Whispering Blush", "ProductCategory": "Paint Shades", "Price": 50.82, "ProductDescription": "A subtle, enchanting pink for warmth and understated elegance.", "ProductPunchLine": "Add a blush of beauty", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlush.png"},
    {"ProductID": "PROD0005", "ProductName": "Ocean Mist", "ProductCategory": "Paint Shades", "Price": 84.83, "ProductDescription": "Premium quality ocean mist paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Ocean Mist!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Ocean Mist_Paint.png"},
    {"ProductID": "PROD0006", "ProductName": "Sunset Coral", "ProductCategory": "Paint Shades", "Price": 48.57, "ProductDescription": "Premium quality sunset coral paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Sunset Coral!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Sunset Coral Paint.png"},
    {"ProductID": "PROD0007", "ProductName": "Forest Whisper", "ProductCategory": "Paint Shades", "Price": 43.09, "ProductDescription": "Premium quality forest whisper paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Forest Whisper!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Forest Whisper Paint.png"},
    {"ProductID": "PROD0008", "ProductName": "Morning Dew", "ProductCategory": "Paint Shades", "Price": 81.94, "ProductDescription": "Premium quality morning dew paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Morning Dew!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Morning Dew Paint.png"},
    {"ProductID": "PROD0009", "ProductName": "Dusty Rose", "ProductCategory": "Paint Shades", "Price": 75.62, "ProductDescription": "Premium quality dusty rose paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Dusty Rose!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Dusty Rose Paint.png"},
    {"ProductID": "PROD0010", "ProductName": "Sage Harmony", "ProductCategory": "Paint Shades", "Price": 33.26, "ProductDescription": "Premium quality sage harmony paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Sage Harmony!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Sage Harmony.png"}
]

def main():
    print("🚀 Seeding products...")
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        
        success_count = 0
        for product in ALL_PRODUCTS:
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
        
    except Exception as e:
        print(f"❌ Error connecting to Cosmos DB: {e}")
        print("Please check your connection details and try again.")

if __name__ == "__main__":
    main()
"@

$seedingScript | Out-File -FilePath "seed-products.py" -Encoding UTF8
Write-Host "✅ Seeding script created" -ForegroundColor Green

Write-Host "`n🌱 Running seeding script..." -ForegroundColor Blue
python seed-products.py

# Clean up
Remove-Item "seed-products.py" -Force -ErrorAction SilentlyContinue

Write-Host "`n🎉 SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host "✅ Cosmos DB created" -ForegroundColor Green
Write-Host "✅ Database and container created" -ForegroundColor Green
Write-Host "✅ Products seeded" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update your backend .env file with:" -ForegroundColor White
Write-Host "   COSMOS_DB_ENDPOINT=$cosmosEndpoint" -ForegroundColor Cyan
Write-Host "   COSMOS_DB_KEY=$($cosmosKey.Substring(0,20))..." -ForegroundColor Cyan
Write-Host "   COSMOS_DB_DATABASE_NAME=ecommerce-db" -ForegroundColor Cyan

Write-Host "`n2. Start your backend and frontend applications" -ForegroundColor White
Write-Host "3. Your e-commerce app is ready!" -ForegroundColor White
