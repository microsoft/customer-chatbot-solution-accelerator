# Azure Services Configuration Script
# This script configures Azure OpenAI and Microsoft Entra ID after infrastructure deployment

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$AppNamePrefix = "ecommerce-chat",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "East US"
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 Configuring Azure Services..." -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Yellow
Write-Host "Environment: $Environment" -ForegroundColor Yellow

# Get Key Vault name
$keyVaultName = "$AppNamePrefix-$Environment-kv"
Write-Host "Key Vault: $keyVaultName" -ForegroundColor Yellow

# Check if Key Vault exists
try {
    $keyVault = Get-AzKeyVault -VaultName $keyVaultName
    Write-Host "✅ Key Vault found: $keyVaultName" -ForegroundColor Green
} catch {
    Write-Error "Key Vault not found: $keyVaultName"
    exit 1
}

# Function to add secret to Key Vault
function Add-KeyVaultSecret {
    param(
        [string]$SecretName,
        [string]$SecretValue,
        [string]$Description
    )
    
    try {
        $secret = ConvertTo-SecureString -String $SecretValue -AsPlainText -Force
        Set-AzKeyVaultSecret -VaultName $keyVaultName -Name $SecretName -SecretValue $secret
        Write-Host "✅ Added secret: $SecretName - $Description" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to add secret $SecretName : $_"
    }
}

# Configure Azure OpenAI Service
Write-Host "`n🤖 Configuring Azure OpenAI Service..." -ForegroundColor Blue

$openAiServiceName = "$AppNamePrefix-$Environment-openai"
Write-Host "Checking if Azure OpenAI service exists: $openAiServiceName" -ForegroundColor Yellow

try {
    $openAiService = Get-AzCognitiveServicesAccount -ResourceGroupName $ResourceGroupName -Name $openAiServiceName -ErrorAction SilentlyContinue
    
    if (-not $openAiService) {
        Write-Host "Creating Azure OpenAI service..." -ForegroundColor Yellow
        
        # Create Azure OpenAI service
        $openAiService = New-AzCognitiveServicesAccount `
            -ResourceGroupName $ResourceGroupName `
            -Name $openAiServiceName `
            -Location $Location `
            -SkuName "S0" `
            -Kind "OpenAI" `
            -CustomSubDomainName $openAiServiceName
        
        Write-Host "✅ Azure OpenAI service created: $openAiServiceName" -ForegroundColor Green
    } else {
        Write-Host "✅ Azure OpenAI service already exists: $openAiServiceName" -ForegroundColor Green
    }
    
    # Get the keys
    $keys = Get-AzCognitiveServicesAccountKey -ResourceGroupName $ResourceGroupName -Name $openAiServiceName
    $endpoint = $openAiService.Endpoint
    
    # Add secrets to Key Vault
    Add-KeyVaultSecret -SecretName "azure-openai-endpoint" -SecretValue $endpoint -Description "Azure OpenAI endpoint"
    Add-KeyVaultSecret -SecretName "azure-openai-api-key" -SecretValue $keys.Key1 -Description "Azure OpenAI API key"
    Add-KeyVaultSecret -SecretName "azure-openai-api-version" -SecretValue "2024-02-15-preview" -Description "Azure OpenAI API version"
    
    Write-Host "✅ Azure OpenAI configuration completed" -ForegroundColor Green
    
} catch {
    Write-Warning "Failed to configure Azure OpenAI: $_"
    Write-Host "Please configure Azure OpenAI manually and add secrets to Key Vault" -ForegroundColor Yellow
}

# Configure Microsoft Entra ID App Registration
Write-Host "`n🔐 Configuring Microsoft Entra ID..." -ForegroundColor Blue

$appRegistrationName = "$AppNamePrefix-$Environment-app"
Write-Host "Checking if app registration exists: $appRegistrationName" -ForegroundColor Yellow

