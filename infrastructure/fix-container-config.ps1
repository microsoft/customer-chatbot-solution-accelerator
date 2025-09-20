param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$WebAppName = "ecommerce-frontend-20250916"
)

Write-Host "🔧 Fixing Container Configuration" -ForegroundColor Blue

# Use the most recent registry
$registryName = "ecreg202509161556"
$fullImageName = "$registryName.azurecr.io/frontend:latest"

Write-Host "Using registry: $registryName" -ForegroundColor Yellow
Write-Host "Image: $fullImageName" -ForegroundColor Yellow

# Get ACR credentials
Write-Host "Getting registry credentials..." -ForegroundColor Blue
$acrCredentials = az acr credential show --name $registryName | ConvertFrom-Json

# Reconfigure the container
Write-Host "Reconfiguring container..." -ForegroundColor Blue
az webapp config container set `
    --name $WebAppName `
    --resource-group $ResourceGroupName `
    --docker-custom-image-name $fullImageName `
    --docker-registry-server-url "https://$registryName.azurecr.io" `
    --docker-registry-server-user $acrCredentials.username `
    --docker-registry-server-password $acrCredentials.passwords[0].value `
    --only-show-errors

# Set proper app settings
Write-Host "Setting app settings..." -ForegroundColor Blue
az webapp config appsettings set `
    --name $WebAppName `
    --resource-group $ResourceGroupName `
    --settings `
    WEBSITES_ENABLE_APP_SERVICE_STORAGE="false" `
    WEBSITES_PORT="80" `
    WEBSITES_CONTAINER_START_TIME_LIMIT="1800" `
    --only-show-errors

Write-Host "✅ Configuration fixed! Wait 2-3 minutes then test:" -ForegroundColor Green
Write-Host "🌐 https://ecommerce-frontend-20250916.azurewebsites.net" -ForegroundColor Cyan

