param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$BackendUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd"
$storageAccountName = "frontend$timestamp"

Write-Host "🚀 Deploying React Frontend as Static Website" -ForegroundColor Green
Write-Host "Storage Account: $storageAccountName" -ForegroundColor Yellow
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Yellow

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

    # Check if Node.js is available
    $nodeCheck = node --version 2>$null
    if (-not $nodeCheck) {
        throw "Node.js not found. Please install Node.js first."
    }
    Write-Host "✓ Node.js found: $nodeCheck" -ForegroundColor Green

    # Build the React app locally
    Write-Host "Building React app locally..." -ForegroundColor Blue
    Push-Location $frontendDir
    try {
        # Create production environment file
        $envContent = @"
VITE_API_BASE_URL=$BackendUrl
NODE_ENV=production
"@
        $envContent | Out-File -FilePath ".env.production" -Encoding UTF8

        # Install dependencies if needed
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing dependencies..." -ForegroundColor Blue
            npm install
        }

        # Build the app
        Write-Host "Running build..." -ForegroundColor Blue
        npm run build

        if (-not (Test-Path "dist")) {
            throw "Build failed - dist folder not created"
        }

        Write-Host "✓ React app built successfully" -ForegroundColor Green

    } finally {
        Remove-Item ".env.production" -Force -ErrorAction SilentlyContinue
        Pop-Location
    }

    # Create storage account
    Write-Host "Creating storage account..." -ForegroundColor Blue
    az storage account create `
        --name $storageAccountName `
        --resource-group $ResourceGroupName `
        --location $Location `
        --sku Standard_LRS `
        --kind StorageV2 `
        --access-tier Hot `
        --allow-blob-public-access true `
        --only-show-errors
    Write-Host "✓ Storage account created" -ForegroundColor Green

    # Enable static website hosting
    Write-Host "Enabling static website hosting..." -ForegroundColor Blue
    az storage blob service-properties update `
        --account-name $storageAccountName `
        --auth-mode login `
        --static-website true `
        --index-document index.html `
        --404-document index.html `
        --only-show-errors
    Write-Host "✓ Static website hosting enabled" -ForegroundColor Green

    # Upload built files
    Write-Host "Uploading built files..." -ForegroundColor Blue
    $distPath = Join-Path $frontendDir "dist"
    az storage blob upload-batch `
        --account-name $storageAccountName `
        --auth-mode login `
        --destination '$web' `
        --source $distPath `
        --overwrite `
        --only-show-errors
    Write-Host "✓ Files uploaded successfully" -ForegroundColor Green

    # Get the static website URL
    $frontendUrl = "https://$storageAccountName.z22.web.core.windows.net"
    
    Write-Host "" -ForegroundColor Green
    Write-Host "✅ SUCCESS! Frontend deployed successfully!" -ForegroundColor Green
    Write-Host "🌐 URL: $frontendUrl" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Visit the URL above to test your app" -ForegroundColor White
    Write-Host "2. If you need CORS, configure it on your backend for domain: $frontendUrl" -ForegroundColor White
    Write-Host "3. To update: re-run this script after making changes" -ForegroundColor White

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

