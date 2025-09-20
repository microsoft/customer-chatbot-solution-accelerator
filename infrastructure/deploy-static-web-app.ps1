# Static Web App Deployment Script
# This is the SIMPLEST way to deploy a React frontend - no Docker, no App Service complexity!

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 STATIC WEB APP DEPLOYMENT (SIMPLEST)" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

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

# Check if dist folder exists
$distPath = "..\modern-e-commerce-ch\dist"
if (-not (Test-Path $distPath)) {
    Write-Host "❌ Dist folder not found at: $distPath" -ForegroundColor Red
    Write-Host "Please run 'npm run build' in the frontend directory first." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found built files in dist folder" -ForegroundColor Green

# Variables
$resourceNamePrefix = "$AppNamePrefix$Environment"
$staticWebAppName = "$resourceNamePrefix-static"

Write-Host "`n📋 Deployment Configuration:" -ForegroundColor Blue
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "Static Web App: $staticWebAppName" -ForegroundColor White
Write-Host "Source: $distPath" -ForegroundColor White

# Deploy Static Web App
Write-Host "`n🌐 Deploying Static Web App..." -ForegroundColor Blue
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "static-web-app.bicep" `
    --parameters resourceGroupName=$ResourceGroupName `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --parameters appNamePrefix=$AppNamePrefix `
    --output table

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Static Web App deployment failed" -ForegroundColor Red
    exit 1
}

# Get deployment token
Write-Host "`n🔑 Getting deployment token..." -ForegroundColor Blue
$deploymentToken = az staticwebapp secrets list --name $staticWebAppName --resource-group $ResourceGroupName --query "properties.apiKey" -o tsv

if (-not $deploymentToken) {
    Write-Host "❌ Failed to get deployment token" -ForegroundColor Red
    exit 1
}

# Deploy files using Azure CLI
Write-Host "`n📦 Deploying static files..." -ForegroundColor Blue
az staticwebapp deploy --name $staticWebAppName --resource-group $ResourceGroupName --source $distPath --token $deploymentToken

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Static files deployment failed" -ForegroundColor Red
    exit 1
}

# Get the URL
$staticWebAppUrl = az staticwebapp show --name $staticWebAppName --resource-group $ResourceGroupName --query "defaultHostname" -o tsv
$fullUrl = "https://$staticWebAppUrl"

# Success
Write-Host "`n🎉 STATIC WEB APP DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host "✅ Static Web App: $staticWebAppName" -ForegroundColor Green
Write-Host "✅ URL: $fullUrl" -ForegroundColor Green

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   $fullUrl" -ForegroundColor White

Write-Host "`n📋 What happened:" -ForegroundColor Cyan
Write-Host "• Created Azure Static Web App (FREE tier)" -ForegroundColor White
Write-Host "• Deployed your built React files from dist/ folder" -ForegroundColor White
Write-Host "• No Docker, no App Service, no complexity!" -ForegroundColor White
Write-Host "• Perfect for React applications" -ForegroundColor White

Write-Host "`n✨ Benefits of Static Web Apps:" -ForegroundColor Yellow
Write-Host "• FREE hosting tier" -ForegroundColor White
Write-Host "• Global CDN" -ForegroundColor White
Write-Host "• Built-in CI/CD" -ForegroundColor White
Write-Host "• Perfect for React/Vue/Angular" -ForegroundColor White
Write-Host "• No server management" -ForegroundColor White