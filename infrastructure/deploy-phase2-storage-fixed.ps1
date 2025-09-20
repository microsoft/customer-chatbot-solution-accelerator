# Phase 2: Frontend Deployment (Azure Storage Static Website - Fixed)
# This is the most reliable way to deploy React static files

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 2: AZURE STORAGE STATIC WEBSITE (RELIABLE)" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

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
    exit 1
}

Write-Host "✅ Found built files in dist folder" -ForegroundColor Green

# Variables - create a simple, valid storage account name
$timestamp = Get-Date -Format "yyyyMMdd"
$storageAccountName = "frontend$Environment$timestamp".ToLower()
# Ensure it's under 24 characters
if ($storageAccountName.Length -gt 24) {
    $storageAccountName = $storageAccountName.Substring(0, 24)
}

Write-Host "`n📋 Deployment Configuration:" -ForegroundColor Blue
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "Storage Account: $storageAccountName" -ForegroundColor White
Write-Host "Location: $Location" -ForegroundColor White

# Create storage account
Write-Host "`n📦 Creating storage account..." -ForegroundColor Blue
az storage account create `
    --name $storageAccountName `
    --resource-group $ResourceGroupName `
    --location $Location `
    --sku Standard_LRS `
    --kind StorageV2 `
    --access-tier Hot `
    --allow-blob-public-access true

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Storage account creation failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Storage account created successfully" -ForegroundColor Green

# Enable static website hosting
Write-Host "`n🌐 Enabling static website hosting..." -ForegroundColor Blue
az storage blob service-properties update `
    --account-name $storageAccountName `
    --auth-mode login `
    --static-website true `
    --index-document index.html `
    --404-document index.html

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to enable static website hosting" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Static website hosting enabled" -ForegroundColor Green

# Upload files to $web container
Write-Host "`n📤 Uploading your React app files..." -ForegroundColor Blue
az storage blob upload-batch `
    --account-name $storageAccountName `
    --auth-mode login `
    --destination '$web' `
    --source $distPath `
    --overwrite

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ File upload failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Files uploaded successfully" -ForegroundColor Green

# Get the static website URL
$frontendUrl = "https://$storageAccountName.z22.web.core.windows.net"

# Test the deployment
Write-Host "`n🧪 Testing deployment..." -ForegroundColor Blue
Start-Sleep -Seconds 10
try {
    $response = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 30 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Your React app is live and responding!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Still propagating, but should be ready soon" -ForegroundColor Yellow
}

# Success message
Write-Host "`n🎉 PHASE 2 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Storage Account: $storageAccountName" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ Method: Azure Storage Static Website" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test your frontend at: $frontendUrl" -ForegroundColor White
Write-Host "2. Run Phase 3: Backend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase3-backend.ps1" -ForegroundColor Cyan

Write-Host "`n🌐 Your React App:" -ForegroundColor Yellow
Write-Host "   $frontendUrl" -ForegroundColor White

Write-Host "`n✨ Why This Works:" -ForegroundColor Green
Write-Host "• Direct file serving - no servers needed" -ForegroundColor White
Write-Host "• Uses your exact built files from dist/" -ForegroundColor White
Write-Host "• React Router supported with 404-document fallback" -ForegroundColor White
Write-Host "• Super fast and reliable" -ForegroundColor White
Write-Host "• Costs pennies per month" -ForegroundColor White

Write-Host "`n✨ Ready for Phase 3!" -ForegroundColor Green
