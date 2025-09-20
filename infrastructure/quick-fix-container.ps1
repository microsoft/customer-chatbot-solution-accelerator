param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$WebAppName = "ecommerce-frontend-20250916"
)

Write-Host "🔧 Quick Container Fixes" -ForegroundColor Blue
Write-Host "========================" -ForegroundColor Blue

# 1. Restart the web app
Write-Host "`n1. Restarting web app..." -ForegroundColor Yellow
az webapp restart --name $WebAppName --resource-group $ResourceGroupName --only-show-errors
Write-Host "✓ Web app restarted" -ForegroundColor Green

# 2. Update container settings to ensure proper configuration
Write-Host "`n2. Updating container settings..." -ForegroundColor Yellow
az webapp config appsettings set `
    --name $WebAppName `
    --resource-group $ResourceGroupName `
    --settings `
    WEBSITES_ENABLE_APP_SERVICE_STORAGE="false" `
    WEBSITES_PORT="80" `
    WEBSITES_CONTAINER_START_TIME_LIMIT="1800" `
    --only-show-errors
Write-Host "✓ Container settings updated" -ForegroundColor Green

# 3. Wait a moment and test
Write-Host "`n3. Waiting 30 seconds for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 4. Test connectivity
$webApp = az webapp show --name $WebAppName --resource-group $ResourceGroupName | ConvertFrom-Json
$url = "https://$($webApp.defaultHostName)"

Write-Host "`n4. Testing connectivity..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 15 -ErrorAction Stop
    Write-Host "✅ SUCCESS! HTTP Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "🌐 Your app should be working at: $url" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Still not working: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n🔍 Next steps:" -ForegroundColor Yellow
    Write-Host "• Run ./debug-frontend.ps1 for detailed diagnostics" -ForegroundColor White
    Write-Host "• The container might need more time to start" -ForegroundColor White
    Write-Host "• Check if the Docker image built correctly" -ForegroundColor White
}

