# Complete Deployment Script with Entra ID Authentication
# This script deploys the entire e-commerce chat application with Microsoft Entra ID authentication

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat",
    [string]$AzureTenantId,
    [string]$AzureClientId,
    [string]$AzureClientSecret,
    [string]$CosmosDbEndpoint,
    [string]$CosmosDbKey,
    [string]$OpenAiEndpoint,
    [string]$OpenAiApiKey,
    [string]$OpenAiDeploymentName = "gpt-4o-mini",
    [switch]$SkipCosmos = $false,
    [switch]$SkipFrontend = $false,
    [switch]$SkipBackend = $false,
    [switch]$SkipIntegration = $false
)

Write-Host "🚀 COMPLETE E-COMMERCE CHAT DEPLOYMENT WITH AUTH" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "App Name Prefix: $AppNamePrefix" -ForegroundColor Cyan

# Validate required parameters
if (-not $AzureTenantId) {
    Write-Host "❌ AzureTenantId is required. Please provide your Azure tenant ID." -ForegroundColor Red
    Write-Host "You can find this in Azure Portal > Azure Active Directory > Overview" -ForegroundColor Yellow
    exit 1
}

if (-not $AzureClientId) {
    Write-Host "❌ AzureClientId is required. Please provide your Azure App Registration client ID." -ForegroundColor Red
    Write-Host "You can find this in Azure Portal > Azure Active Directory > App registrations" -ForegroundColor Yellow
    exit 1
}

if (-not $AzureClientSecret) {
    Write-Host "❌ AzureClientSecret is required. Please provide your Azure App Registration client secret." -ForegroundColor Red
    Write-Host "You can find this in Azure Portal > Azure Active Directory > App registrations > Certificates & secrets" -ForegroundColor Yellow
    exit 1
}

if (-not $CosmosDbEndpoint) {
    Write-Host "❌ CosmosDbEndpoint is required. Please provide your Cosmos DB endpoint." -ForegroundColor Red
    Write-Host "You can find this in Azure Portal > Cosmos DB > Keys" -ForegroundColor Yellow
    exit 1
}

if (-not $CosmosDbKey) {
    Write-Host "❌ CosmosDbKey is required. Please provide your Cosmos DB primary key." -ForegroundColor Red
    Write-Host "You can find this in Azure Portal > Cosmos DB > Keys" -ForegroundColor Yellow
    exit 1
}

if (-not $OpenAiEndpoint) {
    Write-Host "❌ OpenAiEndpoint is required. Please provide your Azure OpenAI endpoint." -ForegroundColor Red
    Write-Host "You can find this in Azure Portal > Azure OpenAI > Keys and Endpoint" -ForegroundColor Yellow
    exit 1
}

if (-not $OpenAiApiKey) {
    Write-Host "❌ OpenAiApiKey is required. Please provide your Azure OpenAI API key." -ForegroundColor Red
    Write-Host "You can find this in Azure Portal > Azure OpenAI > Keys and Endpoint" -ForegroundColor Yellow
    exit 1
}

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

# Set environment variables for deployment
$env:AZURE_TENANT_ID = $AzureTenantId
$env:AZURE_CLIENT_ID = $AzureClientId
$env:AZURE_CLIENT_SECRET = $AzureClientSecret
$env:COSMOS_DB_ENDPOINT = $CosmosDbEndpoint
$env:COSMOS_DB_KEY = $CosmosDbKey
$env:AZURE_OPENAI_ENDPOINT = $OpenAiEndpoint
$env:AZURE_OPENAI_API_KEY = $OpenAiApiKey
$env:AZURE_OPENAI_DEPLOYMENT_NAME = $OpenAiDeploymentName

Write-Host "`n🔐 Authentication Configuration:" -ForegroundColor Yellow
Write-Host "Tenant ID: $AzureTenantId" -ForegroundColor Cyan
Write-Host "Client ID: $AzureClientId" -ForegroundColor Cyan
Write-Host "Client Secret: [HIDDEN]" -ForegroundColor Cyan

