param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$BackendUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMddHHmm"
$webAppName = "ecommerce-backend-$timestamp"
$planName = "frontend-plan"
$registryName = "ecreg$timestamp"
$imageName = "backend:latest"
$fullImageName = "$registryName.azurecr.io/$imageName"

Write-Host "🚀 Deploying Backend via Container" -ForegroundColor Green
Write-Host "Web App: $webAppName" -ForegroundColor Yellow
Write-Host "Registry: $registryName" -ForegroundColor Yellow
Write-Host "Container Image: $fullImageName" -ForegroundColor Yellow

try {
    # Check prerequisites
    $azCheck = az --version 2>$null
    if (-not $azCheck) {
        throw "Azure CLI not found. Please install Azure CLI first."
    }

    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        throw "Not logged into Azure. Please run 'az login' first."
    }
    
    Write-Host "Logged in as: $($account.user.name)" -ForegroundColor Green

    # Get paths
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    $backendDir = Join-Path $projectRoot "backend"
    
    if (-not (Test-Path $backendDir)) {
        throw "Backend directory not found: $backendDir"
    }
    
    Write-Host "Backend directory: $backendDir" -ForegroundColor Gray

    # Find frontend for CORS
    $frontendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'frontend')].name" -o tsv
    if ($frontendApps) {
        $frontendName = ($frontendApps -split "`n")[-1]
        $frontendUrl = "https://$frontendName.azurewebsites.net"
        Write-Host "✅ Found frontend: $frontendName" -ForegroundColor Green
    } else {
        $frontendUrl = "http://localhost:5173"
        Write-Host "⚠️  No frontend found, using localhost" -ForegroundColor Yellow
    }

    # Create unique registry
    Write-Host "Creating Azure Container Registry: $registryName" -ForegroundColor Blue
    
    $nameCheck = az acr check-name --name $registryName | ConvertFrom-Json
    if (-not $nameCheck.nameAvailable) {
        $timestamp = Get-Date -Format "yyyyMMddHHmmss"
        $registryName = "ecreg$timestamp"
        $fullImageName = "$registryName.azurecr.io/$imageName"
        Write-Host "Registry name taken, using: $registryName" -ForegroundColor Yellow
    }
    
    $createResult = az acr create `
        --name $registryName `
        --resource-group $ResourceGroupName `
        --location $Location `
        --sku Basic `
        --admin-enabled true 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Registry creation output: $createResult" -ForegroundColor Red
        throw "Failed to create container registry: $registryName"
    }
    
    Write-Host "✓ Azure Container Registry created: $registryName" -ForegroundColor Green

    # Build and push container image
    Write-Host "Building and pushing container image..." -ForegroundColor Blue
    Push-Location $backendDir
    try {
        # Create Dockerfile for backend
        $dockerfileContent = @"
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"@
        $dockerfileContent | Out-File -FilePath "Dockerfile" -Encoding UTF8

        # Create .dockerignore
        $dockerignoreContent = @"
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.venv
venv/
.vscode/
.idea/
*.swp
*.swo
"@
        $dockerignoreContent | Out-File -FilePath ".dockerignore" -Encoding UTF8

        # No need for build-time environment file for backend
        # Backend gets all config from App Service environment variables

        # Build and push to ACR
        Write-Host "Building container image..." -ForegroundColor Gray
        
        # Set environment to handle Unicode properly
        $env:PYTHONIOENCODING = "utf-8"
        $env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"
        
        az acr build `
            --registry $registryName `
            --image $imageName `
            --file "Dockerfile" `
            . `
            --no-logs
        
        if ($LASTEXITCODE -ne 0) {
            throw "Container build failed"
        }
        
        # Verify the image was created
        Write-Host "Verifying image was pushed..." -ForegroundColor Gray
        $imageExists = az acr repository show --name $registryName --repository "backend" 2>$null
        if (-not $imageExists) {
            throw "Image was not successfully pushed to registry"
        }
        
        Write-Host "✓ Image verified in registry" -ForegroundColor Green

        # Clean up temp files
        Remove-Item "Dockerfile" -Force -ErrorAction SilentlyContinue
        Remove-Item ".dockerignore" -Force -ErrorAction SilentlyContinue
        
    } finally {
        Pop-Location
    }
    Write-Host "✓ Container image built and pushed" -ForegroundColor Green

    # Create Web App with container
    Write-Host "Creating Web App with container..." -ForegroundColor Blue
    az webapp create `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --plan $planName `
        --deployment-container-image-name $fullImageName `
        --only-show-errors
    Write-Host "✓ Web App created" -ForegroundColor Green

    # Configure container registry credentials
    Write-Host "Configuring container registry access..." -ForegroundColor Blue
    
    Start-Sleep -Seconds 10
    
    $credResult = az acr credential show --name $registryName 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to get ACR credentials: $credResult"
    }
    
    $acrCredentials = $credResult | ConvertFrom-Json
    if (-not $acrCredentials -or -not $acrCredentials.username -or -not $acrCredentials.passwords) {
        throw "Invalid ACR credentials received for registry: $registryName"
    }
    
    Write-Host "✓ ACR credentials obtained" -ForegroundColor Green
    
    az webapp config container set `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --docker-custom-image-name $fullImageName `
        --docker-registry-server-url "https://$registryName.azurecr.io" `
        --docker-registry-server-user $acrCredentials.username `
        --docker-registry-server-password $acrCredentials.passwords[0].value `
        --only-show-errors
    Write-Host "✓ Container registry configured" -ForegroundColor Green

    # Configure app settings
    Write-Host "Configuring app settings..." -ForegroundColor Blue
    az webapp config appsettings set `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --settings `
        WEBSITES_ENABLE_APP_SERVICE_STORAGE="false" `
        WEBSITES_PORT="8000" `
        ALLOWED_ORIGINS_STR="$frontendUrl,http://localhost:5173" `
        --only-show-errors
    Write-Host "✓ App settings configured" -ForegroundColor Green

    $backendUrl = "https://$webAppName.azurewebsites.net"
    
    Write-Host "" -ForegroundColor Green
    Write-Host "✅ SUCCESS! Backend deployed successfully!" -ForegroundColor Green
    Write-Host "🌐 URL: $backendUrl" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Green
    Write-Host "Test URLs:" -ForegroundColor Yellow
    Write-Host "API Docs: $backendUrl/docs" -ForegroundColor White
    Write-Host "Health Check: $backendUrl/health" -ForegroundColor White
    Write-Host "Frontend: $frontendUrl" -ForegroundColor White
    Write-Host "" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Wait 3-5 minutes for container to start" -ForegroundColor White
    Write-Host "2. Test the URLs above" -ForegroundColor White
    Write-Host "3. Run integration tests" -ForegroundColor White

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "For troubleshooting, check:" -ForegroundColor Yellow
    Write-Host "- Azure portal for detailed error messages" -ForegroundColor White
    Write-Host "- Container logs: az webapp log tail --name $webAppName --resource-group $ResourceGroupName" -ForegroundColor White
    exit 1
}
