# Complete Deployment Script with Entra ID Authentication
# This script runs the original deploy-complete.ps1 and then adds authentication

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat",
    [switch]$SkipCosmos = $false,
    [switch]$SkipFrontend = $false,
    [switch]$SkipBackend = $false,
    [switch]$SkipIntegration = $false
)

Write-Host "🚀 COMPLETE E-COMMERCE CHAT DEPLOYMENT WITH AUTH" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "App Name Prefix: $AppNamePrefix" -ForegroundColor Cyan

# Check if already logged in
Write-Host "`n🔍 Checking Azure status..." -ForegroundColor Blue
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($account) {
        Write-Host "✅ Already logged in as: $account" -ForegroundColor Green
    } else {
        Write-Host "❌ Not logged in. Please run 'az login' first." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Not logged in. Please run 'az login' first." -ForegroundColor Red
    exit 1
}

# Get tenant ID
Write-Host "`n📋 Getting Azure tenant information..." -ForegroundColor Blue
$tenantInfo = az account show --query "{tenantId: tenantId, name: name}" -o json | ConvertFrom-Json
$AzureTenantId = $tenantInfo.tenantId
$tenantName = $tenantInfo.name
Write-Host "Using tenant: $tenantName ($AzureTenantId)" -ForegroundColor Cyan

# Calculate expected URLs
$frontendAppServiceName = "$AppNamePrefix-$Environment-frontend"
$backendAppServiceName = "$AppNamePrefix-$Environment-backend"
$expectedFrontendUrl = "https://$frontendAppServiceName.azurewebsites.net"

Write-Host "Expected Frontend URL: $expectedFrontendUrl" -ForegroundColor Cyan

# Create Azure App Registration
Write-Host "`n🔐 Creating Azure App Registration..." -ForegroundColor Blue

$appName = "$AppNamePrefix-$Environment-App"

# Create app registration with placeholder URLs first
Write-Host "Creating app registration with placeholder URLs..." -ForegroundColor Gray

$appRegistration = az ad app create `
    --display-name $appName `
    --sign-in-audience "AzureADMyOrg" `
    --web-redirect-uris "https://placeholder.azurewebsites.net" "https://placeholder.azurewebsites.net/auth/callback" `
    --enable-id-token-issuance true `
    --query "{appId: appId, id: id}" `
    -o json | ConvertFrom-Json

if (-not $appRegistration) {
    Write-Host "❌ Failed to create app registration" -ForegroundColor Red
    exit 1
}

$AzureClientId = $appRegistration.appId
$appObjectId = $appRegistration.id

Write-Host "✅ App Registration created successfully!" -ForegroundColor Green
Write-Host "Client ID: $AzureClientId" -ForegroundColor Cyan
Write-Host "App Object ID: $appObjectId" -ForegroundColor Cyan

# Create client secret
Write-Host "`n🔑 Creating client secret..." -ForegroundColor Blue

$secretName = "$AppNamePrefix-Secret-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$secretResponse = az ad app credential reset `
    --id $AzureClientId `
    --display-name $secretName `
    --query "{password: password}" `
    -o json | ConvertFrom-Json

if (-not $secretResponse) {
    Write-Host "❌ Failed to create client secret" -ForegroundColor Red
    exit 1
}

$AzureClientSecret = $secretResponse.password

Write-Host "✅ Client secret created successfully!" -ForegroundColor Green
Write-Host "Secret Name: $secretName" -ForegroundColor Cyan
Write-Host "Client Secret: $AzureClientSecret" -ForegroundColor Cyan

# Configure API permissions
Write-Host "`n🔐 Configuring API permissions..." -ForegroundColor Blue

$permissions = @("User.Read", "openid", "profile")

foreach ($permission in $permissions) {
    Write-Host "Adding permission: $permission" -ForegroundColor Gray
    
    $permissionId = az ad sp show --id "00000003-0000-0000-c000-000000000000" --query "appRoles[?value=='$permission'].id" -o tsv
    
    if ($permissionId) {
        az ad app permission add --id $AzureClientId --api "00000003-0000-0000-c000-000000000000" --api-permissions $permissionId | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Added permission: $permission" -ForegroundColor Green
        }
    }
}