try {
    # Check if app registration already exists
    $existingApp = Get-AzADApplication -DisplayName $appRegistrationName -ErrorAction SilentlyContinue
    
    if (-not $existingApp) {
        Write-Host "Creating Microsoft Entra ID app registration..." -ForegroundColor Yellow
        
        # Create app registration
        $appRegistration = New-AzADApplication `
            -DisplayName $appRegistrationName `
            -HomePage "https://$AppNamePrefix-$Environment-frontend.azurewebsites.net" `
            -ReplyUrls @("https://$AppNamePrefix-$Environment-frontend.azurewebsites.net", "http://localhost:5173") `
            -AvailableToOtherTenants $false
        
        # Create service principal
        $servicePrincipal = New-AzADServicePrincipal -ApplicationId $appRegistration.AppId
        
        # Generate client secret
        $clientSecret = New-AzADSpCredential -ObjectId $servicePrincipal.Id -EndDate (Get-Date).AddYears(1)
        
        Write-Host "✅ Microsoft Entra ID app registration created: $appRegistrationName" -ForegroundColor Green
        Write-Host "App ID: $($appRegistration.AppId)" -ForegroundColor Yellow
        Write-Host "Client Secret: $($clientSecret.SecretText)" -ForegroundColor Yellow
        
        # Add secrets to Key Vault
        Add-KeyVaultSecret -SecretName "azure-client-id" -SecretValue $appRegistration.AppId -Description "Microsoft Entra ID Client ID"
        Add-KeyVaultSecret -SecretName "azure-client-secret" -SecretValue $clientSecret.SecretText -Description "Microsoft Entra ID Client Secret"
        Add-KeyVaultSecret -SecretName "azure-tenant-id" -SecretValue (Get-AzContext).Tenant.Id -Description "Microsoft Entra ID Tenant ID"
        
        Write-Host "✅ Microsoft Entra ID configuration completed" -ForegroundColor Green
        
    } else {
        Write-Host "✅ Microsoft Entra ID app registration already exists: $appRegistrationName" -ForegroundColor Green
        Write-Host "App ID: $($existingApp.AppId)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Warning "Failed to configure Microsoft Entra ID: $_"
    Write-Host "Please configure Microsoft Entra ID manually and add secrets to Key Vault" -ForegroundColor Yellow
}

# Update App Service configurations with Key Vault references
Write-Host "`n⚙️ Updating App Service configurations..." -ForegroundColor Blue

try {
    $backendAppServiceName = "$AppNamePrefix-$Environment-backend"
    $frontendAppServiceName = "$AppNamePrefix-$Environment-frontend"
    
    # Update backend app service
    Write-Host "Updating backend app service: $backendAppServiceName" -ForegroundColor Yellow
    
    $backendAppSettings = @{
        "COSMOS_DB_KEY" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/cosmos-db-key/)"
        "AZURE_OPENAI_ENDPOINT" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/azure-openai-endpoint/)"
        "AZURE_OPENAI_API_KEY" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/azure-openai-api-key/)"
        "AZURE_OPENAI_API_VERSION" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/azure-openai-api-version/)"
        "AZURE_CLIENT_ID" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/azure-client-id/)"
        "AZURE_CLIENT_SECRET" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/azure-client-secret/)"
        "AZURE_TENANT_ID" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/azure-tenant-id/)"
    }
    
    Set-AzWebApp -ResourceGroupName $ResourceGroupName -Name $backendAppServiceName -AppSettings $backendAppSettings
    Write-Host "✅ Backend app service updated with Key Vault references" -ForegroundColor Green
    
    # Update frontend app service
    Write-Host "Updating frontend app service: $frontendAppServiceName" -ForegroundColor Yellow
    
    $frontendAppSettings = @{
        "VITE_AZURE_CLIENT_ID" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/azure-client-id/)"
        "VITE_AZURE_TENANT_ID" = "@Microsoft.KeyVault(SecretUri=https://$keyVaultName.vault.azure.net/secrets/azure-tenant-id/)"
    }
    
    Set-AzWebApp -ResourceGroupName $ResourceGroupName -Name $frontendAppServiceName -AppSettings $frontendAppSettings
    Write-Host "✅ Frontend app service updated with Key Vault references" -ForegroundColor Green
    
} catch {
    Write-Warning "Failed to update App Service configurations: $_"
    Write-Host "Please update app settings manually with Key Vault references" -ForegroundColor Yellow
}

# Display configuration summary
Write-Host "`n📋 Configuration Summary:" -ForegroundColor Cyan
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "Key Vault: $keyVaultName" -ForegroundColor White
Write-Host "Backend App Service: $AppNamePrefix-$Environment-backend" -ForegroundColor White
Write-Host "Frontend App Service: $AppNamePrefix-$Environment-frontend" -ForegroundColor White

Write-Host "`n🔗 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Deploy your application code to the App Services" -ForegroundColor White
Write-Host "2. Test the application endpoints" -ForegroundColor White
Write-Host "3. Configure custom domains if needed" -ForegroundColor White
Write-Host "4. Set up monitoring and alerting" -ForegroundColor White

Write-Host "`n✨ Configuration completed!" -ForegroundColor Green