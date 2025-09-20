# Local Development Setup Script
# This script sets up both backend and frontend for local development with authentication

Write-Host "🚀 Setting up Local Development Environment" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "backend") -or -not (Test-Path "modern-e-commerce-ch")) {
    Write-Host "❌ Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Step 1: Setup Backend
Write-Host "`n🐍 Setting up Backend..." -ForegroundColor Blue
Write-Host "=========================" -ForegroundColor Blue

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item "env.local.example" ".env"
    Write-Host "✅ Created .env file. Please update it with your Cosmos DB credentials." -ForegroundColor Green
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

Write-Host "✅ Backend setup complete" -ForegroundColor Green

# Step 2: Setup Frontend
Write-Host "`n⚛️ Setting up Frontend..." -ForegroundColor Blue
Write-Host "=========================" -ForegroundColor Blue

Set-Location ../modern-e-commerce-ch

# Install Node dependencies
Write-Host "Installing Node dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install Node dependencies" -ForegroundColor Red
    exit 1
}

# Create .env.local file if it doesn't exist
if (-not (Test-Path ".env.local")) {
    Write-Host "Creating .env.local file..." -ForegroundColor Yellow
    @"
VITE_API_BASE_URL=http://localhost:8000
VITE_AZURE_CLIENT_ID=local-dev
VITE_AZURE_AUTHORITY=https://login.microsoftonline.com/common
"@ | Out-File -FilePath ".env.local" -Encoding UTF8
    Write-Host "✅ Created .env.local file for local development" -ForegroundColor Green
} else {
    Write-Host "✅ .env.local file already exists" -ForegroundColor Green
}

Write-Host "✅ Frontend setup complete" -ForegroundColor Green

# Step 3: Instructions
Write-Host "`n🎉 Setup Complete!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Start the backend:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Cyan
Write-Host "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan

Write-Host "`n2. Start the frontend (in a new terminal):" -ForegroundColor White
Write-Host "   cd modern-e-commerce-ch" -ForegroundColor Cyan
Write-Host "   npm run dev" -ForegroundColor Cyan

Write-Host "`n3. Open your browser:" -ForegroundColor White
Write-Host "   http://localhost:5173" -ForegroundColor Cyan

Write-Host "`n🔐 Authentication:" -ForegroundColor Yellow
Write-Host "- Mock authentication is enabled by default" -ForegroundColor White
Write-Host "- Click 'Login' to authenticate with mock user" -ForegroundColor White
Write-Host "- For real Entra ID, see LOCAL_AUTH_SETUP.md" -ForegroundColor White

Write-Host "`n✨ Features Available:" -ForegroundColor Yellow
Write-Host "- Product browsing and search" -ForegroundColor White
Write-Host "- Shopping cart functionality" -ForegroundColor White
Write-Host "- AI-powered chat" -ForegroundColor White
Write-Host "- User authentication" -ForegroundColor White
Write-Host "- Responsive design" -ForegroundColor White

Set-Location ..
Write-Host "`n🚀 Ready to develop!" -ForegroundColor Green
