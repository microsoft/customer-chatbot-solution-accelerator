param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$BackendAppName = "ecommerce-backend-202509181049"
)

Write-Host "🔧 Fixing Backend Startup Configuration" -ForegroundColor Blue

# Set the correct startup command
Write-Host "Setting startup command..." -ForegroundColor Yellow
az webapp config set `
    --name $BackendAppName `
    --resource-group $ResourceGroupName `
    --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" `
    --only-show-errors

# Also ensure the Python version is set correctly
Write-Host "Ensuring Python runtime is set..." -ForegroundColor Yellow
az webapp config appsettings set `
    --name $BackendAppName `
    --resource-group $ResourceGroupName `
    --settings `
    WEBSITES_PORT="8000" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="1" `
    ENABLE_ORYX_BUILD="true" `
    --only-show-errors

# Restart the app service
Write-Host "Restarting backend app service..." -ForegroundColor Yellow
az webapp restart `
    --name $BackendAppName `
    --resource-group $ResourceGroupName `
    --only-show-errors

Write-Host "✅ Backend startup configuration updated!" -ForegroundColor Green
Write-Host "🔍 Wait 2-3 minutes, then test:" -ForegroundColor Yellow
Write-Host "   https://$BackendAppName.azurewebsites.net/docs" -ForegroundColor Cyan
Write-Host "   https://$BackendAppName.azurewebsites.net/health" -ForegroundColor Cyan
