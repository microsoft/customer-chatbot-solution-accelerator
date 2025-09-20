# Azure Cosmos DB Emulator Setup Script for Windows
# This script helps you set up the Cosmos DB Emulator for local development

Write-Host "Setting up Azure Cosmos DB Emulator for local development..." -ForegroundColor Green

# Check if Docker is available
$dockerAvailable = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerAvailable) {
    Write-Host "Docker is available. Setting up Cosmos DB Emulator with Docker..." -ForegroundColor Yellow
    
    # Stop any existing emulator container
    docker stop cosmosdb-emulator 2>$null
    docker rm cosmosdb-emulator 2>$null
    
    # Pull the latest emulator image
    Write-Host "Pulling Azure Cosmos DB Emulator Docker image..." -ForegroundColor Yellow
    docker pull mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
    
    # Run the emulator
    Write-Host "Starting Azure Cosmos DB Emulator..." -ForegroundColor Yellow
    docker run -d `
        -p 8081:8081 `
        -p 10251:10251 `
        -p 10252:10252 `
        -p 10253:10253 `
        -p 10254:10254 `
        -m 3g `
        --cpus=2.0 `
        --name=cosmosdb-emulator `
        -e AZURE_COSMOS_EMULATOR_PARTITION_COUNT=10 `
        -e AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE=true `
        -e AZURE_COSMOS_EMULATOR_IP_ADDRESS_OVERRIDE=127.0.0.1 `
        mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
    
    Write-Host "Cosmos DB Emulator is starting up..." -ForegroundColor Yellow
    Write-Host "Waiting for emulator to be ready..." -ForegroundColor Yellow
    
    # Wait for emulator to be ready
    $maxAttempts = 30
    $attempt = 0
    do {
        Start-Sleep -Seconds 2
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "https://localhost:8081" -SkipCertificateCheck -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "Cosmos DB Emulator is ready!" -ForegroundColor Green
                break
            }
        } catch {
            Write-Host "Attempt $attempt/$maxAttempts - Emulator not ready yet..." -ForegroundColor Yellow
        }
    } while ($attempt -lt $maxAttempts)
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "Emulator may still be starting. Please wait a moment and check manually." -ForegroundColor Yellow
    }
    
} else {
    Write-Host "Docker not found. Please install Docker Desktop or use the Windows installer." -ForegroundColor Red
    Write-Host "Download the Azure Cosmos DB Emulator from: https://learn.microsoft.com/en-us/azure/cosmos-db/emulator" -ForegroundColor Yellow
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Open https://localhost:8081/_explorer/index.html in your browser" -ForegroundColor White
Write-Host "2. Copy the Primary Key from the Quickstart section" -ForegroundColor White
Write-Host "3. Update your .env file with:" -ForegroundColor White
Write-Host "   COSMOS_DB_ENDPOINT=https://localhost:8081" -ForegroundColor Gray
Write-Host "   COSMOS_DB_KEY=<your-primary-key>" -ForegroundColor Gray
Write-Host "4. Run: python app/main.py" -ForegroundColor White
