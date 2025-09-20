# Build Frontend Script
# This script builds the React frontend for production deployment

param(
    [string]$FrontendPath = "..\modern-e-commerce-ch"
)

Write-Host "🔨 BUILDING FRONTEND FOR PRODUCTION" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

$fullFrontendPath = Join-Path $PSScriptRoot $FrontendPath
if (-not (Test-Path $fullFrontendPath)) {
    Write-Host "❌ Frontend directory not found at: $fullFrontendPath" -ForegroundColor Red
    exit 1
}

Write-Host "`n📁 Frontend path: $fullFrontendPath" -ForegroundColor Blue

# Check if Node.js is installed
Write-Host "`n🔍 Checking Node.js..." -ForegroundColor Blue
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Check if npm is available
try {
    $npmVersion = npm --version
    Write-Host "✅ npm version: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm not found. Please install npm first." -ForegroundColor Red
    exit 1
}

# Build the frontend
Write-Host "`n🚀 Building frontend..." -ForegroundColor Blue
Push-Location $fullFrontendPath
try {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm install failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Building production bundle..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm run build failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Frontend built successfully!" -ForegroundColor Green
    Write-Host "📦 Build output: $fullFrontendPath\dist" -ForegroundColor Cyan
    
} finally {
    Pop-Location
}

Write-Host "`n🎉 BUILD COMPLETE!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host "✅ Production files ready in dist/ folder" -ForegroundColor Green
Write-Host "✅ Ready for deployment" -ForegroundColor Green

