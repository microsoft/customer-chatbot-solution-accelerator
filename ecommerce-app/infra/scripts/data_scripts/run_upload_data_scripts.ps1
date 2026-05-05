#!/usr/bin/env pwsh
#Requires -Version 7.0

param(
    [string]$resource_group
)

# Variables
$solutionName = ""
$aiFoundryName = ""
$backend_app_pid = ""
$backend_app_uid = ""
$app_service = ""
$ai_search_endpoint = ""
$azure_openai_endpoint = ""
$embedding_model_name = ""
$aiFoundryResourceId = ""
$aiSearchResourceId = ""
$cosmosdb_account = ""
$azSubscriptionId = ""

function Test-AzdInstalled {
    try {
        $null = Get-Command azd -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Get-ValuesFromAzdEnv {
    if (-not (Test-AzdInstalled)) {
        Write-Host "Error: Azure Developer CLI is not installed."
        return $false
    }

    Write-Host "Getting values from azd environment..."
    
    $script:solutionName = $(azd env get-value SOLUTION_NAME)
    $script:aiFoundryName = $(azd env get-value AI_SERVICE_NAME)
    $script:backend_app_pid = $(azd env get-value API_PID)
    $script:backend_app_uid = $(azd env get-value API_UID)
    $script:app_service = $(azd env get-value API_APP_NAME)
    $script:resource_group = $(azd env get-value RESOURCE_GROUP_NAME)
    $script:ai_search_endpoint = $(azd env get-value AZURE_AI_SEARCH_ENDPOINT)
    $script:azure_openai_endpoint = $(azd env get-value AZURE_OPENAI_ENDPOINT)
    $script:embedding_model_name = $(azd env get-value AZURE_OPENAI_EMBEDDING_MODEL)
    $script:aiFoundryResourceId = $(azd env get-value AI_FOUNDRY_RESOURCE_ID)
    $script:aiSearchResourceId = $(azd env get-value AI_SEARCH_SERVICE_RESOURCE_ID)
    $script:cosmosdb_account = $(azd env get-value AZURE_COSMOSDB_ACCOUNT)
    
    # Validate that we got all required values
    if (-not $script:resource_group -or -not $script:ai_search_endpoint -or -not $script:azure_openai_endpoint -or -not $script:cosmosdb_account) {
        Write-Host "Error: Could not retrieve all required values from azd environment."
        return $false
    }
    
    Write-Host "Successfully retrieved values from azd environment."
    return $true
}

function Get-DeploymentValue {
    param(
        [object]$DeploymentOutputs,
        [string]$PrimaryKey,
        [string]$FallbackKey
    )
    
    $value = $null
    
    # Try primary key first
    if ($DeploymentOutputs.PSObject.Properties[$PrimaryKey]) {
        $value = $DeploymentOutputs.$PrimaryKey.value
    }
    
    # If primary key failed, try fallback key
    if (-not $value -and $DeploymentOutputs.PSObject.Properties[$FallbackKey]) {
        $value = $DeploymentOutputs.$FallbackKey.value
    }
    
    return $value
}

function Get-ValuesFromAzDeployment {
    Write-Host "Getting values from Azure deployment outputs..."
    
    Write-Host "Fetching deployment name..."
    $deploymentName = az group show --name $resource_group --query "tags.DeploymentName" -o tsv
    if (-not $deploymentName) {
        Write-Host "Error: Could not find deployment name in resource group tags."
        return $false
    }
    
    Write-Host "Fetching deployment outputs for deployment: $deploymentName"
    $deploymentOutputs = az deployment group show --resource-group $resource_group --name $deploymentName --query "properties.outputs" -o json | ConvertFrom-Json
    if (-not $deploymentOutputs) {
        Write-Host "Error: Could not fetch deployment outputs."
        return $false
    }
    
    # Extract all values using the helper function
    $script:solutionName = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "solutioN_NAME" -FallbackKey "solutionName"
    $script:aiFoundryName = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "aI_SERVICE_NAME" -FallbackKey "aiServiceName"
    $script:backend_app_pid = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "apI_PID" -FallbackKey "apiPid"
    $script:backend_app_uid = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "apI_UID" -FallbackKey "apiUid"
    $script:app_service = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "apI_APP_NAME" -FallbackKey "apiAppName"
    $script:ai_search_endpoint = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "azurE_AI_SEARCH_ENDPOINT" -FallbackKey "azureAiSearchEndpoint"
    $script:azure_openai_endpoint = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "azurE_OPENAI_ENDPOINT" -FallbackKey "azureOpenaiEndpoint"
    $script:embedding_model_name = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "azurE_OPENAI_EMBEDDING_MODEL" -FallbackKey "azureOpenaiEmbeddingModel"
    $script:aiFoundryResourceId = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "aI_FOUNDRY_RESOURCE_ID" -FallbackKey "aiFoundryResourceId"
    $script:aiSearchResourceId = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "aI_SEARCH_SERVICE_RESOURCE_ID" -FallbackKey "aiSearchServiceResourceId"
    $script:cosmosdb_account = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "azurE_COSMOSDB_ACCOUNT" -FallbackKey "azureCosmosdbAccount"
    
    # Validate that we extracted all required values
    if (-not $script:ai_search_endpoint -or -not $script:azure_openai_endpoint -or -not $script:cosmosdb_account) {
        Write-Host "Error: Could not extract all required values from deployment outputs."
        return $false
    }
    
    Write-Host "Successfully retrieved values from deployment outputs."
    return $true
}

Write-Host "Starting the data upload script"

# Authenticate with Azure
$null = az account show 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Already authenticated with Azure."
} else {
    Write-Host "Not authenticated with Azure. Attempting to authenticate..."
    Write-Host "Authenticating with Azure CLI..."
    az login
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI login failed. Please verify your credentials and try again."
    }
}

