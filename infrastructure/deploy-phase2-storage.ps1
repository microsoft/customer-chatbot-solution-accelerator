# Phase 2: Frontend Deployment (Azure Storage Static Website)
# This is the SIMPLEST way to deploy React apps - no containers, no runtimes, just static files!

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 2: STORAGE STATIC WEBSITE DEPLOYMENT" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

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
    Write-Host "Please ensure built files exist in the dist folder." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found built files in dist folder" -ForegroundColor Green

# Variables
$resourceNamePrefix = "$AppNamePrefix$Environment"
# Storage account names must be 3-24 chars, lowercase letters and numbers only
$tempName = ($AppNamePrefix + $Environment + "st").ToLower().Replace("-", "")
$storageAccountName = if ($tempName.Length -gt 24) { $tempName.Substring(0, 24) } else { $tempName }

Write-Host "`n📋 Deployment Configuration:" -ForegroundColor Blue
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "Storage Account: $storageAccountName" -ForegroundColor White
Write-Host "Location: $Location" -ForegroundColor White

# Deploy Storage Account
Write-Host "`n📦 Creating Storage Account..." -ForegroundColor Blue
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file "storage-static-website.bicep" `
    --parameters resourceGroupName=$ResourceGroupName `
    --parameters location=$Location `
    --parameters environment=$Environment `
    --parameters appNamePrefix=$AppNamePrefix `
    --output table

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Storage Account creation failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Storage Account created successfully" -ForegroundColor Green

# Get the actual storage account name from the deployment
$actualStorageAccountName = az deployment group show --resource-group $ResourceGroupName --name "storage-static-website" --query "properties.outputs.storageAccountName.value" -o tsv

Write-Host "Using storage account: $actualStorageAccountName" -ForegroundColor Cyan

# Enable static website hosting
Write-Host "`n🌐 Enabling static website hosting..." -ForegroundColor Blue
az storage blob service-properties update `
    --account-name $actualStorageAccountName `
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
Write-Host "`n📤 Uploading files to storage..." -ForegroundColor Blue
az storage blob upload-batch `
    --account-name $actualStorageAccountName `
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
$frontendUrl = "https://$actualStorageAccountName.z22.web.core.windows.net"

# Success message
Write-Host "`n🎉 PHASE 2 COMPLETE!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "✅ Storage Account: $actualStorageAccountName" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ Deployment Method: Azure Storage Static Website" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run Phase 3: Backend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase3-backend.ps1" -ForegroundColor Cyan

Write-Host "`n🌐 Test your frontend:" -ForegroundColor Yellow
Write-Host "   URL: $frontendUrl" -ForegroundColor White
Write-Host "   Note: Backend not deployed yet, so API calls will fail" -ForegroundColor Yellow

Write-Host "`n✨ Why This Works Better:" -ForegroundColor Green
Write-Host "• No containers or runtimes needed" -ForegroundColor White
Write-Host "• Instant deployment" -ForegroundColor White
Write-Host "• Super cheap (pennies per month)" -ForegroundColor White
Write-Host "• Perfect for static React apps" -ForegroundColor White
Write-Host "• No timeout issues ever!" -ForegroundColor White
Write-Host "• Global CDN available" -ForegroundColor White

Write-Host "`n✨ Ready for Phase 3!" -ForegroundColor Green
