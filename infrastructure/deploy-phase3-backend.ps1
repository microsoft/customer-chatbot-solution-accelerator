# Phase 3: Backend Deployment
# This script deploys the FastAPI backend to Azure App Service

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 3: BACKEND DEPLOYMENT" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

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
    Write-Host "❌ Resource group does not exist. Please run Phase 1 first." -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ Resource group exists" -ForegroundColor Green
}

# Get Cosmos DB details
Write-Host "`n🔍 Getting Cosmos DB details..." -ForegroundColor Blue
$cosmosAccounts = az cosmosdb list --resource-group $ResourceGroupName --query "[].name" -o tsv
if (-not $cosmosAccounts) {
    Write-Host "⚠️  No Cosmos DB accounts found. Backend will use mock data." -ForegroundColor Yellow
    $cosmosDbName = "mock"
    $cosmosEndpoint = "mock"
    $cosmosKey = "mock"
} else {
    $cosmosDbName = $cosmosAccounts[0]
    $cosmosEndpoint = az cosmosdb show --name $cosmosDbName --resource-group $ResourceGroupName --query "documentEndpoint" -o tsv
    $cosmosKey = az cosmosdb keys list --name $cosmosDbName --resource-group $ResourceGroupName --query "primaryMasterKey" -o tsv
    Write-Host "✅ Found Cosmos DB: $cosmosDbName" -ForegroundColor Green
}

# Get the most recent frontend deployment name
Write-Host "`n🔍 Finding frontend deployment..." -ForegroundColor Blue
$frontendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'frontend') || contains(name, 'ecommerce-frontend')].name" -o tsv
if (-not $frontendApps) {
    Write-Host "❌ No frontend deployment found. Please deploy frontend first." -ForegroundColor Red
    exit 1
}

# Use the most recent frontend app (last in the list)
$frontendAppServiceName = ($frontendApps -split "`n")[-1]
Write-Host "✅ Found frontend: $frontendAppServiceName" -ForegroundColor Green

# Variables  
$timestamp = Get-Date -Format "yyyyMMddHHmm"
$backendAppServiceName = "ecommerce-backend-$timestamp"
$appServicePlanName = "frontend-plan"  # Use the same plan as frontend

# Deploy Backend App Service
Write-Host "`n🐍 Deploying Backend App Service..." -ForegroundColor Blue
Write-Host "Backend App Service Name: $backendAppServiceName" -ForegroundColor Cyan

# Create the backend app service directly (simplified approach)
Write-Host "Creating backend app service..." -ForegroundColor Gray
az webapp create `
    --name $backendAppServiceName `
    --resource-group $ResourceGroupName `
    --plan $appServicePlanName `
    --runtime "PYTHON:3.11" `
    --only-show-errors

# Configure app settings and startup command
Write-Host "Configuring app settings..." -ForegroundColor Gray
$frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

az webapp config appsettings set `
    --name $backendAppServiceName `
    --resource-group $ResourceGroupName `
    --settings `
    COSMOS_DB_ENDPOINT=$cosmosEndpoint `
    COSMOS_DB_KEY=$cosmosKey `
    COSMOS_DB_DATABASE_NAME="ecommerce_db" `
    ALLOWED_ORIGINS="$frontendUrl,http://localhost:5173" `
    WEBSITES_PORT="8000" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="1" `
    ENABLE_ORYX_BUILD="true" `
    AZURE_OPENAI_ENDPOINT="https://testmodle.openai.azure.com/" `
    AZURE_OPENAI_API_KEY="your_openai_api_key_here" `
    AZURE_OPENAI_API_VERSION="2025-01-01-preview" `
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" `
    --only-show-errors

# Set the startup command
Write-Host "Setting startup command..." -ForegroundColor Gray
az webapp config set `
    --name $backendAppServiceName `
    --resource-group $ResourceGroupName `
    --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" `
    --only-show-errors

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend App Service deployment completed" -ForegroundColor Green
} else {
    Write-Host "❌ Backend App Service deployment failed" -ForegroundColor Red
    exit 1
}

