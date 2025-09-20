param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$WebAppName = "ecommerce-frontend-20250916"
)

Write-Host "🔍 Finding the correct container image..." -ForegroundColor Blue

# Check all registries for the frontend image
$registries = @("ecreg202509161539", "ecreg202509161554", "ecreg202509161556")

foreach ($registry in $registries) {
    Write-Host "Checking registry: $registry" -ForegroundColor Yellow
    try {
        $images = az acr repository list --name $registry --output tsv 2>$null
        if ($images -contains "frontend") {
            Write-Host "✓ Found 'frontend' repository in $registry" -ForegroundColor Green
            
            # Get image tags
            $tags = az acr repository show-tags --name $registry --repository frontend --output tsv 2>$null
            Write-Host "  Available tags: $($tags -join ', ')" -ForegroundColor Cyan
            
            if ($tags -contains "latest") {
                Write-Host "✅ Found frontend:latest in $registry" -ForegroundColor Green
                
                # This is our registry - configure the web app
                $fullImageName = "$registry.azurecr.io/frontend:latest"
                Write-Host "Configuring web app with: $fullImageName" -ForegroundColor Blue
                
                # Get fresh credentials
                $acrCredentials = az acr credential show --name $registry | ConvertFrom-Json
                
                # Reconfigure container
                az webapp config container set `
                    --name $WebAppName `
                    --resource-group $ResourceGroupName `
                    --docker-custom-image-name $fullImageName `
                    --docker-registry-server-url "https://$registry.azurecr.io" `
                    --docker-registry-server-user $acrCredentials.username `
                    --docker-registry-server-password $acrCredentials.passwords[0].value `
                    --only-show-errors
                
                Write-Host "✅ Web app reconfigured with correct image!" -ForegroundColor Green
                Write-Host "Wait 2-3 minutes and test: https://$WebAppName.azurewebsites.net" -ForegroundColor Cyan
                return
            }
        }
    } catch {
        Write-Host "  Registry $registry not accessible or empty" -ForegroundColor Gray
    }
}

Write-Host "❌ No frontend:latest image found in any registry!" -ForegroundColor Red
Write-Host "You need to rebuild and push the container image." -ForegroundColor Yellow

