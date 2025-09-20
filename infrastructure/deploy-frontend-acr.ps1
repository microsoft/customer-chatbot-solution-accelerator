# ACR Frontend Deployment Script
# This script deploys the React frontend using Azure Container Registry - no local builds required!

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 ACR FRONTEND DEPLOYMENT (NO LOCAL BUILD)" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Check Azure login
Write-Host "`n🔍 Checking Azure status..." -ForegroundColor Blue
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($account) {
        Write-Host "✅ Logged in as: $account" -ForegroundColor Green
    } else {
        Write-Host "❌ Not logged in. Please run 'az login' first." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Not logged in. Please run 'az login' first." -ForegroundColor Red
    exit 1
}

# Variables
$resourceNamePrefix = "$AppNamePrefix-$Environment"
$appServicePlanName = "$resourceNamePrefix-plan"
$frontendAppServiceName = "$resourceNamePrefix-frontend"
$acrName = "$resourceNamePrefix" + "acr"
$imageName = "frontend"
$imageTag = "latest"

# Deploy ACR
Write-Host "`n📦 Deploying Azure Container Registry..." -ForegroundColor Blue
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "acr.bicep" `
    --parameters resourceGroupName=$ResourceGroupName `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --parameters appNamePrefix=$AppNamePrefix `
    --output table

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ACR deployment failed" -ForegroundColor Red
    exit 1
}

# Deploy App Service Plan
Write-Host "`n🏗️ Deploying App Service Plan..." -ForegroundColor Blue
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "app-service-plan.bicep" `
    --parameters resourceGroupName=$ResourceGroupName `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --parameters appNamePrefix=$AppNamePrefix `
    --output table

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ App Service Plan deployment failed" -ForegroundColor Red
    exit 1
}

# Build and push container using ACR Tasks (cloud build)
Write-Host "`n🐳 Building and pushing container to ACR..." -ForegroundColor Blue

# Get ACR login server
$acrLoginServer = az acr show --name $acrName --resource-group $ResourceGroupName --query "loginServer" -o tsv

# Enable admin user for ACR
Write-Host "Enabling admin user for ACR..." -ForegroundColor Yellow
az acr update --name $acrName --admin-enabled true

# Copy Dockerfile to frontend directory for build context
Write-Host "Preparing build context..." -ForegroundColor Yellow
Copy-Item "Dockerfile.frontend" "..\modern-e-commerce-ch\Dockerfile" -Force
Copy-Item "nginx.conf" "..\modern-e-commerce-ch\nginx.conf" -Force

# Build and push using ACR Tasks (no local Docker required!)
Write-Host "Building container in ACR..." -ForegroundColor Yellow
az acr build --registry $acrName --image "$imageName`:$imageTag" --file "Dockerfile" "..\modern-e-commerce-ch"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Container build failed" -ForegroundColor Red
    exit 1
}

# Deploy Frontend App Service with Container
Write-Host "`n🌐 Deploying Frontend App Service with Container..." -ForegroundColor Blue
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "frontend-app-service-container.bicep" `
    --parameters resourceGroupName=$ResourceGroupName `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --parameters appNamePrefix=$AppNamePrefix `
    --parameters appServicePlanName=$appServicePlanName `
    --parameters acrName=$acrName `
    --parameters imageName=$imageName `
    --parameters imageTag=$imageTag `
    --parameters backendAppServiceUrl="https://$resourceNamePrefix-backend.azurewebsites.net" `
    --output table

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend App Service deployment failed" -ForegroundColor Red
    exit 1
}

# Success
$frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

Write-Host "`n🎉 ACR DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host "✅ Container Registry: $acrName" -ForegroundColor Green
Write-Host "✅ Container Image: $acrLoginServer/$imageName`:$imageTag" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ App Service: $frontendAppServiceName" -ForegroundColor Green

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   $frontendUrl" -ForegroundColor White

Write-Host "`n📋 What happened:" -ForegroundColor Cyan
Write-Host "• Built React app in Azure Container Registry (no local build)" -ForegroundColor White
Write-Host "• Created container with Nginx to serve static files" -ForegroundColor White
Write-Host "• Deployed container to Azure App Service" -ForegroundColor White
Write-Host "• No local disk space or Docker required!" -ForegroundColor White