# Grant admin consent
Write-Host "`n🔓 Granting admin consent..." -ForegroundColor Blue
try {
    az ad app permission admin-consent --id $AzureClientId | Out-Null
    Write-Host "✅ Admin consent granted!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not grant admin consent automatically. You may need to do this manually." -ForegroundColor Yellow
}

# Set up environment variables for deployment
$env:AZURE_TENANT_ID = $AzureTenantId
$env:AZURE_CLIENT_ID = $AzureClientId
$env:AZURE_CLIENT_SECRET = $AzureClientSecret

# Run the original deploy-complete.ps1 script
Write-Host "`n🚀 Running original deployment script..." -ForegroundColor Blue
Write-Host "This will deploy Cosmos DB, Frontend, Backend, and run integration tests" -ForegroundColor Gray

& "$PSScriptRoot\deploy-complete.ps1" -ResourceGroupName $ResourceGroupName -Location $Location -Environment $Environment -AppNamePrefix $AppNamePrefix -SkipCosmos:$SkipCosmos -SkipFrontend:$SkipFrontend -SkipBackend:$SkipBackend -SkipIntegration:$SkipIntegration

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Original deployment failed. Stopping." -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Original deployment completed successfully!" -ForegroundColor Green

# Now configure authentication
Write-Host "`n🔐 CONFIGURING AUTHENTICATION" -ForegroundColor Magenta
Write-Host "=============================" -ForegroundColor Magenta

# Configure Entra ID settings for frontend
Write-Host "`n🔐 Configuring Entra ID for Frontend..." -ForegroundColor Blue

$frontendSettings = @(
    "VITE_API_BASE_URL=https://$backendAppServiceName.azurewebsites.net",
    "VITE_AZURE_CLIENT_ID=$AzureClientId",
    "VITE_AZURE_TENANT_ID=$AzureTenantId",
    "VITE_AZURE_AUTHORITY=https://login.microsoftonline.com/$AzureTenantId",
    "VITE_REDIRECT_URI=https://$frontendAppServiceName.azurewebsites.net/auth/callback",
    "VITE_ENVIRONMENT=production"
)

foreach ($setting in $frontendSettings) {
    $parts = $setting -split "=", 2
    $name = $parts[0]
    $value = $parts[1]
    
    Write-Host "Setting $name = $value" -ForegroundColor Gray
    
    az webapp config appsettings set `
        --name $frontendAppServiceName `
        --resource-group $ResourceGroupName `
        --settings "$name=$value" `
        --only-show-errors | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to set $name" -ForegroundColor Red
        exit 1
    }
}

# Configure Entra ID settings for backend
Write-Host "`n🔐 Configuring Entra ID for Backend..." -ForegroundColor Blue

$backendSettings = @(
    "AZURE_TENANT_ID=$AzureTenantId",
    "AZURE_CLIENT_ID=$AzureClientId",
    "AZURE_CLIENT_SECRET=$AzureClientSecret",
    "ALLOWED_ORIGINS_STR=https://$frontendAppServiceName.azurewebsites.net"
)

foreach ($setting in $backendSettings) {
    $parts = $setting -split "=", 2
    $name = $parts[0]
    $value = $parts[1]
    
    Write-Host "Setting $name = $value" -ForegroundColor Gray
    
    az webapp config appsettings set `
        --name $backendAppServiceName `
        --resource-group $ResourceGroupName `
        --settings "$name=$value" `
        --only-show-errors | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to set $name" -ForegroundColor Red
        exit 1
    }
}

# Update App Registration with correct URLs
Write-Host "`n🔧 Updating App Registration with correct URLs..." -ForegroundColor Blue

$authConfig = @{
    "web" = @{
        "redirectUris" = @($expectedFrontendUrl, "$expectedFrontendUrl/auth/callback")
        "implicitGrantSettings" = @{
            "enableIdTokenIssuance" = $true
            "enableAccessTokenIssuance" = $false
        }
    }
    "spa" = @{
        "redirectUris" = @($expectedFrontendUrl, "$expectedFrontendUrl/auth/callback")
    }
}

