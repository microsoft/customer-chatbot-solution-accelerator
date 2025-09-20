# Phase 4: Integration Test
# This script tests the complete deployment and verifies frontend-backend communication

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 4: INTEGRATION TEST" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green

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

# Find the most recent deployments
Write-Host "`n🔍 Finding deployed services..." -ForegroundColor Blue

$frontendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'frontend') || contains(name, 'ecommerce-frontend')].name" -o tsv
$backendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'backend') || contains(name, 'ecommerce-backend')].name" -o tsv

if (-not $frontendApps) {
    Write-Host "❌ No frontend deployment found" -ForegroundColor Red
    exit 1
}

if (-not $backendApps) {
    Write-Host "❌ No backend deployment found" -ForegroundColor Red
    exit 1
}

# Use the most recent deployments
$frontendAppServiceName = ($frontendApps -split "`n")[-1]
$backendAppServiceName = ($backendApps -split "`n")[-1]
$backendUrl = "https://$backendAppServiceName.azurewebsites.net"
$frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

Write-Host "✅ Found frontend: $frontendAppServiceName" -ForegroundColor Green
Write-Host "✅ Found backend: $backendAppServiceName" -ForegroundColor Green

Write-Host "`n🔍 Testing Backend Services..." -ForegroundColor Blue

# Test 1: Backend Health Check
Write-Host "`n1️⃣ Testing Backend Health..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$backendUrl/health" -Method GET -TimeoutSec 30
    Write-Host "✅ Backend health check passed" -ForegroundColor Green
    Write-Host "   Status: $($healthResponse.status)" -ForegroundColor Cyan
    Write-Host "   Database: $($healthResponse.database)" -ForegroundColor Cyan
    Write-Host "   OpenAI: $($healthResponse.openai)" -ForegroundColor Cyan
    Write-Host "   Auth: $($healthResponse.auth)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Backend health check failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Please check the backend deployment and try again." -ForegroundColor Yellow
}

# Test 2: Backend API Endpoints
Write-Host "`n2️⃣ Testing Backend API Endpoints..." -ForegroundColor Yellow

# Test root endpoint
try {
    $rootResponse = Invoke-RestMethod -Uri "$backendUrl/" -Method GET -TimeoutSec 30
    Write-Host "✅ Root endpoint working" -ForegroundColor Green
    Write-Host "   Message: $($rootResponse.message)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Root endpoint failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test products endpoint
try {
    $productsResponse = Invoke-RestMethod -Uri "$backendUrl/products" -Method GET -TimeoutSec 30
    Write-Host "✅ Products endpoint working" -ForegroundColor Green
    Write-Host "   Products count: $($productsResponse.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Products endpoint failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Frontend Accessibility
Write-Host "`n3️⃣ Testing Frontend Accessibility..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -Method GET -TimeoutSec 30
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend is accessible" -ForegroundColor Green
        Write-Host "   Status Code: $($frontendResponse.StatusCode)" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Frontend returned status code: $($frontendResponse.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Frontend accessibility test failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: CORS Configuration
Write-Host "`n4️⃣ Testing CORS Configuration..." -ForegroundColor Yellow
try {
    $corsHeaders = @{
        'Origin' = $frontendUrl
        'Access-Control-Request-Method' = 'GET'
        'Access-Control-Request-Headers' = 'Content-Type'
    }
    
    $corsResponse = Invoke-WebRequest -Uri "$backendUrl/" -Method OPTIONS -Headers $corsHeaders -TimeoutSec 30
    if ($corsResponse.Headers['Access-Control-Allow-Origin']) {
        Write-Host "✅ CORS configuration working" -ForegroundColor Green
        Write-Host "   Allowed Origin: $($corsResponse.Headers['Access-Control-Allow-Origin'])" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  CORS headers not found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ CORS test failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Database Connectivity
Write-Host "`n5️⃣ Testing Database Connectivity..." -ForegroundColor Yellow
try {
    $cosmosAccounts = az cosmosdb list --resource-group $ResourceGroupName --query "[].name" -o tsv
    if ($cosmosAccounts) {
        $cosmosDbName = $cosmosAccounts[0]
        $cosmosEndpoint = az cosmosdb show --name $cosmosDbName --resource-group $ResourceGroupName --query "documentEndpoint" -o tsv
        Write-Host "✅ Cosmos DB connection details retrieved" -ForegroundColor Green
        Write-Host "   Database: $cosmosDbName" -ForegroundColor Cyan
        Write-Host "   Endpoint: $cosmosEndpoint" -ForegroundColor Cyan
    } else {
        Write-Host "❌ No Cosmos DB accounts found" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Database connectivity test failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n📊 DEPLOYMENT SUMMARY" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
Write-Host "✅ Resource Group: $ResourceGroupName" -ForegroundColor Green
Write-Host "✅ Backend URL: $backendUrl" -ForegroundColor Green
Write-Host "✅ Frontend URL: $frontendUrl" -ForegroundColor Green
Write-Host "✅ Environment: $Environment" -ForegroundColor Green

Write-Host "`n🔗 IMPORTANT LINKS" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow
Write-Host "🌐 Frontend Application: $frontendUrl" -ForegroundColor White
Write-Host "🐍 Backend API: $backendUrl" -ForegroundColor White
Write-Host "📚 API Documentation: $backendUrl/docs" -ForegroundColor White
Write-Host "🔍 Health Check: $backendUrl/health" -ForegroundColor White

Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host "Your e-commerce chat application is now deployed and running on Azure!" -ForegroundColor Green

Write-Host "`n📋 NEXT STEPS" -ForegroundColor Yellow
Write-Host "=============" -ForegroundColor Yellow
Write-Host "1. Visit your frontend application: $frontendUrl" -ForegroundColor White
Write-Host "2. Test the chat functionality" -ForegroundColor White
Write-Host "3. Check the API documentation: $backendUrl/docs" -ForegroundColor White
Write-Host "4. Monitor your application in the Azure portal" -ForegroundColor White

Write-Host "`n🔧 TROUBLESHOOTING" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow
Write-Host "If you encounter issues:" -ForegroundColor White
Write-Host "1. Check the Azure App Service logs" -ForegroundColor White
Write-Host "2. Verify environment variables in App Service configuration" -ForegroundColor White
Write-Host "3. Test individual endpoints using the API documentation" -ForegroundColor White
Write-Host "4. Check Cosmos DB connectivity and data" -ForegroundColor White

Write-Host "`n✨ Happy coding!" -ForegroundColor Green
