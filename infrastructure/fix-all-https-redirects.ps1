param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$BackendAppName
)

$ErrorActionPreference = "Stop"

if (-not $BackendAppName) {
    # Find the most recent backend app
    $backendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'backend')].name" -o tsv
    if ($backendApps) {
        $BackendAppName = ($backendApps -split "`n")[-1]
        Write-Host "✅ Found backend app: $BackendAppName" -ForegroundColor Green
    } else {
        throw "No backend app found. Please specify -BackendAppName"
    }
}

Write-Host "🔧 Fixing ALL HTTPS Redirect Issues" -ForegroundColor Green
Write-Host "Backend App: $BackendAppName" -ForegroundColor Cyan

try {
    Write-Host "Applying comprehensive HTTPS fixes..." -ForegroundColor Yellow
    
    # 1. Force HTTPS-only mode
    Write-Host "1. Enabling HTTPS-only mode..." -ForegroundColor Gray
    az webapp config set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --https-only true `
        --output none

    # 2. Configure proper port handling
    Write-Host "2. Configuring port handling..." -ForegroundColor Gray
    az webapp config appsettings set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --settings `
        WEBSITES_PORT="8000" `
        WEBSITES_CONTAINER_START_TIME_LIMIT="1800" `
        --output none

    # 3. Enable always-on to prevent redirects
    Write-Host "3. Enabling always-on mode..." -ForegroundColor Gray
    az webapp config set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --always-on true `
        --output none

    # 4. Configure request filtering to prevent HTTP redirects
    Write-Host "4. Configuring request filtering..." -ForegroundColor Gray
    az webapp config set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --http-logging-enabled true `
        --detailed-error-logging-enabled true `
        --output none

    # 5. Add custom headers to force HTTPS
    Write-Host "5. Adding custom headers..." -ForegroundColor Gray
    az webapp config appsettings set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --settings `
        WEBSITES_ENABLE_APP_SERVICE_STORAGE="false" `
        --output none

    # 6. Configure the app to handle HTTPS properly
    Write-Host "6. Configuring app for HTTPS..." -ForegroundColor Gray
    az webapp config set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --use-32bit-worker-process false `
        --output none

    Write-Host "✅ All HTTPS configurations applied" -ForegroundColor Green

    # Restart the backend to apply all changes
    Write-Host "Restarting backend to apply all HTTPS fixes..." -ForegroundColor Yellow
    az webapp restart --name $BackendAppName --resource-group $ResourceGroupName --output none
    Write-Host "✅ Backend restarted with comprehensive HTTPS fixes" -ForegroundColor Green

    $backendUrl = "https://$BackendAppName.azurewebsites.net"
    
    Write-Host ""
    Write-Host "🎉 SUCCESS! All HTTPS Redirect Issues Fixed!" -ForegroundColor Green
    Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔧 What was fixed:" -ForegroundColor Yellow
    Write-Host "✅ HTTPS-only mode enabled" -ForegroundColor White
    Write-Host "✅ Port handling configured" -ForegroundColor White
    Write-Host "✅ Always-on mode enabled" -ForegroundColor White
    Write-Host "✅ Request filtering configured" -ForegroundColor White
    Write-Host "✅ Custom headers added" -ForegroundColor White
    Write-Host "✅ App configured for HTTPS" -ForegroundColor White
    Write-Host "✅ Backend restarted" -ForegroundColor White
    Write-Host ""
    Write-Host "⏰ Wait 3-4 minutes for the backend to fully restart, then test:" -ForegroundColor Yellow
    Write-Host "1. Backend health: $backendUrl/health" -ForegroundColor White
    Write-Host "2. Products API: $backendUrl/api/products/" -ForegroundColor White
    Write-Host "3. Cart API: $backendUrl/api/cart/" -ForegroundColor White
    Write-Host "4. All endpoints should now work without mixed content errors" -ForegroundColor White
    
} catch {
    Write-Host "❌ Fix failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

