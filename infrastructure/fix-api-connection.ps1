param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$FrontendAppName,
    [string]$BackendUrl
)

$ErrorActionPreference = "Stop"

if (-not $FrontendAppName) {
    # Find the most recent frontend app
    $frontendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'frontend')].name" -o tsv
    if ($frontendApps) {
        $FrontendAppName = ($frontendApps -split "`n")[-1]
        Write-Host "✅ Found frontend app: $FrontendAppName" -ForegroundColor Green
    } else {
        throw "No frontend app found. Please specify -FrontendAppName"
    }
}

if (-not $BackendUrl) {
    # Find the most recent backend app
    $backendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'backend')].name" -o tsv
    if ($backendApps) {
        $backendName = ($backendApps -split "`n")[-1]
        $BackendUrl = "https://$backendName.azurewebsites.net"
        Write-Host "✅ Found backend app: $backendName" -ForegroundColor Green
    } else {
        throw "No backend app found. Please specify -BackendUrl"
    }
}

Write-Host "🔧 Fixing API Connection Issues" -ForegroundColor Green
Write-Host "Frontend App: $FrontendAppName" -ForegroundColor Cyan
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Cyan

try {
    # Get paths
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    $frontendDir = Join-Path $projectRoot "modern-e-commerce-ch"
    
    # Get registry info from existing frontend app
    $containerConfig = az webapp config container show --name $FrontendAppName --resource-group $ResourceGroupName | ConvertFrom-Json
    $currentImage = $containerConfig.linuxFxVersion -replace "DOCKER\|", ""
    $registryUrl = ($currentImage -split "/")[0]
    $registryName = $registryUrl -replace "\.azurecr\.io", ""
    
    Write-Host "Using registry: $registryName" -ForegroundColor Gray
    
    # Build updated frontend with API fixes
    Push-Location $frontendDir
    try {
        # Create runtime configuration with correct backend URL
        $configContent = @"
// Runtime configuration
window.APP_CONFIG = {
  API_BASE_URL: '$BackendUrl',
  ENVIRONMENT: 'production'
};
"@
        $configContent | Out-File -FilePath "public/config.js" -Encoding UTF8
        Write-Host "✅ Updated runtime config with backend URL" -ForegroundColor Green
        
        # Create build environment
        $envContent = @"
VITE_API_BASE_URL=$BackendUrl
NODE_ENV=production
"@
        $envContent | Out-File -FilePath ".env.production" -Encoding UTF8
        
        # Clean existing builds
        if (Test-Path "node_modules") { Remove-Item "node_modules" -Recurse -Force -ErrorAction SilentlyContinue }
        if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue }
        
        # Build new image with API fixes
        $timestamp = Get-Date -Format "yyyyMMddHHmmss"
        $newImageTag = "frontend:api-fix-$timestamp"
        
        Write-Host "Building updated image with API fixes: $newImageTag" -ForegroundColor Yellow
        
        $env:PYTHONIOENCODING = "utf-8"
        $env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"
        
        az acr build `
            --registry $registryName `
            --image $newImageTag `
            --file "Dockerfile" `
            . `
            --no-logs
            
        if ($LASTEXITCODE -ne 0) {
            throw "Container build failed"
        }
        
        Write-Host "✅ New image built successfully with API fixes" -ForegroundColor Green
        
        # Clean up
        Remove-Item ".env.production" -Force -ErrorAction SilentlyContinue
        
    } finally {
        Pop-Location
    }
    
    # Get ACR credentials
    $acrCredentials = az acr credential show --name $registryName | ConvertFrom-Json
    
    # Update frontend app to use new image
    $newFullImage = "$registryName.azurecr.io/$newImageTag"
    Write-Host "Updating frontend to use: $newFullImage" -ForegroundColor Yellow
    
    az webapp config container set `
        --name $FrontendAppName `
        --resource-group $ResourceGroupName `
        --docker-custom-image-name $newFullImage `
        --docker-registry-server-url "https://$registryName.azurecr.io" `
        --docker-registry-server-user $acrCredentials.username `
        --docker-registry-server-password $acrCredentials.passwords[0].value `
        --output none
        
    Write-Host "✅ Frontend updated successfully with API fixes" -ForegroundColor Green
    
    $frontendUrl = "https://$FrontendAppName.azurewebsites.net"
    
    Write-Host ""
    Write-Host "🎉 SUCCESS! API Connection Fixed!" -ForegroundColor Green
    Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan
    Write-Host "Backend URL: $BackendUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔧 What was fixed:" -ForegroundColor Yellow
    Write-Host "✅ Enhanced URL validation and HTTPS enforcement" -ForegroundColor White
    Write-Host "✅ Better error handling and logging" -ForegroundColor White
    Write-Host "✅ Improved mixed content error handling" -ForegroundColor White
    Write-Host "✅ More robust API connection logic" -ForegroundColor White
    Write-Host ""
    Write-Host "⏰ Wait 2-3 minutes for the container to restart, then:" -ForegroundColor Yellow
    Write-Host "1. Visit $frontendUrl" -ForegroundColor White
    Write-Host "2. Open browser console and check for detailed API logs" -ForegroundColor White
    Write-Host "3. Verify products are loaded from the API (not mock data)" -ForegroundColor White
    Write-Host "4. Check Network tab for successful API calls to $BackendUrl" -ForegroundColor White
    
} catch {
    Write-Host "❌ Fix failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