# Get subscription ID from azd if available
if (Test-AzdInstalled) {
    try {
        $azSubscriptionId = $(azd env get-value AZURE_SUBSCRIPTION_ID)
        if (-not $azSubscriptionId) {
            $azSubscriptionId = $env:AZURE_SUBSCRIPTION_ID
        }
    } catch {
        $azSubscriptionId = ""
    }
}

# Check if user has selected the correct subscription
$currentSubscriptionId = az account show --query id -o tsv
$currentSubscriptionName = az account show --query name -o tsv

if ($currentSubscriptionId -ne $azSubscriptionId -and $azSubscriptionId) {
    Write-Host "Current selected subscription is $currentSubscriptionName ( $currentSubscriptionId )."
    $confirmation = Read-Host "Do you want to continue with this subscription?(y/n)"
    if ($confirmation -notin @("y", "Y")) {
        Write-Host "Fetching available subscriptions..."
        $availableSubscriptions = az account list --query "[?state=='Enabled'].[name,id]" --output json | ConvertFrom-Json
        
        do {
            Write-Host ""
            Write-Host "Available Subscriptions:"
            Write-Host "========================"
            for ($i = 0; $i -lt $availableSubscriptions.Count; $i++) {
                $index = $i + 1
                Write-Host "$index. $($availableSubscriptions[$i][0]) ( $($availableSubscriptions[$i][1]) )"
            }
            Write-Host "========================"
            Write-Host ""
            
            $subscriptionIndex = Read-Host "Enter the number of the subscription (1-$($availableSubscriptions.Count)) to use"
            
            if ($subscriptionIndex -match '^\d+$' -and [int]$subscriptionIndex -ge 1 -and [int]$subscriptionIndex -le $availableSubscriptions.Count) {
                $selectedIndex = [int]$subscriptionIndex - 1
                $selectedSubscriptionName = $availableSubscriptions[$selectedIndex][0]
                $selectedSubscriptionId = $availableSubscriptions[$selectedIndex][1]
                
                try {
                    az account set --subscription $selectedSubscriptionId
                    Write-Host "Switched to subscription: $selectedSubscriptionName ( $selectedSubscriptionId )"
                    $azSubscriptionId = $selectedSubscriptionId
                    break
                } catch {
                    Write-Host "Failed to switch to subscription: $selectedSubscriptionName ( $selectedSubscriptionId )."
                }
            } else {
                Write-Host "Invalid selection. Please try again."
            }
        } while ($true)
    } else {
        Write-Host "Proceeding with the current subscription: $currentSubscriptionName ( $currentSubscriptionId )"
        az account set --subscription $currentSubscriptionId
        $azSubscriptionId = $currentSubscriptionId
    }
} else {
    Write-Host "Proceeding with the subscription: $currentSubscriptionName ( $currentSubscriptionId )"
    az account set --subscription $currentSubscriptionId
    $azSubscriptionId = $currentSubscriptionId
}

