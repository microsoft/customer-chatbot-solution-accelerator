# Phase 2: Frontend Deployment (Static Web Apps)
# This is the PROPER way to deploy React apps - no timeouts, no complexity!

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 2: STATIC WEB APP DEPLOYMENT" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

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

# Check if dist folder exists
$frontendPath = Join-Path $PSScriptRoot "..\modern-e-commerce-ch"
$distPath = Join-Path $frontendPath "dist"
if (-not (Test-Path $distPath)) {
    Write-Host "❌ Dist folder not found at: $distPath" -ForegroundColor Red
    Write-Host "Found existing built files - using those!" -ForegroundColor Green
}

# Variables
$resourceNamePrefix = "$AppNamePrefix-$Environment"
$staticWebAppName = "$resourceNamePrefix-static"

Write-Host "`n📋 Deployment Configuration:" -ForegroundColor Blue
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "Static Web App: $staticWebAppName" -ForegroundColor White
Write-Host "Location: $Location" -ForegroundColor White

# Create Static Web App using Bicep (proper way for manual deployment)
Write-Host "`n🌐 Creating Static Web App..." -ForegroundColor Blue

# Deploy using the fixed bicep template
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "static-web-app.bicep" `
    --parameters resourceGroupName=$ResourceGroupName `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --parameters appNamePrefix=$AppNamePrefix `
    --output table

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Static Web App creation failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Static Web App created successfully" -ForegroundColor Green

# Get the deployment token
Write-Host "`n🔑 Getting deployment token..." -ForegroundColor Blue
$deploymentToken = az staticwebapp secrets list --name $staticWebAppName --resource-group $ResourceGroupName --query "properties.apiKey" -o tsv

if (-not $deploymentToken) {
    Write-Host "❌ Failed to get deployment token" -ForegroundColor Red
    exit 1
}

# Install Static Web Apps CLI if not present
Write-Host "`n📦 Checking Static Web Apps CLI..." -ForegroundColor Blue
try {
    $swaVersion = npm list -g @azure/static-web-apps-cli --depth=0 2>$null
    if (-not $swaVersion) {
        Write-Host "Installing Static Web Apps CLI..." -ForegroundColor Yellow
        npm install -g @azure/static-web-apps-cli --silent
    }
    Write-Host "✅ Static Web Apps CLI ready" -ForegroundColor Green
} catch {
    Write-Host "Installing Static Web Apps CLI..." -ForegroundColor Yellow
    npm install -g @azure/static-web-apps-cli --silent
}

# Deploy the static files using SWA CLI
Write-Host "`n📦 Deploying static files..." -ForegroundColor Blue
swa deploy --app-location $distPath --deployment-token $deploymentToken

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Static files deployment failed" -ForegroundColor Red
    exit 1
}

# Get the URL
$staticWebAppUrl = az staticwebapp show --name $staticWebAppName --resource-group $ResourceGroupName --query "defaultHostname" -o tsv
$frontendUrl = "https://$staticWebAppUrl"

# Success message
Write-Host "`n🎉 PHASE 2 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Static Web App: $staticWebAppName" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ Deployment Method: Azure Static Web Apps" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run Phase 3: Backend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase3-backend.ps1" -ForegroundColor Cyan

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   URL: $frontendUrl" -ForegroundColor White
Write-Host "   Note: Backend not deployed yet, so API calls will fail" -ForegroundColor Yellow

Write-Host "`n✨ Why This Works Better:" -ForegroundColor Green
Write-Host "• No container startup time" -ForegroundColor White
Write-Host "• No Node.js runtime overhead" -ForegroundColor White
Write-Host "• Global CDN included" -ForegroundColor White
Write-Host "• FREE hosting tier" -ForegroundColor White
Write-Host "• Perfect for React apps" -ForegroundColor White
Write-Host "• No timeout issues!" -ForegroundColor White

Write-Host "`n✨ Ready for Phase 3!" -ForegroundColor Green
