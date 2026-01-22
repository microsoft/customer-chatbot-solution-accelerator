#!/usr/bin/env pwsh

# Variables
param(
    [string]$solutionName,
    [string]$aiFoundryName,
    [string]$backend_app_pid,
    [string]$backend_app_uid,
    [string]$app_service,
    [string]$resource_group,
    [string]$ai_search_endpoint,
    [string]$azure_openai_endpoint,
    [string]$embedding_model_name,
    [string]$aiFoundryResourceId,
    [string]$aiSearchResourceId,
    [string]$cosmosdb_account
)

Write-Host "Starting the data upload script"

# Get parameters from azd env, if not provided
if ([string]::IsNullOrEmpty($solutionName)) {
    $solutionName = azd env get-value SOLUTION_NAME
}

if ([string]::IsNullOrEmpty($aiFoundryName)) {
    $aiFoundryName = azd env get-value AI_SERVICE_NAME
}

if ([string]::IsNullOrEmpty($backend_app_pid)) {
    $backend_app_pid = azd env get-value API_PID
}

if ([string]::IsNullOrEmpty($backend_app_uid)) {
    $backend_app_uid = azd env get-value API_UID
}

if ([string]::IsNullOrEmpty($app_service)) {
    $app_service = azd env get-value API_APP_NAME
}

if ([string]::IsNullOrEmpty($resource_group)) {
    $resource_group = azd env get-value RESOURCE_GROUP_NAME
}

if ([string]::IsNullOrEmpty($ai_search_endpoint)) {
    $ai_search_endpoint = azd env get-value AZURE_AI_SEARCH_ENDPOINT
}

if ([string]::IsNullOrEmpty($azure_openai_endpoint)) {
    $azure_openai_endpoint = azd env get-value AZURE_OPENAI_ENDPOINT
}

if ([string]::IsNullOrEmpty($embedding_model_name)) {
    $embedding_model_name = azd env get-value AZURE_OPENAI_EMBEDDING_MODEL
}

if ([string]::IsNullOrEmpty($aiFoundryResourceId)) {
    $aiFoundryResourceId = azd env get-value AI_FOUNDRY_RESOURCE_ID
}

if ([string]::IsNullOrEmpty($aiSearchResourceId)) {
    $aiSearchResourceId = azd env get-value AI_SEARCH_SERVICE_RESOURCE_ID
}

if ([string]::IsNullOrEmpty($cosmosdb_account)) {
    $cosmosdb_account = azd env get-value AZURE_COSMOSDB_ACCOUNT
}

# Check if user is logged in to Azure
Write-Host "Checking Azure authentication..."
try {
    $null = az account show 2>&1
    Write-Host "Already authenticated with Azure."
} catch {
    # Use Azure CLI login if running locally
    Write-Host "Authenticating with Azure CLI..."
    az login
}

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
python infra/scripts/data_scripts/03_write_products_to_cosmos.py --cosmosdb_account="$cosmosdb_account"

Write-Host "Data upload script completed."