# Get configuration values based on strategy
if (-not $resource_group) {
    # No resource group provided - use azd env
    if (-not (Get-ValuesFromAzdEnv)) {
        Write-Host "Failed to get values from azd environment."
        Write-Host "If you want to use deployment outputs instead, please provide the resource group name as an argument."
        Write-Host "Usage: .\run_upload_data_scripts.ps1 -resource_group <ResourceGroupName>"
        exit 1
    }
} else {
    # Resource group provided - use deployment outputs
    Write-Host "Resource group provided: $resource_group"
    
    if (-not (Get-ValuesFromAzDeployment)) {
        Write-Host "Failed to get values from deployment outputs."
        exit 1
    }
}

Write-Host ""
Write-Host "==============================================="
Write-Host "Values to be used:"
Write-Host "==============================================="
Write-Host "Resource Group: $resource_group"
Write-Host "AI Search Endpoint: $ai_search_endpoint"
Write-Host "Azure OpenAI Endpoint: $azure_openai_endpoint"
Write-Host "Cosmos DB Account: $cosmosdb_account"
Write-Host "Subscription ID: $azSubscriptionId"
Write-Host "==============================================="
Write-Host ""

Write-Host "Getting signed in user id"
$signed_user_id = az ad signed-in-user show --query id -o tsv

Write-Host "Checking if the user has Search roles on the AI Search Service"
# search service contributor role id: 7ca78c08-252a-4471-8644-bb5ff32d4ba0
# search index data contributor role id: 8ebe5a00-799e-43f5-93ac-243d3dce84a7
# search index data reader role id: 1407120a-92aa-4202-b7e9-c0e197c71c8f

$role_assignment = az role assignment list `
  --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" `
  --scope "$aiSearchResourceId" `
  --assignee "$signed_user_id" `
  --query "[].roleDefinitionId" -o tsv

