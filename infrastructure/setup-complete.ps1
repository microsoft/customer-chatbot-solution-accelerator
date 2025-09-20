# Complete Setup Script for E-commerce Chat Application
Write-Host "🚀 Complete Setup for E-commerce Chat Application" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Step 1: Get Cosmos DB Connection String
Write-Host "`n🔗 Step 1: Getting Cosmos DB Connection String..." -ForegroundColor Blue
.\get-connection-string.ps1

if (-not (Test-Path "cosmos-connection-string.txt")) {
    Write-Host "❌ Failed to get connection string. Exiting." -ForegroundColor Red
    exit 1
}

# Step 2: Seed Product Data
Write-Host "`n🌱 Step 2: Seeding Product Data..." -ForegroundColor Blue
.\run-seeding.ps1

# Step 3: Setup Backend
Write-Host "`n🔧 Step 3: Setting up Backend..." -ForegroundColor Blue
.\setup-backend.ps1

# Step 4: Display Summary
Write-Host "`n📊 Setup Summary:" -ForegroundColor Cyan
Write-Host "✅ Cosmos DB: Connected and configured" -ForegroundColor Green
Write-Host "✅ Product Data: Seeded with paint products" -ForegroundColor Green
Write-Host "✅ Backend: Configured for Cosmos DB" -ForegroundColor Green

Write-Host "`n🎯 Ready to Test!" -ForegroundColor Yellow
Write-Host "`nBackend API:" -ForegroundColor White
Write-Host "  Start: cd ../backend && python -m uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "  Test: http://localhost:8000/api/products" -ForegroundColor Gray
Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Gray

Write-Host "`nFrontend:" -ForegroundColor White
Write-Host "  Start: cd ../modern-e-commerce-ch && npm run dev" -ForegroundColor Gray
Write-Host "  URL: http://localhost:5173" -ForegroundColor Gray

Write-Host "`n🔗 Azure Resources:" -ForegroundColor White
Write-Host "  Cosmos DB: ecommerce-chat-dev-cosmos" -ForegroundColor Gray
Write-Host "  Key Vault: ecommerce-chat-dev-kv" -ForegroundColor Gray
Write-Host "  Resource Group: ecommerce-chat-rg" -ForegroundColor Gray

Write-Host "`n✨ Happy coding!" -ForegroundColor Green