# Phase 1: Cosmos DB
if (-not $SkipCosmos) {
    Write-Host "`n🏗️ PHASE 1: COSMOS DB DEPLOYMENT" -ForegroundColor Magenta
    Write-Host "=================================" -ForegroundColor Magenta
    
    & "$PSScriptRoot\deploy-phase1-cosmos.ps1" -ResourceGroupName $ResourceGroupName -Location $Location -Environment $Environment -AppNamePrefix $AppNamePrefix
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Phase 1 failed. Stopping deployment." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n✅ Phase 1 completed successfully!" -ForegroundColor Green
    Start-Sleep -Seconds 5
} else {
    Write-Host "`n⏭️  Skipping Phase 1: Cosmos DB" -ForegroundColor Yellow
}

# Phase 2: Frontend with Entra ID
if (-not $SkipFrontend) {
    Write-Host "`n🌐 PHASE 2: FRONTEND DEPLOYMENT WITH ENTRA ID" -ForegroundColor Magenta
    Write-Host "=============================================" -ForegroundColor Magenta
    
    $frontendAppServiceName = "$AppNamePrefix-$Environment-frontend"
    $backendAppServiceName = "$AppNamePrefix-$Environment-backend"
    
    # Deploy frontend using existing script
    & "$PSScriptRoot\deploy-phase2-frontend.ps1" -ResourceGroupName $ResourceGroupName -Location $Location -Environment $Environment -AppNamePrefix $AppNamePrefix
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Phase 2 failed. Stopping deployment." -ForegroundColor Red
        exit 1
    }
    
    # Configure Entra ID settings for frontend
    Write-Host "`n🔐 Configuring Entra ID for Frontend..." -ForegroundColor Blue
    
    $frontendSettings = @(
        "VITE_API_BASE_URL=https://$backendAppServiceName.azurewebsites.net",
        "VITE_AZURE_CLIENT_ID=$AzureClientId",
        "VITE_AZURE_TENANT_ID=$AzureTenantId",
        "VITE_AZURE_AUTHORITY=https://login.microsoftonline.com/$AzureTenantId",
        "VITE_REDIRECT_URI=https://$frontendAppServiceName.azurewebsites.net/auth/callback",
        "VITE_ENVIRONMENT=production"
    )
    
    foreach ($setting in $frontendSettings) {
        $parts = $setting -split "=", 2
        $name = $parts[0]
        $value = $parts[1]
        
        Write-Host "Setting $name = $value" -ForegroundColor Gray
        
        az webapp config appsettings set `
            --name $frontendAppServiceName `
            --resource-group $ResourceGroupName `
            --settings "$name=$value" `
            --only-show-errors | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to set $name" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "`n✅ Phase 2 completed successfully!" -ForegroundColor Green
    Start-Sleep -Seconds 5
} else {
    Write-Host "`n⏭️  Skipping Phase 2: Frontend" -ForegroundColor Yellow
}

# Phase 3: Backend with Entra ID
if (-not $SkipBackend) {
    Write-Host "`n🐍 PHASE 3: BACKEND DEPLOYMENT WITH ENTRA ID" -ForegroundColor Magenta
    Write-Host "=============================================" -ForegroundColor Magenta
    
    $backendAppServiceName = "$AppNamePrefix-$Environment-backend"
    
    # Deploy backend using existing script
    & "$PSScriptRoot\deploy-phase3-backend.ps1" -ResourceGroupName $ResourceGroupName -Location $Location -Environment $Environment -AppNamePrefix $AppNamePrefix
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Phase 3 failed. Stopping deployment." -ForegroundColor Red
        exit 1
    }
    
    # Configure Entra ID settings for backend
    Write-Host "`n🔐 Configuring Entra ID for Backend..." -ForegroundColor Blue
    
    $backendSettings = @(
        "AZURE_TENANT_ID=$AzureTenantId",
        "AZURE_CLIENT_ID=$AzureClientId",
        "AZURE_CLIENT_SECRET=$AzureClientSecret",
        "COSMOS_DB_ENDPOINT=$CosmosDbEndpoint",
        "COSMOS_DB_KEY=$CosmosDbKey",
        "COSMOS_DB_DATABASE_NAME=ecommerce-db",
        "AZURE_OPENAI_ENDPOINT=$OpenAiEndpoint",
        "AZURE_OPENAI_API_KEY=$OpenAiApiKey",
        "AZURE_OPENAI_DEPLOYMENT_NAME=$OpenAiDeploymentName",
        "AZURE_OPENAI_API_VERSION=2025-01-01-preview",
        "ALLOWED_ORIGINS_STR=https://$AppNamePrefix-$Environment-frontend.azurewebsites.net"
    )
    
    foreach ($setting in $backendSettings) {
        $parts = $setting -split "=", 2
        $name = $parts[0]
        $value = $parts[1]
        
        Write-Host "Setting $name = $value" -ForegroundColor Gray
        
        az webapp config appsettings set `
            --name $backendAppServiceName `
            --resource-group $ResourceGroupName `
            --settings "$name=$value" `
            --only-show-errors | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to set $name" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "`n✅ Phase 3 completed successfully!" -ForegroundColor Green
    Start-Sleep -Seconds 5
} else {
    Write-Host "`n⏭️  Skipping Phase 3: Backend" -ForegroundColor Yellow
}

