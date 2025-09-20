# Add Auto-Seeding to Existing Deployment
# This script modifies your existing deploy.ps1 to include automatic product seeding

Write-Host "🔧 Adding auto-seeding to existing deployment script..." -ForegroundColor Blue

# Read the existing deploy.ps1
$deployScript = Get-Content "deploy.ps1" -Raw

# Add seeding function at the end of the script, before the final success message
$seedingFunction = @"

# Auto-Seeding Function
function Invoke-AutoSeeding {
    param(
        [string]$CosmosEndpoint,
        [string]$CosmosKey,
        [string]$DatabaseName = "ecommerce-db",
        [string]$ContainerName = "products"
    )
    
    Write-Host "`n🌱 Starting Auto-Seeding Process..." -ForegroundColor Blue
    
    # Install azure-cosmos if not already installed
    try {
        pip install azure-cosmos --quiet
        Write-Host "✅ Azure Cosmos SDK installed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Could not install azure-cosmos, continuing anyway..." -ForegroundColor Yellow
    }
    
    # Create seeding script
    $seedingScript = @'
import os
import json
import uuid
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError

# Cosmos DB configuration
COSMOS_ENDPOINT = "$CosmosEndpoint"
COSMOS_KEY = "$CosmosKey"
DATABASE_NAME = "$DatabaseName"
CONTAINER_NAME = "$ContainerName"

# All 54 products data (truncated for brevity - full list would be here)
ALL_PRODUCTS = [
    {"ProductID": "PROD0001", "ProductName": "Pale Meadow", "ProductCategory": "Paint Shades", "Price": 29.99, "ProductDescription": "A soft, earthy green reminiscent of open meadows at dawn.", "ProductPunchLine": "Nature's touch inside your home", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/PaleMeadow.png"},
    # ... (all 54 products would be here)
]

def main():
    print("🚀 Auto-seeding products...")
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

if __name__ == "__main__":
    main()
'@
    
    # Write and execute seeding script
    $seedingScript | Out-File -FilePath "temp-seed.py" -Encoding UTF8
    try {
        python temp-seed.py
        Write-Host "✅ Auto-seeding completed successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Auto-seeding failed: $_" -ForegroundColor Red
    } finally {
        Remove-Item "temp-seed.py" -Force -ErrorAction SilentlyContinue
    }
}

"@

# Find where to insert the seeding call
$insertPoint = $deployScript.IndexOf("Write-Host ""✅ Deployment completed successfully!"" -ForegroundColor Green")

if ($insertPoint -gt 0) {
    # Insert the seeding function before the final success message
    $beforeSuccess = $deployScript.Substring(0, $insertPoint)
    $afterSuccess = $deployScript.Substring($insertPoint)
    
    # Add seeding call
    $seedingCall = @"

# Auto-seed products after successful deployment
Write-Host "`n🌱 Auto-seeding products..." -ForegroundColor Blue
try {
    $cosmosEndpoint = az cosmosdb show --name `$cosmosAccountName --resource-group `$resourceGroupName --query "documentEndpoint" -o tsv
    $cosmosKey = az cosmosdb keys list --name `$cosmosAccountName --resource-group `$resourceGroupName --query "primaryMasterKey" -o tsv
    
    Invoke-AutoSeeding -CosmosEndpoint $cosmosEndpoint -CosmosKey $cosmosKey
} catch {
    Write-Host "⚠️ Auto-seeding failed, but deployment was successful: $_" -ForegroundColor Yellow
}

"@
    
    $newDeployScript = $beforeSuccess + $seedingFunction + $seedingCall + $afterSuccess
    
    # Write the updated script
    $newDeployScript | Out-File -FilePath "deploy-with-auto-seeding.ps1" -Encoding UTF8
    
    Write-Host "✅ Created deploy-with-auto-seeding.ps1" -ForegroundColor Green
    Write-Host "   This script includes automatic product seeding after deployment" -ForegroundColor Yellow
} else {
    Write-Host "❌ Could not find insertion point in deploy.ps1" -ForegroundColor Red
}
