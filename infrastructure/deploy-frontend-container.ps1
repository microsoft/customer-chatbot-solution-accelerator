param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$BackendUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMddHHmm"
$webAppName = "ecommerce-frontend-$timestamp"
$planName = "frontend-plan"
$registryName = "ecreg$timestamp"
$imageName = "frontend:latest"
$fullImageName = "$registryName.azurecr.io/$imageName"

Write-Host "🚀 Deploying React Frontend via Container" -ForegroundColor Green
Write-Host "Web App: $webAppName" -ForegroundColor Yellow
Write-Host "Registry: $registryName" -ForegroundColor Yellow
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Yellow
Write-Host "Container Image: $fullImageName" -ForegroundColor Yellow

try {
    # Check if Azure CLI is available
    $azCheck = az --version 2>$null
    if (-not $azCheck) {
        throw "Azure CLI not found. Please install Azure CLI first."
    }

    # Check if logged in
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        throw "Not logged into Azure. Please run 'az login' first."
    }
    
    Write-Host "Logged in as: $($account.user.name)" -ForegroundColor Green

    # Get the correct paths
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    $frontendDir = Join-Path $projectRoot "modern-e-commerce-ch"
    
    if (-not (Test-Path $frontendDir)) {
        throw "Frontend directory not found: $frontendDir"
    }
    
    Write-Host "Frontend directory: $frontendDir" -ForegroundColor Gray

    # Create unique Azure Container Registry
    Write-Host "Creating Azure Container Registry: $registryName" -ForegroundColor Blue
    
    # Check if registry name is available first
    $nameCheck = az acr check-name --name $registryName | ConvertFrom-Json
    if (-not $nameCheck.nameAvailable) {
        # Generate a new unique name
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
    Push-Location $frontendDir
    try {
        # Create a temporary env file for build-time variables
        $envContent = @"
VITE_API_BASE_URL=$BackendUrl
NODE_ENV=production
"@
        $envContent | Out-File -FilePath ".env.production" -Encoding UTF8

        # Create a comprehensive .dockerignore to handle Windows path issues
        Write-Host "Creating comprehensive .dockerignore..." -ForegroundColor Gray
        $dockerignoreContent = @"
node_modules
node_modules/**
.git
.git/**
.github
.github/**
dist
dist/**
build
build/**
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
Thumbs.db
.vscode
.vscode/**
.nyc_output
.nyc_output/**
coverage
coverage/**
.env
.env.*
README.md
*.md
.gitignore
"@
        $dockerignoreContent | Out-File -FilePath ".dockerignore" -Encoding UTF8 -Force
        Write-Host "✓ Updated .dockerignore with comprehensive exclusions" -ForegroundColor Green
        
        # Clean up any existing node_modules to avoid path issues
        if (Test-Path "node_modules") {
            Write-Host "Removing existing node_modules to avoid path issues..." -ForegroundColor Gray
            Remove-Item "node_modules" -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        # Also remove dist if it exists
        if (Test-Path "dist") {
            Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
        }

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
        $imageExists = az acr repository show --name $registryName --repository "frontend" 2>$null
        if (-not $imageExists) {
            throw "Image was not successfully pushed to registry"
        }
        
        Write-Host "✓ Image verified in registry" -ForegroundColor Green

        # Clean up temp files
        Remove-Item ".env.production" -Force -ErrorAction SilentlyContinue
        
    } finally {
        Pop-Location
    }
    Write-Host "✓ Container image built and pushed" -ForegroundColor Green

    # Create App Service Plan
    Write-Host "Creating App Service Plan..." -ForegroundColor Blue
    $planExists = az appservice plan show --name $planName --resource-group $ResourceGroupName 2>$null
    if (-not $planExists) {
        az appservice plan create `
            --name $planName `
            --resource-group $ResourceGroupName `
            --location $Location `
            --sku B1 `
            --is-linux `
            --only-show-errors
        Write-Host "✓ App Service Plan created" -ForegroundColor Green
    } else {
        Write-Host "✓ App Service Plan already exists" -ForegroundColor Green
    }

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
    
    # Wait a moment for registry to be fully ready
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
        WEBSITES_PORT="80" `
        --only-show-errors
    Write-Host "✓ App settings configured" -ForegroundColor Green

    $frontendUrl = "https://$webAppName.azurewebsites.net"
    
    Write-Host "" -ForegroundColor Green
    Write-Host "✅ SUCCESS! Frontend deployed successfully!" -ForegroundColor Green
    Write-Host "🌐 URL: $frontendUrl" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Wait 3-5 minutes for container to start" -ForegroundColor White
    Write-Host "2. Visit the URL above to test your app" -ForegroundColor White
    Write-Host "3. Check container logs if needed: az webapp log tail --name $webAppName --resource-group $ResourceGroupName" -ForegroundColor White

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "For troubleshooting, check:" -ForegroundColor Yellow
    Write-Host "- Azure portal for detailed error messages" -ForegroundColor White
    Write-Host "- Container logs: az webapp log tail --name $webAppName --resource-group $ResourceGroupName" -ForegroundColor White
    exit 1
}
