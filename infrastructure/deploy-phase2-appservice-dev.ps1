# Phase 2: Frontend Deployment (App Service with Dev Server)
# This approach runs your app exactly like npm run dev but in Azure

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 2: APP SERVICE DEV SERVER DEPLOYMENT" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

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

# Variables
$resourceNamePrefix = "$AppNamePrefix-$Environment"
$appServicePlanName = "$resourceNamePrefix-plan"
$frontendAppServiceName = "$resourceNamePrefix-frontend"

Write-Host "`n📋 Deployment Configuration:" -ForegroundColor Blue
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "App Service Plan: $appServicePlanName" -ForegroundColor White
Write-Host "Frontend App Service: $frontendAppServiceName" -ForegroundColor White

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

Write-Host "✅ App Service Plan deployment completed" -ForegroundColor Green

# Create App Service for Frontend (Node.js runtime)
Write-Host "`n🌐 Creating Frontend App Service..." -ForegroundColor Blue

az webapp create `
    --resource-group $ResourceGroupName `
    --plan $appServicePlanName `
    --name $frontendAppServiceName `
    --runtime "NODE:18-lts"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend App Service creation failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Frontend App Service created" -ForegroundColor Green

# Configure App Service settings
Write-Host "`n⚙️ Configuring App Service settings..." -ForegroundColor Blue

# Set Node.js version and startup command
az webapp config appsettings set `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName `
    --settings WEBSITE_NODE_DEFAULT_VERSION=18.19.0 `
    --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true `
    --settings ENABLE_ORYX_BUILD=true `
    --settings WEBSITE_RUN_FROM_PACKAGE=1

# Set startup command to run dev server on port 80
az webapp config set `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName `
    --startup-file "npm run dev -- --host 0.0.0.0 --port 80"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ App Service configuration failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ App Service configured" -ForegroundColor Green

# Create deployment package
Write-Host "`n📦 Creating deployment package..." -ForegroundColor Blue

$frontendPath = Join-Path $PSScriptRoot "..\modern-e-commerce-ch"
$deployPath = Join-Path $PSScriptRoot "frontend-deploy"

if (Test-Path $deployPath) {
    Remove-Item $deployPath -Recurse -Force
}
New-Item -ItemType Directory -Path $deployPath -Force

# Copy ALL source files (not just built files)
Write-Host "Copying source files..." -ForegroundColor Yellow
Copy-Item "$frontendPath\*" $deployPath -Recurse -Force -Exclude @("node_modules", "dist", ".git")

# Modify package.json to work in production
$packageJsonPath = Join-Path $deployPath "package.json"
$packageJson = Get-Content $packageJsonPath | ConvertFrom-Json

# Update dev script to work on port 80 and all hosts
$packageJson.scripts.dev = "vite --host 0.0.0.0 --port 80"
# Add start script if it doesn't exist
$packageJson.scripts | Add-Member -Name "start" -Value "vite --host 0.0.0.0 --port 80" -MemberType NoteProperty -Force

$packageJson | ConvertTo-Json -Depth 10 | Set-Content $packageJsonPath

Write-Host "✅ Deployment package created" -ForegroundColor Green

# Create zip and deploy
$zipPath = Join-Path $PSScriptRoot "frontend-deploy.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$deployPath\*" -DestinationPath $zipPath -Force

Write-Host "`n🚀 Deploying to Azure App Service..." -ForegroundColor Blue
az webapp deployment source config-zip `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName `
    --src $zipPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Deployment completed" -ForegroundColor Green

# Get the URL
$frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

# Wait for startup
Write-Host "`n⏳ Waiting for app to start (this may take a few minutes)..." -ForegroundColor Blue
Start-Sleep -Seconds 60

# Success message
Write-Host "`n🎉 PHASE 2 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Frontend App Service: $frontendAppServiceName" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ Runtime: Node.js 18 LTS" -ForegroundColor Green
Write-Host "✅ Server: Vite Dev Server" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test your frontend at: $frontendUrl" -ForegroundColor White
Write-Host "2. Run Phase 3: Backend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase3-backend.ps1" -ForegroundColor Cyan

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   URL: $frontendUrl" -ForegroundColor White
Write-Host "   Note: This runs your exact npm run dev setup" -ForegroundColor Cyan

Write-Host "`n✨ Why This Works:" -ForegroundColor Green
Write-Host "• Uses the exact same command that works locally" -ForegroundColor White
Write-Host "• Vite handles all the React/TypeScript compilation" -ForegroundColor White
Write-Host "• Hot reload disabled for production stability" -ForegroundColor White
Write-Host "• All your dependencies installed automatically" -ForegroundColor White

Write-Host "`n✨ Ready for Phase 3!" -ForegroundColor Green
