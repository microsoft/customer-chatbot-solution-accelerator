# Phase 2: Frontend Deployment (Simple Fix)
# This approach uses a minimal Node.js server to serve your built React files

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 2: SIMPLE FRONTEND DEPLOYMENT (FIXED)" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

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

# Variables
$resourceNamePrefix = "$AppNamePrefix-$Environment"
$appServicePlanName = "$resourceNamePrefix-plan"
$frontendAppServiceName = "$resourceNamePrefix-frontend"

# Check if dist folder exists
$frontendPath = Join-Path $PSScriptRoot "..\modern-e-commerce-ch"
$distPath = Join-Path $frontendPath "dist"
if (-not (Test-Path $distPath)) {
    Write-Host "❌ Dist folder not found at: $distPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found built files in dist folder" -ForegroundColor Green

# Create a simple deployment package
Write-Host "`n📦 Creating simple deployment package..." -ForegroundColor Blue

$deployPath = Join-Path $PSScriptRoot "frontend-deploy"
if (Test-Path $deployPath) {
    Remove-Item $deployPath -Recurse -Force
}
New-Item -ItemType Directory -Path $deployPath -Force

# Copy built files
Copy-Item "$distPath\*" $deployPath -Recurse -Force

# Create a simple package.json for serving static files
$packageJson = @"
{
  "name": "ecommerce-frontend",
  "version": "1.0.0",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  },
  "engines": {
    "node": "18.x"
  }
}
"@
$packageJson | Out-File -FilePath "$deployPath\package.json" -Encoding UTF8 -Force

# Create a simple Express server to serve static files
$serverJs = @'
const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 80;

// Serve static files from current directory
app.use(express.static(__dirname));

// Handle React Router (send all routes to index.html)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log('Server running on port ' + port);
});
'@
$serverJs | Out-File -FilePath "$deployPath\server.js" -Encoding UTF8 -Force

Write-Host "✅ Deployment package created" -ForegroundColor Green

# Create zip and deploy
$zipPath = Join-Path $PSScriptRoot "frontend-deploy.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$deployPath\*" -DestinationPath $zipPath -Force

Write-Host "`n🚀 Deploying to Azure App Service..." -ForegroundColor Blue
az webapp deploy `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName `
    --src-path $zipPath `
    --type zip

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green

# Configure startup command and settings
Write-Host "`n⚙️ Configuring startup command..." -ForegroundColor Blue
az webapp config set `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName `
    --startup-file "npm start"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set startup command" -ForegroundColor Red
    exit 1
}

# Set app settings
Write-Host "Setting app settings..." -ForegroundColor Yellow
az webapp config appsettings set `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName `
    --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true `
    --settings WEBSITES_PORT=80 `
    --settings WEBSITE_NODE_DEFAULT_VERSION=18.19.0

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set app settings" -ForegroundColor Red
    exit 1
}

# Restart the app to apply new settings
Write-Host "Restarting app service..." -ForegroundColor Yellow
az webapp restart `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to restart app service" -ForegroundColor Red
    exit 1
}

# Get the URL and test
$frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

Write-Host "`n⏳ Waiting for app to start..." -ForegroundColor Blue
Start-Sleep -Seconds 60

# Test if the app is responding
Write-Host "Testing app response..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 30 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ App is responding successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ App returned status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ App may still be starting up. Please check manually: $frontendUrl" -ForegroundColor Yellow
}

Write-Host "`n🎉 PHASE 2 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Frontend App Service: $frontendAppServiceName" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ Server: Express.js serving static files" -ForegroundColor Green

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   URL: $frontendUrl" -ForegroundColor White

Write-Host "`n✨ How this works:" -ForegroundColor Green
Write-Host "• Uses your existing built files from dist/" -ForegroundColor White
Write-Host "• Simple Express.js server serves static files" -ForegroundColor White
Write-Host "• Handles React Router correctly" -ForegroundColor White
Write-Host "• No complex build process in Azure" -ForegroundColor White
Write-Host "• Reliable and fast startup" -ForegroundColor White

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test your frontend at: $frontendUrl" -ForegroundColor White
Write-Host "2. Run Phase 3: Backend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase3-backend.ps1" -ForegroundColor Cyan

Write-Host "`n✨ Ready for Phase 3!" -ForegroundColor Green
