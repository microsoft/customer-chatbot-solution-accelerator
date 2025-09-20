# Run Product Data Seeding Script
Write-Host "🌱 Starting Product Data Seeding..." -ForegroundColor Green

# First, get the connection string
Write-Host "🔗 Getting Cosmos DB Connection String..." -ForegroundColor Blue
.\get-connection-string.ps1

# Check if connection string file exists
if (Test-Path "cosmos-connection-string.txt") {
    $connectionString = Get-Content "cosmos-connection-string.txt" -Raw
    
    # Update the Python script with the connection string
    Write-Host "📝 Updating seeding script with connection string..." -ForegroundColor Blue
    (Get-Content "seed-products.py") -replace "YOUR_COSMOS_KEY_HERE", $connectionString | Set-Content "seed-products.py"
    
    # Install Python dependencies
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Blue
    pip install -r requirements.txt
    
    # Run the seeding script
    Write-Host "🌱 Running product seeding..." -ForegroundColor Blue
    python seed-products.py
    
    Write-Host "✅ Product seeding completed!" -ForegroundColor Green
} else {
    Write-Host "❌ Connection string file not found. Please run get-connection-string.ps1 first." -ForegroundColor Red
}
