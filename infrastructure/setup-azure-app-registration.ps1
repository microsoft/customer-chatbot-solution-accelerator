# Azure App Registration Setup Script
# This script helps you create and configure an Azure App Registration for Entra ID authentication

param(
    [string]$AppName = "E-commerce Chat App",
    [string]$FrontendUrl = "https://your-frontend-app.azurewebsites.net",
    [string]$Environment = "production"
)

Write-Host "🔐 AZURE APP REGISTRATION SETUP" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host "App Name: $AppName" -ForegroundColor Cyan
Write-Host "Frontend URL: $FrontendUrl" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan

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
$tenantId = $tenantInfo.tenantId
$tenantName = $tenantInfo.name

Write-Host "Tenant: $tenantName" -ForegroundColor Cyan
Write-Host "Tenant ID: $tenantId" -ForegroundColor Cyan

# Create App Registration
Write-Host "`n🏗️ Creating Azure App Registration..." -ForegroundColor Blue

$appRegistration = az ad app create `
    --display-name $AppName `
    --sign-in-audience "AzureADMyOrg" `
    --web-redirect-uris "$FrontendUrl" "$FrontendUrl/auth/callback" `
    --enable-id-token-issuance true `
    --query "{appId: appId, id: id}" `
    -o json | ConvertFrom-Json

if (-not $appRegistration) {
    Write-Host "❌ Failed to create app registration" -ForegroundColor Red
    exit 1
}

$clientId = $appRegistration.appId
$appObjectId = $appRegistration.id

Write-Host "✅ App Registration created successfully!" -ForegroundColor Green
Write-Host "Client ID: $clientId" -ForegroundColor Cyan
Write-Host "App Object ID: $appObjectId" -ForegroundColor Cyan

# Create client secret
Write-Host "`n🔑 Creating client secret..." -ForegroundColor Blue

$secretName = "E-commerce-Chat-Secret-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$secretResponse = az ad app credential reset `
    --id $clientId `
    --display-name $secretName `
    --query "{password: password}" `
    -o json | ConvertFrom-Json

if (-not $secretResponse) {
    Write-Host "❌ Failed to create client secret" -ForegroundColor Red
    exit 1
}

$clientSecret = $secretResponse.password

Write-Host "✅ Client secret created successfully!" -ForegroundColor Green
Write-Host "Secret Name: $secretName" -ForegroundColor Cyan
Write-Host "Client Secret: $clientSecret" -ForegroundColor Cyan

# Configure API permissions
Write-Host "`n🔐 Configuring API permissions..." -ForegroundColor Blue

# Add Microsoft Graph permissions
$permissions = @(
    "User.Read",
    "openid", 
    "profile"
)

foreach ($permission in $permissions) {
    Write-Host "Adding permission: $permission" -ForegroundColor Gray
    
    # Get the permission ID
    $permissionId = az ad sp show --id "00000003-0000-0000-c000-000000000000" --query "appRoles[?value=='$permission'].id" -o tsv
    
    if ($permissionId) {
        # Add the permission
        az ad app permission add --id $clientId --api "00000003-0000-0000-c000-000000000000" --api-permissions $permissionId | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Added permission: $permission" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Permission $permission may already exist" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Could not find permission ID for: $permission" -ForegroundColor Yellow
    }
}

# Grant admin consent for the permissions
Write-Host "`n🔓 Granting admin consent for permissions..." -ForegroundColor Blue

try {
    az ad app permission admin-consent --id $clientId | Out-Null
    Write-Host "✅ Admin consent granted successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not grant admin consent automatically. You may need to do this manually in the Azure Portal." -ForegroundColor Yellow
}

# Configure authentication
Write-Host "`n🔧 Configuring authentication settings..." -ForegroundColor Blue

# Update the app registration to ensure it's configured as SPA
$authConfig = @{
    "web" = @{
        "redirectUris" = @("$FrontendUrl", "$FrontendUrl/auth/callback")
        "implicitGrantSettings" = @{
            "enableIdTokenIssuance" = $true
            "enableAccessTokenIssuance" = $false
        }
    }
    "spa" = @{
        "redirectUris" = @("$FrontendUrl", "$FrontendUrl/auth/callback")
    }
}

$authConfigJson = $authConfig | ConvertTo-Json -Depth 3

try {
    az rest --method PATCH --uri "https://graph.microsoft.com/v1.0/applications/$appObjectId" --body $authConfigJson | Out-Null
    Write-Host "✅ Authentication settings configured successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not update authentication settings automatically. You may need to configure this manually in the Azure Portal." -ForegroundColor Yellow
}

# Display summary
Write-Host "`n🎉 APP REGISTRATION SETUP COMPLETE!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

Write-Host "`n📋 CONFIGURATION SUMMARY" -ForegroundColor Yellow
Write-Host "========================" -ForegroundColor Yellow
Write-Host "App Name: $AppName" -ForegroundColor White
Write-Host "Client ID: $clientId" -ForegroundColor White
Write-Host "Client Secret: $clientSecret" -ForegroundColor White
Write-Host "Tenant ID: $tenantId" -ForegroundColor White
Write-Host "Frontend URL: $FrontendUrl" -ForegroundColor White
Write-Host "Redirect URIs:" -ForegroundColor White
Write-Host "  - $FrontendUrl" -ForegroundColor Cyan
Write-Host "  - $FrontendUrl/auth/callback" -ForegroundColor Cyan

Write-Host "`n🚀 NEXT STEPS" -ForegroundColor Yellow
Write-Host "=============" -ForegroundColor Yellow
Write-Host "1. Save these credentials securely:" -ForegroundColor White
Write-Host "   - Client ID: $clientId" -ForegroundColor Cyan
Write-Host "   - Client Secret: $clientSecret" -ForegroundColor Cyan
Write-Host "   - Tenant ID: $tenantId" -ForegroundColor Cyan

Write-Host "`n2. Deploy your application using:" -ForegroundColor White
Write-Host "   .\deploy-with-auth.ps1 -AzureTenantId '$tenantId' -AzureClientId '$clientId' -AzureClientSecret '$clientSecret' -CosmosDbEndpoint 'YOUR_COSMOS_ENDPOINT' -CosmosDbKey 'YOUR_COSMOS_KEY' -OpenAiEndpoint 'YOUR_OPENAI_ENDPOINT' -OpenAiApiKey 'YOUR_OPENAI_KEY'" -ForegroundColor Cyan

Write-Host "`n3. Verify the configuration in Azure Portal:" -ForegroundColor White
Write-Host "   - Go to Azure Portal > Azure Active Directory > App registrations" -ForegroundColor Cyan
Write-Host "   - Find your app: $AppName" -ForegroundColor Cyan
Write-Host "   - Check Authentication > Platform configurations" -ForegroundColor Cyan
Write-Host "   - Verify redirect URIs are correct" -ForegroundColor Cyan

Write-Host "`n⚠️  IMPORTANT SECURITY NOTES" -ForegroundColor Yellow
Write-Host "===========================" -ForegroundColor Yellow
Write-Host "• Store the client secret securely - it won't be shown again" -ForegroundColor White
Write-Host "• Consider using certificates instead of secrets for production" -ForegroundColor White
Write-Host "• Regularly rotate your client secrets" -ForegroundColor White
Write-Host "• Monitor app registration usage in Azure AD logs" -ForegroundColor White

Write-Host "`n✨ Setup complete! You're ready to deploy with authentication." -ForegroundColor Green

