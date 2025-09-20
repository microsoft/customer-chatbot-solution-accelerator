# Simple Frontend Deployment Script
# This script deploys the React frontend to Azure App Service with minimal complexity

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 SIMPLE FRONTEND DEPLOYMENT" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green

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

# Deploy infrastructure
Write-Host "`n🏗️ Deploying infrastructure..." -ForegroundColor Blue

# Deploy App Service Plan
Write-Host "Deploying App Service Plan..." -ForegroundColor Yellow
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

# Deploy Frontend App Service
Write-Host "Deploying Frontend App Service..." -ForegroundColor Yellow
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "frontend-app-service.bicep" `
    --parameters resourceGroupName=$ResourceGroupName `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --parameters appNamePrefix=$AppNamePrefix `
    --parameters appServicePlanName=$appServicePlanName `
    --parameters backendAppServiceUrl="https://$resourceNamePrefix-backend.azurewebsites.net" `
    --output table

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend App Service deployment failed" -ForegroundColor Red
    exit 1
}

# Build and deploy frontend
Write-Host "`n🔨 Building and deploying frontend..." -ForegroundColor Blue

$frontendPath = Join-Path $PSScriptRoot "..\modern-e-commerce-ch"
if (-not (Test-Path $frontendPath)) {
    Write-Host "❌ Frontend directory not found at: $frontendPath" -ForegroundColor Red
    exit 1
}

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
Push-Location $frontendPath
try {
    npm install --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm install failed" -ForegroundColor Red
        exit 1
    }
    
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm run build failed" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# Create deployment package
$deployPath = Join-Path $PSScriptRoot "frontend-deploy"
if (Test-Path $deployPath) {
    Remove-Item $deployPath -Recurse -Force
}
New-Item -ItemType Directory -Path $deployPath -Force

# Copy built files
Copy-Item "$frontendPath\dist\*" $deployPath -Recurse -Force

# Create minimal package.json
$packageJson = @"
{
  "name": "ecommerce-frontend",
  "version": "1.0.0",
  "scripts": {
    "start": "npx serve -s . -l 80"
  },
  "dependencies": {
    "serve": "^14.2.1"
  }
}
"@
$packageJson | Out-File -FilePath "$deployPath\package.json" -Encoding UTF8 -Force

# Create web.config
$webConfig = @"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="React Routes" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
"@
$webConfig | Out-File -FilePath "$deployPath\web.config" -Encoding UTF8

# Deploy to Azure
Write-Host "Deploying to Azure..." -ForegroundColor Yellow
$zipPath = Join-Path $PSScriptRoot "frontend-deploy.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$deployPath\*" -DestinationPath $zipPath -Force

az webapp deployment source config-zip `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName `
    --src $zipPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend deployment completed!" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend deployment failed" -ForegroundColor Red
    exit 1
}

# Success
$frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ App Service: $frontendAppServiceName" -ForegroundColor Green

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   $frontendUrl" -ForegroundColor White