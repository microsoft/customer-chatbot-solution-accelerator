param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$WebAppName = "ecommerce-frontend-20250916"
)

Write-Host "🔍 Frontend Debugging Report" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue

# 1. Check if web app exists and its status
Write-Host "`n1. Web App Status:" -ForegroundColor Yellow
try {
    $webApp = az webapp show --name $WebAppName --resource-group $ResourceGroupName | ConvertFrom-Json
    Write-Host "✓ App exists: $($webApp.name)" -ForegroundColor Green
    Write-Host "✓ State: $($webApp.state)" -ForegroundColor Green
    Write-Host "✓ URL: https://$($webApp.defaultHostName)" -ForegroundColor Cyan
    Write-Host "✓ Container Image: $($webApp.siteConfig.linuxFxVersion)" -ForegroundColor Green
} catch {
    Write-Host "❌ Web app not found or error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Check container configuration
Write-Host "`n2. Container Configuration:" -ForegroundColor Yellow
$containerConfig = az webapp config container show --name $WebAppName --resource-group $ResourceGroupName | ConvertFrom-Json
Write-Host "✓ Registry URL: $($containerConfig.dockerRegistryServerUrl)" -ForegroundColor Green
Write-Host "✓ Image: $($containerConfig.dockerCustomImageName)" -ForegroundColor Green

# 3. Get recent log entries (limited to avoid hanging)
Write-Host "`n3. Recent Log Entries (last 50 lines):" -ForegroundColor Yellow
try {
    $logs = az webapp log download --name $WebAppName --resource-group $ResourceGroupName --log-file "temp-logs.zip" 2>$null
    if (Test-Path "temp-logs.zip") {
        Write-Host "✓ Logs downloaded to temp-logs.zip" -ForegroundColor Green
        Remove-Item "temp-logs.zip" -Force -ErrorAction SilentlyContinue
    }
} catch {
    Write-Host "⚠️ Could not download logs" -ForegroundColor Yellow
}

# 4. Check app settings
Write-Host "`n4. App Settings:" -ForegroundColor Yellow
$settings = az webapp config appsettings list --name $WebAppName --resource-group $ResourceGroupName | ConvertFrom-Json
foreach ($setting in $settings) {
    if ($setting.name -like "VITE_*" -or $setting.name -like "NODE_*" -or $setting.name -like "WEBSITES_*") {
        Write-Host "✓ $($setting.name): $($setting.value)" -ForegroundColor Green
    }
}

# 5. Quick connectivity test
Write-Host "`n5. Connectivity Test:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://$($webApp.defaultHostName)" -Method Head -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✓ HTTP Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Message -match "503") {
        Write-Host "🔧 503 Error = Container not starting properly" -ForegroundColor Yellow
    }
}

# 6. Container restart suggestion
Write-Host "`n6. Quick Fixes to Try:" -ForegroundColor Yellow
Write-Host "• Restart container: az webapp restart --name $WebAppName --resource-group $ResourceGroupName" -ForegroundColor White
Write-Host "• Check if port 80 is exposed in container" -ForegroundColor White
Write-Host "• Verify nginx is starting correctly" -ForegroundColor White

Write-Host "`n✅ Debug report complete!" -ForegroundColor Green