# Build and deploy backend code
Write-Host "`n🔨 Building Backend Application..." -ForegroundColor Blue

# Navigate to backend directory
$backendPath = Join-Path $PSScriptRoot "..\backend"
if (-not (Test-Path $backendPath)) {
    Write-Host "❌ Backend directory not found at: $backendPath" -ForegroundColor Red
    exit 1
}

Push-Location $backendPath

try {
    # Verify requirements.txt exists
    if (-not (Test-Path "requirements.txt")) {
        Write-Host "❌ requirements.txt not found in backend directory" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Found requirements.txt" -ForegroundColor Green
    
    # Create startup command file for Azure App Service
    $startupCommand = @"
#!/bin/bash
cd /home/site/wwwroot
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
"@
    $startupCommand | Out-File -FilePath "startup.sh" -Encoding UTF8
    
    # Create deployment package
    $deployPath = Join-Path $PSScriptRoot "backend-deploy"
    if (Test-Path $deployPath) {
        Remove-Item $deployPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $deployPath -Force
    
    # Copy backend files
    Copy-Item "app" $deployPath -Recurse -Force
    Copy-Item "requirements.txt" $deployPath -Force
    Copy-Item "startup.sh" $deployPath -Force
    
    # Create .deployment file
    $deploymentConfig = @"
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT = 1
ENABLE_ORYX_BUILD = true
"@
    $deploymentConfig | Out-File -FilePath "$deployPath\.deployment" -Encoding UTF8
    
    # Deploy using zip deployment
    $zipPath = Join-Path $PSScriptRoot "backend-deploy.zip"
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    Compress-Archive -Path "$deployPath\*" -DestinationPath $zipPath -Force
    
    # Deploy to Azure
    Write-Host "Deploying backend to Azure App Service..." -ForegroundColor Yellow
    az webapp deployment source config-zip `
        --resource-group $ResourceGroupName `
        --name $backendAppServiceName `
        --src $zipPath
        
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Backend deployment completed" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend deployment failed" -ForegroundColor Red
        exit 1
    }
    
} finally {
    Pop-Location
}

# Get URLs
$backendUrl = "https://$backendAppServiceName.azurewebsites.net"
$frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

# Test backend health
Write-Host "`n🔍 Testing Backend Health..." -ForegroundColor Blue
Start-Sleep -Seconds 30  # Wait for deployment to complete

try {
    $healthResponse = Invoke-RestMethod -Uri "$backendUrl/health" -Method GET -TimeoutSec 30
    Write-Host "✅ Backend health check passed" -ForegroundColor Green
    Write-Host "   Status: $($healthResponse.status)" -ForegroundColor Cyan
    Write-Host "   Database: $($healthResponse.database)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️  Backend health check failed or still starting up" -ForegroundColor Yellow
    Write-Host "   This is normal for new deployments. Please wait a few minutes and test manually." -ForegroundColor Yellow
}

# Success message
Write-Host "`n🎉 PHASE 3 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Backend App Service: $backendAppServiceName" -ForegroundColor Green
Write-Host "✅ Backend URL: $backendUrl" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run Phase 4: Integration Test" -ForegroundColor White
Write-Host "   .\deploy-phase4-integration.ps1" -ForegroundColor Cyan

Write-Host "`n🔧 Test your backend:" -ForegroundColor Yellow
Write-Host "   Health Check: $backendUrl/health" -ForegroundColor White
Write-Host "   API Docs: $backendUrl/docs" -ForegroundColor White

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   URL: $frontendUrl" -ForegroundColor White
Write-Host "   Note: Should now be able to communicate with backend" -ForegroundColor Cyan

Write-Host "`n✨ Ready for Phase 4!" -ForegroundColor Green