# Phase 4: Integration Test
if (-not $SkipIntegration) {
    Write-Host "`n🔍 PHASE 4: INTEGRATION TEST" -ForegroundColor Magenta
    Write-Host "============================" -ForegroundColor Magenta
    
    & "$PSScriptRoot\deploy-phase4-integration.ps1" -ResourceGroupName $ResourceGroupName -Environment $Environment -AppNamePrefix $AppNamePrefix
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Phase 4 failed. Please check the integration test results." -ForegroundColor Red
    } else {
        Write-Host "`n✅ Phase 4 completed successfully!" -ForegroundColor Green
    }
} else {
    Write-Host "`n⏭️  Skipping Phase 4: Integration Test" -ForegroundColor Yellow
}

# Final Summary
$resourceNamePrefix = "$AppNamePrefix-$Environment"
$backendUrl = "https://$resourceNamePrefix-backend.azurewebsites.net"
$frontendUrl = "https://$resourceNamePrefix-frontend.azurewebsites.net"

Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host "✅ All phases completed successfully!" -ForegroundColor Green

Write-Host "`n🔗 YOUR APPLICATION" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow
Write-Host "🌐 Frontend: $frontendUrl" -ForegroundColor White
Write-Host "🐍 Backend: $backendUrl" -ForegroundColor White
Write-Host "📚 API Docs: $backendUrl/docs" -ForegroundColor White

Write-Host "`n🔐 AUTHENTICATION SETUP" -ForegroundColor Yellow
Write-Host "=======================" -ForegroundColor Yellow
Write-Host "✅ Entra ID authentication configured" -ForegroundColor Green
Write-Host "✅ Frontend configured with client ID: $AzureClientId" -ForegroundColor Green
Write-Host "✅ Backend configured with tenant ID: $AzureTenantId" -ForegroundColor Green

Write-Host "`n📋 QUICK START" -ForegroundColor Yellow
Write-Host "==============" -ForegroundColor Yellow
Write-Host "1. Open your browser and go to: $frontendUrl" -ForegroundColor White
Write-Host "2. Click 'Login' to authenticate with Microsoft" -ForegroundColor White
Write-Host "3. Test the chat functionality" -ForegroundColor White
Write-Host "4. Add items to cart and test checkout" -ForegroundColor White
Write-Host "5. Check the API documentation at: $backendUrl/docs" -ForegroundColor White

Write-Host "`n⚠️  IMPORTANT NOTES" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow
Write-Host "• Make sure your Azure App Registration has the correct redirect URIs:" -ForegroundColor White
Write-Host "  - $frontendUrl" -ForegroundColor Cyan
Write-Host "  - $frontendUrl/auth/callback" -ForegroundColor Cyan
Write-Host "• The app registration should be configured as 'Single-page application (SPA)'" -ForegroundColor White
Write-Host "• Required API permissions: User.Read, openid, profile" -ForegroundColor White

Write-Host "`n✨ Happy coding!" -ForegroundColor Green

