# Setup Backend for Cosmos DB Connection
Write-Host "🔧 Setting up Backend for Cosmos DB..." -ForegroundColor Green

# Get the connection string
Write-Host "🔗 Getting Cosmos DB Connection String..." -ForegroundColor Blue
.\get-connection-string.ps1

if (Test-Path "cosmos-connection-string.txt") {
    $connectionString = Get-Content "cosmos-connection-string.txt" -Raw
    
    # Extract endpoint and key from connection string
    $endpoint = ($connectionString -split "AccountEndpoint=")[1] -split ";")[0]
    $key = ($connectionString -split "AccountKey=")[1] -split ";")[0]
    
    Write-Host "📝 Creating backend .env file..." -ForegroundColor Blue
    
    # Create .env file for backend
    $envContent = @"
# Azure Cosmos DB
COSMOS_DB_ENDPOINT=$endpoint
COSMOS_DB_KEY=$key
COSMOS_DB_DATABASE_NAME=ecommerce-db

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Key Vault
AZURE_KEY_VAULT_URL=your_key_vault_url

# Microsoft Entra ID
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id

# Application Configuration
DEBUG=true
HOST=0.0.0.0
PORT=8000
"@
    
    $envContent | Out-File -FilePath "../backend/.env" -Encoding UTF8
    
    Write-Host "✅ Backend .env file created!" -ForegroundColor Green
    Write-Host "📍 Location: ../backend/.env" -ForegroundColor Cyan
    
    Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Run: cd ../backend" -ForegroundColor White
    Write-Host "2. Run: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "3. Run: python -m uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "4. Test: http://localhost:8000/api/products" -ForegroundColor White
    
} else {
    Write-Host "❌ Connection string file not found. Please run get-connection-string.ps1 first." -ForegroundColor Red
}
