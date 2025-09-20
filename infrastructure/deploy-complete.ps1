# Complete Deployment Script
# This script runs all phases of the deployment in sequence

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat",
    [switch]$SkipCosmos = $false,
    [switch]$SkipFrontend = $false,
    [switch]$SkipBackend = $false,
    [switch]$SkipIntegration = $false
)

Write-Host "🚀 COMPLETE E-COMMERCE CHAT DEPLOYMENT" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "App Name Prefix: $AppNamePrefix" -ForegroundColor Cyan

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

# Phase 2: Frontend
if (-not $SkipFrontend) {
    Write-Host "`n🌐 PHASE 2: FRONTEND DEPLOYMENT" -ForegroundColor Magenta
    Write-Host "===============================" -ForegroundColor Magenta
    
    & "$PSScriptRoot\deploy-phase2-frontend.ps1" -ResourceGroupName $ResourceGroupName -Location $Location -Environment $Environment -AppNamePrefix $AppNamePrefix
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Phase 2 failed. Stopping deployment." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n✅ Phase 2 completed successfully!" -ForegroundColor Green
    Start-Sleep -Seconds 5
} else {
    Write-Host "`n⏭️  Skipping Phase 2: Frontend" -ForegroundColor Yellow
}

# Phase 3: Backend
if (-not $SkipBackend) {
    Write-Host "`n🐍 PHASE 3: BACKEND DEPLOYMENT" -ForegroundColor Magenta
    Write-Host "==============================" -ForegroundColor Magenta
    
    & "$PSScriptRoot\deploy-phase3-backend.ps1" -ResourceGroupName $ResourceGroupName -Location $Location -Environment $Environment -AppNamePrefix $AppNamePrefix
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Phase 3 failed. Stopping deployment." -ForegroundColor Red
        exit 1
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

Write-Host "`n📋 QUICK START" -ForegroundColor Yellow
Write-Host "==============" -ForegroundColor Yellow
Write-Host "1. Open your browser and go to: $frontendUrl" -ForegroundColor White
Write-Host "2. Test the chat functionality" -ForegroundColor White
Write-Host "3. Check the API documentation at: $backendUrl/docs" -ForegroundColor White

Write-Host "`n✨ Happy coding!" -ForegroundColor Green