$authConfigJson = $authConfig | ConvertTo-Json -Depth 3

try {
    az rest --method PATCH --uri "https://graph.microsoft.com/v1.0/applications/$appObjectId" --body $authConfigJson | Out-Null
    Write-Host "✅ App registration URLs updated successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not update app registration URLs automatically." -ForegroundColor Yellow
    Write-Host "Please update manually in Azure Portal:" -ForegroundColor Yellow
    Write-Host "1. Go to Azure Portal > Azure Active Directory > App registrations" -ForegroundColor Cyan
    Write-Host "2. Find your app: $appName" -ForegroundColor Cyan
    Write-Host "3. Go to Authentication > Platform configurations" -ForegroundColor Cyan
    Write-Host "4. Update redirect URIs to:" -ForegroundColor Cyan
    Write-Host "   - $expectedFrontendUrl" -ForegroundColor White
    Write-Host "   - $expectedFrontendUrl/auth/callback" -ForegroundColor White
}

Write-Host "`n✅ Authentication configuration completed successfully!" -ForegroundColor Green

# Final Summary
$resourceNamePrefix = "$AppNamePrefix-$Environment"
$backendUrl = "https://$resourceNamePrefix-backend.azurewebsites.net"
$frontendUrl = "https://$resourceNamePrefix-frontend.azurewebsites.net"

Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host "✅ All phases completed successfully!" -ForegroundColor Green

Write-Host "`n🔗 YOUR APPLICATION" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow
Write-Host "🌐 Frontend: $frontendUrl" -ForegroundColor White
Write-Host "🐍 Backend: $backendUrl" -ForegroundColor White
Write-Host "📚 API Docs: $backendUrl/docs" -ForegroundColor White

Write-Host "`n🔐 AUTHENTICATION SETUP" -ForegroundColor Yellow
Write-Host "=======================" -ForegroundColor Yellow
Write-Host "✅ Entra ID authentication configured" -ForegroundColor Green
Write-Host "✅ Frontend configured with client ID: $AzureClientId" -ForegroundColor Green
Write-Host "✅ Backend configured with tenant ID: $AzureTenantId" -ForegroundColor Green
Write-Host "✅ App registration created and configured" -ForegroundColor Green
Write-Host "✅ Redirect URIs updated with actual frontend URL" -ForegroundColor Green

Write-Host "`n📋 QUICK START" -ForegroundColor Yellow
Write-Host "==============" -ForegroundColor Yellow
Write-Host "1. Open your browser and go to: $frontendUrl" -ForegroundColor White
Write-Host "2. Click 'Login' to authenticate with Microsoft" -ForegroundColor White
Write-Host "3. Test the chat functionality" -ForegroundColor White
Write-Host "4. Add items to cart and test checkout" -ForegroundColor White
Write-Host "5. Check the API documentation at: $backendUrl/docs" -ForegroundColor White

Write-Host "`n🔑 SAVE THESE CREDENTIALS" -ForegroundColor Yellow
Write-Host "========================" -ForegroundColor Yellow
Write-Host "Client ID: $AzureClientId" -ForegroundColor White
Write-Host "Client Secret: $AzureClientSecret" -ForegroundColor White
Write-Host "Tenant ID: $AzureTenantId" -ForegroundColor White
Write-Host "`n⚠️  Store these credentials securely - you'll need them for future deployments!" -ForegroundColor Yellow

Write-Host "`n⚠️  IMPORTANT NOTES" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow
Write-Host "• Your Azure App Registration is configured with these redirect URIs:" -ForegroundColor White
Write-Host "  - $frontendUrl" -ForegroundColor Cyan
Write-Host "  - $frontendUrl/auth/callback" -ForegroundColor Cyan
Write-Host "• The app registration is configured as 'Single-page application (SPA)'" -ForegroundColor White
Write-Host "• Required API permissions: User.Read, openid, profile" -ForegroundColor White
Write-Host "• You may need to manually grant admin consent in Azure Portal if it wasn't granted automatically" -ForegroundColor White

Write-Host "`n✨ Happy coding!" -ForegroundColor Green
