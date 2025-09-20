# Phase 2: Frontend Deployment (Static Web Apps - The Right Way)
# This deploys your React app exactly as it should be - as static files

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 2: STATIC WEB APPS DEPLOYMENT (THE RIGHT WAY)" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

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
    Write-Host "Your built files should be here. This is what you get from 'npm run build'" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found built files in dist folder" -ForegroundColor Green

# Variables
$resourceNamePrefix = "$AppNamePrefix$Environment"
$staticWebAppName = "$resourceNamePrefix-static"

Write-Host "`n📋 Deployment Configuration:" -ForegroundColor Blue
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "Static Web App: $staticWebAppName" -ForegroundColor White

# Create Static Web App
Write-Host "`n🌐 Creating Static Web App..." -ForegroundColor Blue
az staticwebapp create `
    --name $staticWebAppName `
    --resource-group $ResourceGroupName `
    --location $Location `
    --sku Free

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Static Web App creation failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Static Web App created successfully" -ForegroundColor Green

# Get deployment token
Write-Host "`n🔑 Getting deployment token..." -ForegroundColor Blue
$deploymentToken = az staticwebapp secrets list --name $staticWebAppName --resource-group $ResourceGroupName --query "properties.apiKey" -o tsv

if (-not $deploymentToken) {
    Write-Host "❌ Failed to get deployment token" -ForegroundColor Red
    exit 1
}

# Install SWA CLI if not present
Write-Host "`n📦 Checking Static Web Apps CLI..." -ForegroundColor Blue
try {
    $swaVersion = npx @azure/static-web-apps-cli --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Static Web Apps CLI available" -ForegroundColor Green
    }
} catch {
    Write-Host "Installing Static Web Apps CLI..." -ForegroundColor Yellow
    npm install -g @azure/static-web-apps-cli
}

# Deploy the files using SWA CLI
Write-Host "`n📦 Deploying your built React files..." -ForegroundColor Blue
npx @azure/static-web-apps-cli deploy $distPath --deployment-token $deploymentToken --verbose

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Static files deployment failed" -ForegroundColor Red
    exit 1
}

# Get the URL
$staticWebAppUrl = az staticwebapp show --name $staticWebAppName --resource-group $ResourceGroupName --query "defaultHostname" -o tsv
$frontendUrl = "https://$staticWebAppUrl"

Write-Host "`n🎉 PHASE 2 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Static Web App: $staticWebAppName" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test your frontend at: $frontendUrl" -ForegroundColor White
Write-Host "2. Run Phase 3: Backend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase3-backend.ps1" -ForegroundColor Cyan

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   URL: $frontendUrl" -ForegroundColor White

Write-Host "`n✨ Why This is Better:" -ForegroundColor Green
Write-Host "• No server.js needed - just like your local setup!" -ForegroundColor White
Write-Host "• Uses your exact built files from dist/" -ForegroundColor White
Write-Host "• React Router works automatically" -ForegroundColor White
Write-Host "• Global CDN for fast loading" -ForegroundColor White
Write-Host "• FREE hosting" -ForegroundColor White
Write-Host "• No containers, no complexity" -ForegroundColor White

Write-Host "`n🎯 This matches your local workflow:" -ForegroundColor Cyan
Write-Host "• Local: npm run dev (development)" -ForegroundColor White
Write-Host "• Build: npm run build (creates dist/)" -ForegroundColor White
Write-Host "• Deploy: Static Web Apps serves dist/ files" -ForegroundColor White

Write-Host "`n✨ Ready for Phase 3!" -ForegroundColor Green
