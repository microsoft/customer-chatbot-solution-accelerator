param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$BackendUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$webAppName = "frontend-simple-$timestamp"
$planName = "frontend-plan"
$registryName = "ecreg$timestamp"
$imageName = "frontend"
$tag = "v1"
$fullImageName = "$registryName.azurecr.io/${imageName}:${tag}"

Write-Host "🚀 Simple Container Deployment" -ForegroundColor Green
Write-Host "Web App: $webAppName" -ForegroundColor Yellow
Write-Host "Image: $fullImageName" -ForegroundColor Yellow

try {
    # Check prerequisites
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker not found. Please install Docker Desktop."
    }

    # Get paths
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    $frontendDir = Join-Path $projectRoot "modern-e-commerce-ch"
    
    if (-not (Test-Path $frontendDir)) {
        throw "Frontend directory not found: $frontendDir"
    }

    # Create registry
    Write-Host "Creating container registry..." -ForegroundColor Blue
    az acr create `
        --name $registryName `
        --resource-group $ResourceGroupName `
        --location $Location `
        --sku Basic `
        --admin-enabled true `
        --only-show-errors
    Write-Host "✓ Registry created" -ForegroundColor Green

    # Login to registry
    Write-Host "Logging into registry..." -ForegroundColor Blue
    az acr login --name $registryName
    Write-Host "✓ Logged in" -ForegroundColor Green

    # Build locally
    Write-Host "Building container locally..." -ForegroundColor Blue
    Push-Location $frontendDir
    try {
        # Create production env
        $envContent = @"
VITE_API_BASE_URL=$BackendUrl
NODE_ENV=production
"@
        $envContent | Out-File -FilePath ".env.production" -Encoding UTF8

        # Build container
        docker build -t $fullImageName . --no-cache
        if ($LASTEXITCODE -ne 0) {
            throw "Docker build failed"
        }
        Write-Host "✓ Container built locally" -ForegroundColor Green

        # Push to registry
        Write-Host "Pushing to registry..." -ForegroundColor Blue
        docker push $fullImageName
        if ($LASTEXITCODE -ne 0) {
            throw "Docker push failed"
        }
        Write-Host "✓ Image pushed" -ForegroundColor Green

    } finally {
        Remove-Item ".env.production" -Force -ErrorAction SilentlyContinue
        Pop-Location
    }

    # Create app service plan
    Write-Host "Creating app service plan..." -ForegroundColor Blue
    $planExists = az appservice plan show --name $planName --resource-group $ResourceGroupName 2>$null
    if (-not $planExists) {
        az appservice plan create `
            --name $planName `
            --resource-group $ResourceGroupName `
            --location $Location `
            --sku B1 `
            --is-linux `
            --only-show-errors
    }
    Write-Host "✓ App service plan ready" -ForegroundColor Green

    # Create web app
    Write-Host "Creating web app..." -ForegroundColor Blue
    az webapp create `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --plan $planName `
        --deployment-container-image-name $fullImageName `
        --only-show-errors
    Write-Host "✓ Web app created" -ForegroundColor Green

    # Configure registry access
    Write-Host "Configuring registry access..." -ForegroundColor Blue
    $acrCreds = az acr credential show --name $registryName | ConvertFrom-Json
    
    az webapp config container set `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --docker-custom-image-name $fullImageName `
        --docker-registry-server-url "https://$registryName.azurecr.io" `
        --docker-registry-server-user $acrCreds.username `
        --docker-registry-server-password $acrCreds.passwords[0].value `
        --only-show-errors

    # Set app settings
    az webapp config appsettings set `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --settings `
        WEBSITES_ENABLE_APP_SERVICE_STORAGE="false" `
        WEBSITES_PORT="80" `
        --only-show-errors

    Write-Host "✓ Configuration complete" -ForegroundColor Green

    $url = "https://$webAppName.azurewebsites.net"
    Write-Host "" -ForegroundColor Green
    Write-Host "✅ SUCCESS!" -ForegroundColor Green
    Write-Host "🌐 URL: $url" -ForegroundColor Cyan
    Write-Host "Wait 2-3 minutes for container to start, then test the URL." -ForegroundColor Yellow

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

