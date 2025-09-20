# Phase 2: Frontend Deployment (Simplified)
# This script deploys the React frontend using existing built files - no local builds required!

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 2: FRONTEND DEPLOYMENT (SIMPLIFIED)" -ForegroundColor Green
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

# Check if dist folder exists (built files)
$frontendPath = Join-Path $PSScriptRoot "..\modern-e-commerce-ch"
$distPath = Join-Path $frontendPath "dist"
if (-not (Test-Path $distPath)) {
    Write-Host "❌ Dist folder not found at: $distPath" -ForegroundColor Red
    Write-Host "Please run 'npm run build' in the frontend directory first." -ForegroundColor Yellow
    Write-Host "Or use the existing built files if available." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found built files in dist folder" -ForegroundColor Green

# Variables
$resourceNamePrefix = "$AppNamePrefix-$Environment"
$appServicePlanName = "$resourceNamePrefix-plan"
$frontendAppServiceName = "$resourceNamePrefix-frontend"

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

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ App Service Plan deployment completed" -ForegroundColor Green
} else {
    Write-Host "❌ App Service Plan deployment failed" -ForegroundColor Red
    exit 1
}

# Deploy Frontend App Service
Write-Host "`n🌐 Deploying Frontend App Service..." -ForegroundColor Blue
Write-Host "Frontend App Service Name: $frontendAppServiceName" -ForegroundColor Cyan

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

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend App Service deployment completed" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend App Service deployment failed" -ForegroundColor Red
    exit 1
}

# Deploy existing built files (no local build required!)
Write-Host "`n🚀 Deploying Built Frontend Files..." -ForegroundColor Blue

# Create deployment package with existing built files
$deployPath = Join-Path $PSScriptRoot "frontend-deploy"
if (Test-Path $deployPath) {
    Remove-Item $deployPath -Recurse -Force
}
New-Item -ItemType Directory -Path $deployPath -Force

# Copy built files from dist folder
Write-Host "Copying built files from dist folder..." -ForegroundColor Yellow
Copy-Item "$distPath\*" $deployPath -Recurse -Force

# Create package.json for serving static files
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

# Create web.config for Azure App Service
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
    <staticContent>
      <mimeMap fileExtension=".json" mimeType="application/json" />
    </staticContent>
  </system.webServer>
</configuration>
"@
$webConfig | Out-File -FilePath "$deployPath\web.config" -Encoding UTF8

Write-Host "Created deployment package with existing built files" -ForegroundColor Green

# Deploy using zip deployment
$zipPath = Join-Path $PSScriptRoot "frontend-deploy.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$deployPath\*" -DestinationPath $zipPath -Force

# Deploy to Azure
Write-Host "`n🚀 Deploying to Azure App Service..." -ForegroundColor Blue
az webapp deployment source config-zip `
    --resource-group $ResourceGroupName `
    --name $frontendAppServiceName `
    --src $zipPath
    
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend deployment completed" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend deployment failed" -ForegroundColor Red
    exit 1
}

# Get frontend URL
$frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

# Success message
Write-Host "`n🎉 PHASE 2 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Frontend App Service: $frontendAppServiceName" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ App Service Plan: $appServicePlanName" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run Phase 3: Backend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase3-backend.ps1" -ForegroundColor Cyan

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   URL: $frontendUrl" -ForegroundColor White
Write-Host "   Note: Backend not deployed yet, so API calls will fail" -ForegroundColor Yellow

Write-Host "`n✨ Ready for Phase 3!" -ForegroundColor Green
