# Update environment variables for Cosmos DB Emulator
# Run this after setting up the emulator

Write-Host "Updating environment variables for Cosmos DB Emulator..." -ForegroundColor Green

# Default emulator settings
$endpoint = "https://localhost:8081"
$key = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="

Write-Host "Setting environment variables..." -ForegroundColor Yellow

# Set environment variables for current session
$env:COSMOS_DB_ENDPOINT = $endpoint
$env:COSMOS_DB_KEY = $key

Write-Host "Environment variables set for current session:" -ForegroundColor Green
Write-Host "COSMOS_DB_ENDPOINT = $endpoint" -ForegroundColor White
Write-Host "COSMOS_DB_KEY = $key" -ForegroundColor White

Write-Host "`nTo make these permanent, add them to your system environment variables or create a .env file." -ForegroundColor Cyan

# Test the connection
Write-Host "`nTesting connection to Cosmos DB Emulator..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://localhost:8081" -SkipCertificateCheck -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Cosmos DB Emulator is accessible!" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Cannot connect to Cosmos DB Emulator. Make sure it's running." -ForegroundColor Red
    Write-Host "Run: .\setup-cosmos-emulator.ps1" -ForegroundColor Yellow
}
