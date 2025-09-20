param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$BackendUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd"
$webAppName = "ecommerce-frontend-$timestamp"
$planName = "frontend-plan"

Write-Host "🚀 Deploying React Frontend to Azure App Service" -ForegroundColor Green
Write-Host "Web App: $webAppName" -ForegroundColor Yellow
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

    Write-Host "Creating Web App..." -ForegroundColor Blue
    az webapp create `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --plan $planName `
        --runtime "NODE:18-lts" `
        --only-show-errors
    Write-Host "✓ Web App created" -ForegroundColor Green

    Write-Host "Configuring environment variables..." -ForegroundColor Blue
    az webapp config appsettings set `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --settings `
        VITE_API_BASE_URL=$BackendUrl `
        NODE_ENV="production" `
        SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
        --only-show-errors
    Write-Host "✓ Environment variables configured" -ForegroundColor Green

    Write-Host "Building and deploying application..." -ForegroundColor Blue
    
    # Get the correct paths
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    $frontendDir = Join-Path $projectRoot "modern-e-commerce-ch"
    $zipPath = Join-Path $scriptDir "frontend-deploy.zip"
    
    Write-Host "Script directory: $scriptDir" -ForegroundColor Gray
    Write-Host "Frontend directory: $frontendDir" -ForegroundColor Gray
    
    if (-not (Test-Path $frontendDir)) {
        throw "Frontend directory not found: $frontendDir"
    }
    
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    # Create zip excluding unnecessary folders
    Push-Location $frontendDir
    try {
        $filesToZip = Get-ChildItem -Path "." | Where-Object { 
            $_.Name -notin @("node_modules", "dist", ".git", ".github") 
        }
        Compress-Archive -Path $filesToZip -DestinationPath $zipPath -Force
    } finally {
        Pop-Location
    }

    Write-Host "Uploading application files..." -ForegroundColor Blue
    az webapp deployment source config-zip `
        --name $webAppName `
        --resource-group $ResourceGroupName `
        --src $zipPath `
        --only-show-errors
    Write-Host "✓ Application files uploaded" -ForegroundColor Green

    $frontendUrl = "https://$webAppName.azurewebsites.net"
    
    Write-Host "" -ForegroundColor Green
    Write-Host "✅ SUCCESS! Frontend deployed successfully!" -ForegroundColor Green
    Write-Host "🌐 URL: $frontendUrl" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Wait 2-3 minutes for deployment to complete" -ForegroundColor White
    Write-Host "2. Visit the URL above to test your app" -ForegroundColor White
    Write-Host "3. Deploy your backend and update VITE_API_BASE_URL" -ForegroundColor White

    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
