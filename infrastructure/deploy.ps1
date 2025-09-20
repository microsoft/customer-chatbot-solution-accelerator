# Azure Infrastructure Deployment Script
# This script deploys the e-commerce chat application infrastructure to Azure

param(
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "East US",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$AppNamePrefix = "ecommerce-chat"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Azure Infrastructure Deployment..." -ForegroundColor Green
Write-Host "Subscription ID: $SubscriptionId" -ForegroundColor Yellow
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Yellow
Write-Host "Location: $Location" -ForegroundColor Yellow
Write-Host "Environment: $Environment" -ForegroundColor Yellow

# Login to Azure (if not already logged in)
Write-Host "🔐 Checking Azure login status..." -ForegroundColor Blue
try {
    $context = Get-AzContext
    if (-not $context) {
        Write-Host "Not logged in. Please log in to Azure..." -ForegroundColor Yellow
        Connect-AzAccount
    }
    Write-Host "✅ Successfully logged in to Azure" -ForegroundColor Green
} catch {
    Write-Error "Failed to login to Azure: $_"
    exit 1
}

# Set subscription
Write-Host "📋 Setting subscription..." -ForegroundColor Blue
try {
    Set-AzContext -SubscriptionId $SubscriptionId
    Write-Host "✅ Subscription set to: $SubscriptionId" -ForegroundColor Green
} catch {
    Write-Error "Failed to set subscription: $_"
    exit 1
}

# Create resource group if it doesn't exist
Write-Host "📦 Creating resource group..." -ForegroundColor Blue
try {
    $rg = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
    if (-not $rg) {
        New-AzResourceGroup -Name $ResourceGroupName -Location $Location
        Write-Host "✅ Resource group created: $ResourceGroupName" -ForegroundColor Green
    } else {
        Write-Host "✅ Resource group already exists: $ResourceGroupName" -ForegroundColor Green
    }
} catch {
    Write-Error "Failed to create resource group: $_"
    exit 1
}

# Deploy Bicep template
Write-Host "🏗️ Deploying Bicep template..." -ForegroundColor Blue
try {
    $deploymentName = "ecommerce-chat-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    $deploymentResult = New-AzResourceGroupDeployment `
        -ResourceGroupName $ResourceGroupName `
        -TemplateFile "main.bicep" `
        -TemplateParameterFile "parameters.json" `
        -Name $deploymentName `
        -Verbose
    
    Write-Host "✅ Bicep template deployed successfully!" -ForegroundColor Green
    Write-Host "Deployment Name: $deploymentName" -ForegroundColor Yellow
    
    # Display outputs
    Write-Host "📊 Deployment Outputs:" -ForegroundColor Cyan
    $deploymentResult.Outputs | ForEach-Object {
        Write-Host "  $($_.Key): $($_.Value.Value)" -ForegroundColor White
    }
    
} catch {
    Write-Error "Failed to deploy Bicep template: $_"
    exit 1
}

# Configure Key Vault access policies
Write-Host "🔑 Configuring Key Vault access policies..." -ForegroundColor Blue
try {
    $keyVaultName = "$AppNamePrefix-$Environment-kv"
    $currentUser = (Get-AzContext).Account.Id
    
    # Get the current user's object ID
    $userObjectId = (Get-AzADUser -UserPrincipalName $currentUser).Id
    
    # Set Key Vault access policy
    Set-AzKeyVaultAccessPolicy `
        -VaultName $keyVaultName `
        -ObjectId $userObjectId `
        -PermissionsToSecrets Get, Set, List, Delete `
        -PermissionsToKeys Get, List, Create, Delete, Update, Import, Backup, Restore, Recover, Purge
    
    Write-Host "✅ Key Vault access policies configured" -ForegroundColor Green
} catch {
    Write-Warning "Failed to configure Key Vault access policies: $_"
    Write-Host "You may need to configure access policies manually" -ForegroundColor Yellow
}

# Display next steps
Write-Host "`n🎉 Infrastructure deployment completed successfully!" -ForegroundColor Green
Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Configure Azure OpenAI Service:" -ForegroundColor White
Write-Host "   - Go to Azure Portal > Create Resource > Azure OpenAI" -ForegroundColor Gray
Write-Host "   - Create a new Azure OpenAI resource" -ForegroundColor Gray
Write-Host "   - Deploy GPT-4o model" -ForegroundColor Gray
Write-Host "   - Add secrets to Key Vault" -ForegroundColor Gray

Write-Host "`n2. Configure Microsoft Entra ID:" -ForegroundColor White
Write-Host "   - Go to Azure Portal > Azure Active Directory > App registrations" -ForegroundColor Gray
Write-Host "   - Create new app registration" -ForegroundColor Gray
Write-Host "   - Add secrets to Key Vault" -ForegroundColor Gray

Write-Host "`n3. Deploy Application Code:" -ForegroundColor White
Write-Host "   - Use Azure CLI or Azure DevOps to deploy frontend and backend" -ForegroundColor Gray
Write-Host "   - Configure app settings with Key Vault references" -ForegroundColor Gray

Write-Host "`n4. Test the Application:" -ForegroundColor White
Write-Host "   - Frontend: https://$AppNamePrefix-$Environment-frontend.azurewebsites.net" -ForegroundColor Gray
Write-Host "   - Backend: https://$AppNamePrefix-$Environment-backend.azurewebsites.net" -ForegroundColor Gray
Write-Host "   - API Docs: https://$AppNamePrefix-$Environment-backend.azurewebsites.net/docs" -ForegroundColor Gray

Write-Host "`n🔗 Useful Links:" -ForegroundColor Cyan
Write-Host "Azure Portal: https://portal.azure.com" -ForegroundColor Blue
Write-Host "Resource Group: https://portal.azure.com/#@/resource/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName" -ForegroundColor Blue

Write-Host "`n✨ Happy coding!" -ForegroundColor Green