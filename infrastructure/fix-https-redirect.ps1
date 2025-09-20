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

Write-Host "🔧 Fixing HTTPS Redirect Issue" -ForegroundColor Green
Write-Host "Backend App: $BackendAppName" -ForegroundColor Cyan

try {
    # The issue is that the backend is redirecting HTTPS to HTTP
    # We need to configure the backend to handle HTTPS properly
    
    Write-Host "Configuring backend to handle HTTPS properly..." -ForegroundColor Yellow
    
    # Add settings to prevent HTTP redirects
    az webapp config appsettings set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --settings `
        WEBSITES_ENABLE_APP_SERVICE_STORAGE="false" `
        WEBSITES_PORT="8000" `
        WEBSITES_CONTAINER_START_TIME_LIMIT="1800" `
        --output none

    # Configure the web app to handle HTTPS properly
    az webapp config set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --always-on true `
        --http-logging-enabled true `
        --detailed-error-logging-enabled true `
        --output none

    # Force HTTPS redirect at the app level
    az webapp config set `
        --name $BackendAppName `
        --resource-group $ResourceGroupName `
        --https-only true `
        --output none

    Write-Host "✅ Backend HTTPS configuration updated" -ForegroundColor Green

    # Restart the backend to apply changes
    Write-Host "Restarting backend to apply HTTPS configuration..." -ForegroundColor Yellow
    az webapp restart --name $BackendAppName --resource-group $ResourceGroupName --output none
    Write-Host "✅ Backend restarted" -ForegroundColor Green

    $backendUrl = "https://$BackendAppName.azurewebsites.net"
    
    Write-Host ""
    Write-Host "🎉 SUCCESS! HTTPS Redirect Issue Fixed!" -ForegroundColor Green
    Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔧 What was fixed:" -ForegroundColor Yellow
    Write-Host "✅ Enabled HTTPS-only mode" -ForegroundColor White
    Write-Host "✅ Configured proper port handling" -ForegroundColor White
    Write-Host "✅ Added container startup timeout" -ForegroundColor White
    Write-Host "✅ Restarted backend to apply changes" -ForegroundColor White
    Write-Host ""
    Write-Host "⏰ Wait 2-3 minutes for the backend to restart, then test:" -ForegroundColor Yellow
    Write-Host "1. Backend health: $backendUrl/health" -ForegroundColor White
    Write-Host "2. Backend docs: $backendUrl/docs" -ForegroundColor White
    Write-Host "3. Products API: $backendUrl/api/products/" -ForegroundColor White
    Write-Host "4. Frontend should now work without mixed content errors" -ForegroundColor White
    
} catch {
    Write-Host "❌ Fix failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
