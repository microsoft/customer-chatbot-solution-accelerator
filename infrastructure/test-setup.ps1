# Test Setup Script
Write-Host "🧪 Testing E-commerce Chat Application Setup" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Test 1: Check if backend is running
Write-Host "`n🔍 Test 1: Checking Backend API..." -ForegroundColor Blue
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/products" -Method GET -TimeoutSec 10
    Write-Host "✅ Backend API is running!" -ForegroundColor Green
    Write-Host "📊 Found $($response.Count) products" -ForegroundColor Cyan
    
    # Show first few products
    if ($response.Count -gt 0) {
        Write-Host "`n📦 Sample Products:" -ForegroundColor Yellow
        $response[0..2] | ForEach-Object {
            Write-Host "  • $($_.title) - $$($_.price)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "❌ Backend API is not running or not accessible" -ForegroundColor Red
    Write-Host "💡 Start backend with: cd ../backend && python -m uvicorn app.main:app --reload" -ForegroundColor Yellow
}

# Test 2: Check if frontend is running
Write-Host "`n🔍 Test 2: Checking Frontend..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -TimeoutSec 10
    Write-Host "✅ Frontend is running!" -ForegroundColor Green
    Write-Host "🌐 Frontend URL: http://localhost:5173" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Frontend is not running or not accessible" -ForegroundColor Red
    Write-Host "💡 Start frontend with: cd ../modern-e-commerce-ch && npm run dev" -ForegroundColor Yellow
}

# Test 3: Check Cosmos DB connection
Write-Host "`n🔍 Test 3: Checking Cosmos DB..." -ForegroundColor Blue
if (Test-Path "cosmos-connection-string.txt") {
    Write-Host "✅ Cosmos DB connection string found" -ForegroundColor Green
} else {
    Write-Host "❌ Cosmos DB connection string not found" -ForegroundColor Red
    Write-Host "💡 Run: .\get-connection-string.ps1" -ForegroundColor Yellow
}

Write-Host "`n📋 Summary:" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White

Write-Host "`n✨ Test completed!" -ForegroundColor Green
