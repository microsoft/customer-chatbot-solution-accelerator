# Deploy Cosmos DB with Seeded Data
# This script creates a new Cosmos DB account in the ecommerce-chat-rg resource group
# with the correct schema and pre-seeded data for products and transactions

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat",
    [switch]$SkipSeeding = $false
)

Write-Host "🚀 Deploying Cosmos DB with Seeded Data..." -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan

# Check if resource group exists
Write-Host "`n📋 Checking resource group..." -ForegroundColor Yellow
$rgExists = az group exists --name $ResourceGroupName 2>$null
if ($rgExists -eq "false") {
    Write-Host "❌ Resource group '$ResourceGroupName' not found!" -ForegroundColor Red
    Write-Host "Please create the resource group first or check the name." -ForegroundColor Yellow
    Write-Host "You can create it with: az group create --name $ResourceGroupName --location '$Location'" -ForegroundColor Cyan
    exit 1
}
Write-Host "✅ Resource group found" -ForegroundColor Green

# Generate unique names
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$cosmosDbName = "$AppNamePrefix-$Environment-cosmos-$timestamp"
$databaseName = "ecommerce_db"
$keyVaultName = "$AppNamePrefix-$Environment-kv"

Write-Host "`n🏗️  Deploying Cosmos DB infrastructure..." -ForegroundColor Yellow

# Deploy the Cosmos DB resources
$deploymentName = "cosmos-deployment-$timestamp"
$templateFile = Join-Path $PSScriptRoot "simple-cosmos.bicep"
$parametersFile = Join-Path $PSScriptRoot "cosmos-parameters.json"

# Create parameters file for this deployment in proper Azure format
$cosmosParams = @{
    '$schema' = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#'
    contentVersion = '1.0.0.0'
    parameters = @{
        resourceGroupName = @{ value = $ResourceGroupName }
        location = @{ value = $Location }
        environment = @{ value = $Environment }
        appNamePrefix = @{ value = $AppNamePrefix }
        cosmosDbName = @{ value = $cosmosDbName }
        databaseName = @{ value = $databaseName }
    }
} | ConvertTo-Json -Depth 4

$cosmosParams | Out-File -FilePath $parametersFile -Encoding UTF8

try {
    Write-Host "Deploying Cosmos DB account: $cosmosDbName" -ForegroundColor Yellow
    
    # Deploy using Azure CLI
    Write-Host "Running deployment command..." -ForegroundColor Yellow
    $deploymentOutput = az deployment group create `
        --resource-group $ResourceGroupName `
        --template-file $templateFile `
        --parameters @$parametersFile `
        --name $deploymentName `
        --output json 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Azure CLI deployment failed!" -ForegroundColor Red
        Write-Host "Error output: $deploymentOutput" -ForegroundColor Red
        exit 1
    }
    
    $deploymentResult = $deploymentOutput | ConvertFrom-Json
    $provisioningState = $deploymentResult.properties.provisioningState

    if ($provisioningState -eq "Succeeded") {
        Write-Host "✅ Cosmos DB deployment successful!" -ForegroundColor Green
        
        # Get the connection details using Azure CLI
        $cosmosEndpoint = az cosmosdb show --name $cosmosDbName --resource-group $ResourceGroupName --query "documentEndpoint" -o tsv 2>$null
        $cosmosKey = az cosmosdb keys list --name $cosmosDbName --resource-group $ResourceGroupName --query "primaryMasterKey" -o tsv 2>$null
        
        Write-Host "`n📊 Cosmos DB Details:" -ForegroundColor Cyan
        Write-Host "Account Name: $cosmosDbName" -ForegroundColor White
        Write-Host "Endpoint: $cosmosEndpoint" -ForegroundColor White
        Write-Host "Database: $databaseName" -ForegroundColor White
        
        # Save connection string to file
        $connectionString = "AccountEndpoint=$cosmosEndpoint;AccountKey=$cosmosKey;"
        $connectionString | Out-File -FilePath (Join-Path $PSScriptRoot "cosmos-connection-string.txt") -Encoding UTF8
        Write-Host "Connection string saved to cosmos-connection-string.txt" -ForegroundColor Green
        
        if (-not $SkipSeeding) {
            Write-Host "`n🌱 Seeding data..." -ForegroundColor Yellow
            
            # Set environment variables for seeding
            $env:COSMOS_DB_ENDPOINT = $cosmosEndpoint
            $env:COSMOS_DB_KEY = $cosmosKey
            $env:COSMOS_DB_DATABASE_NAME = $databaseName
            
            # Run the seeding script
            $seedScript = Join-Path $PSScriptRoot "seed-cosmos-data.py"
            if (Test-Path $seedScript) {
                Write-Host "Running data seeding script..." -ForegroundColor Yellow
                python $seedScript
                Write-Host "✅ Data seeding completed!" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Seeding script not found. Please run seeding manually." -ForegroundColor Yellow
            }
        }
        
        Write-Host "`n🎉 Deployment completed successfully!" -ForegroundColor Green
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "1. Update your backend .env file with the new connection details" -ForegroundColor White
        Write-Host "2. Test the connection with your backend application" -ForegroundColor White
        Write-Host "3. Verify the seeded data in the Azure Portal" -ForegroundColor White
        
    } else {
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
        Write-Host "Provisioning State: $provisioningState" -ForegroundColor Red
        Write-Host "Full deployment output: $deploymentOutput" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "❌ Deployment error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Clean up temporary files
    if (Test-Path $parametersFile) {
        Remove-Item $parametersFile -Force
    }
}

Write-Host "`n✨ Script completed!" -ForegroundColor Green