if ([string]::IsNullOrEmpty($role_assignment)) {
    Write-Host "User does not have the search service contributor role. Assigning the role..."
    az role assignment create `
      --assignee "$signed_user_id" `
      --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" `
      --scope "$aiSearchResourceId" `
      --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Search service contributor role assigned successfully."
    } else {
        Write-Host "Failed to assign search service contributor role."
        exit 1
    }
} else {
    Write-Host "User already has the search service contributor role."
}

$role_assignment = az role assignment list `
  --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" `
  --scope "$aiSearchResourceId" `
  --assignee "$signed_user_id" `
  --query "[].roleDefinitionId" -o tsv

if ([string]::IsNullOrEmpty($role_assignment)) {
    Write-Host "User does not have the search index data contributor role. Assigning the role..."
    az role assignment create `
      --assignee "$signed_user_id" `
      --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" `
      --scope "$aiSearchResourceId" `
      --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Search index data contributor role assigned successfully."
    } else {
        Write-Host "Failed to assign search index data contributor role."
        exit 1
    }
} else {
    Write-Host "User already has the search index data contributor role."
}

$role_assignment = az role assignment list `
  --role "1407120a-92aa-4202-b7e9-c0e197c71c8f" `
  --scope "$aiSearchResourceId" `
  --assignee "$signed_user_id" `
  --query "[].roleDefinitionId" -o tsv

if ([string]::IsNullOrEmpty($role_assignment)) {
    Write-Host "User does not have the search index data reader role. Assigning the role..."
    az role assignment create `
      --assignee "$signed_user_id" `
      --role "1407120a-92aa-4202-b7e9-c0e197c71c8f" `
      --scope "$aiSearchResourceId" `
      --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Search index data reader role assigned successfully."
    } else {
        Write-Host "Failed to assign search index data reader role."
        exit 1
    }
} else {
    Write-Host "User already has the search index data reader role."
}

# Check if the user has the Cosmos DB Built-in Data Contributor role
Write-Host "Checking if user has the Cosmos DB Built-in Data Contributor role"
$roleExists = az cosmosdb sql role assignment list `
    --resource-group $resource_group `
    --account-name $cosmosdb_account `
    --query "[?roleDefinitionId.ends_with(@, '00000000-0000-0000-0000-000000000002') && principalId == '$signed_user_id']" -o tsv

# Check if the role exists
if (![string]::IsNullOrEmpty($roleExists)) {
    Write-Host "User already has the Cosmos DB Built-in Data Contributer role."
} else {
    Write-Host "User does not have the Cosmos DB Built-in Data Contributer role. Assigning the role."
    az cosmosdb sql role assignment create `
        --resource-group $resource_group `
        --account-name $cosmosdb_account `
        --role-definition-id 00000000-0000-0000-0000-000000000002 `
        --principal-id $signed_user_id `
        --scope "/" `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Cosmos DB Built-in Data Contributer role assigned successfully."
    } else {
        Write-Host "Failed to assign Cosmos DB Built-in Data Contributer role."
    }
}

# Commented out sections from original bash script
# $role_assignment = az role assignment list `
#   --role "00000000-0000-0000-0000-000000000002" `
#   --scope "$cosmosdbAccountId" `
#   --assignee "$signed_user_id" `
#   --query "[].roleDefinitionId" -o tsv

# if ([string]::IsNullOrEmpty($role_assignment)) {
#     Write-Host "User does not have the Cosmos DB account contributor role. Assigning the role..."
#     az role assignment create `
#       --assignee "$signed_user_id" `
#       --role "00000000-0000-0000-0000-000000000002" `
#       --scope "$cosmosdbAccountId" `
#       --output none

#     if ($LASTEXITCODE -eq 0) {
#         Write-Host "Cosmos DB account contributor role assigned successfully."
#     } else {
#         Write-Host "Failed to assign Cosmos DB account contributor role."
#         exit 1
#     }
# } else {
#     Write-Host "User already has the Cosmos DB account contributor role."
# }

# $role_assignment = az cosmosdb sql role assignment list `
#   --account-name "$cosmosdb_account" `
#   --resource-group "$resource_group" `
#   --scope "$cosmosdbAccountId" `
#   --principal-id "$signed_user_id" `
#   --query "[].roleDefinitionId" -o tsv

# if ([string]::IsNullOrEmpty($role_assignment)) {
#     Write-Host "User does not have the Cosmos DB SQL role. Assigning the role..."
#     az cosmosdb sql role assignment create `
#       --account-name "$cosmosdb_account" `
#       --resource-group "$resource_group" `
#       --principal-id "$signed_user_id" `
#       --role-definition-id "00000000-0000-0000-0000-000000000002" `
#       --scope "$cosmosdbAccountId" `
#       --output none

#     if ($LASTEXITCODE -eq 0) {
#         Write-Host "Cosmos DB SQL role assigned successfully."
#     } else {
#         Write-Host "Failed to assign Cosmos DB SQL role."
#         exit 1
#     }
# } else {
#     Write-Host "User already has the Cosmos DB SQL role."
# }

# python -m venv .venv
# .venv\Scripts\activate

$requirementFile = "infra/scripts/data_scripts/requirements.txt"

# Download and install Python requirements
Write-Host "Installing Python requirements..."
python -m pip install --upgrade pip
python -m pip install --quiet -r "$requirementFile"

# Run Python scripts
Write-Host "Running data upload scripts..."
python infra/scripts/data_scripts/01_create_products_search_index.py --ai_search_endpoint="$ai_search_endpoint" --azure_openai_endpoint="$azure_openai_endpoint" --embedding_model_name="$embedding_model_name"
python infra/scripts/data_scripts/02_create_policies_search_index.py --ai_search_endpoint="$ai_search_endpoint" --azure_openai_endpoint="$azure_openai_endpoint" --embedding_model_name="$embedding_model_name"

# For WAF deployments, temporarily enable public network access on Cosmos DB
Write-Host "=== Temporarily enabling public network access for Cosmos DB ==="
Write-Host "Configuring Cosmos DB network access: $cosmosdb_account"

# Get Cosmos DB resource ID
$subscription_id = az account show --query id -o tsv
$cosmos_resource_id = "/subscriptions/${subscription_id}/resourceGroups/${resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/${cosmosdb_account}"

# Get current public network access setting
$originalCosmosPublicAccess = az resource show --ids $cosmos_resource_id --api-version 2021-04-15 --query "properties.publicNetworkAccess" -o tsv 2>$null
Write-Host "Original Cosmos DB public access: $originalCosmosPublicAccess"

$cosmosAccessEnabled = $false
$originalCosmosIpFilter = "[]"

# Only modify Cosmos DB if it's not already enabled
if ($originalCosmosPublicAccess -eq "Enabled") {
    Write-Host "✓ Cosmos DB public access already enabled - no changes needed"
} else {
    Write-Host "Getting current IP address..."
    $currentIp = (Invoke-RestMethod -Uri "https://api.ipify.org?format=text" -TimeoutSec 10)
    Write-Host "Current IP: $currentIp"
    
    # Get current firewall rules
    Write-Host "Getting current firewall configuration..."
    $originalCosmosIpFilter = az resource show --ids $cosmos_resource_id --api-version 2021-04-15 --query "properties.ipRules" -o json 2>$null
    if (-not $originalCosmosIpFilter) {
        $originalCosmosIpFilter = "[]"
    }
    
    Write-Host "Cosmos DB public access is '$originalCosmosPublicAccess' - enabling access"
    
    # Add current IP to firewall rules and enable public network access
    Write-Host "Adding current IP ($currentIp) to Cosmos DB firewall..."
    $ipRuleJson = "[{\`"ipAddressOrRange\`":\`"$currentIp\`"}]"
    
    az resource update --ids $cosmos_resource_id --api-version 2021-04-15 --set "properties.ipRules=$ipRuleJson" --set "properties.publicNetworkAccess=Enabled" --output none 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Cosmos DB firewall updated to allow current IP"
        Write-Host "✓ Cosmos DB public network access enabled"
        $cosmosAccessEnabled = $true
        
        # Wait for changes to propagate
        Write-Host "Waiting for Cosmos DB network changes to take effect (30 seconds)..."
        Start-Sleep -Seconds 30
        Write-Host "Network configuration should now be active"
    } else {
        Write-Host "⚠ Warning: Failed to update Cosmos DB firewall. You may need to manually add IP $currentIp"
        Write-Host "  Please add this IP address in Azure Portal: Cosmos DB > $cosmosdb_account > Networking > Firewall"
    }
}

Write-Host "=== Public network access enabled successfully ==="

# Run the Cosmos DB upload script within try/finally to ensure network settings are restored on error
$dataUploadFailed = $false
try {
    python infra/scripts/data_scripts/03_write_products_to_cosmos.py --cosmosdb_account="$cosmosdb_account"
    if ($LASTEXITCODE -ne 0) {
        throw "Cosmos DB upload script failed with exit code $LASTEXITCODE"
    }
    $cosmosUploadSuccess = $true
}
catch {
    Write-Host "Error running Cosmos DB upload script: $_"
    $dataUploadFailed = $true
}
finally {
    # Restore original settings - This block ALWAYS runs, even if an error occurred
    Write-Host "=== Restoring original network access settings ==="

    if ($cosmosAccessEnabled) {
        Write-Host "Restoring Cosmos DB settings..."
        
        # Restore both firewall rules and public access setting
        $restoreSuccess = $false
        if ($originalCosmosPublicAccess -and $originalCosmosPublicAccess -ne "null") {
            Write-Host "Restoring Cosmos DB public access to: $originalCosmosPublicAccess"
            az resource update --ids $cosmos_resource_id --api-version 2021-04-15 --set "properties.ipRules=$originalCosmosIpFilter" --set "properties.publicNetworkAccess=$originalCosmosPublicAccess" --output none 2>$null
            $restoreSuccess = ($LASTEXITCODE -eq 0)
        } else {
            az resource update --ids $cosmos_resource_id --api-version 2021-04-15 --set "properties.ipRules=$originalCosmosIpFilter" --output none 2>$null
            $restoreSuccess = ($LASTEXITCODE -eq 0)
        }
        
        if ($restoreSuccess) {
            Write-Host "✓ Cosmos DB settings restored"
        } else {
            Write-Host "⚠ Warning: Failed to restore Cosmos DB settings automatically."
            Write-Host "  Please manually check firewall and network settings in the Azure portal."
        }
    } else {
        Write-Host "Cosmos DB unchanged (no restoration needed)"
    }

    Write-Host "=== Network access restoration completed ==="
}

# Exit with error if data upload failed
if ($dataUploadFailed) {
    Write-Host "Data upload script failed. Network settings have been restored."
    exit 1
}

Write-Host "Data upload script completed."
