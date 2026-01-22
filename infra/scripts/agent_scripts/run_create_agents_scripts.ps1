#!/usr/bin/env pwsh
#Requires -Version 7.0

param(
    [string]$resourceGroup,
    [Alias("resource_group")]
    [string]$ResourceGroupAlias
)

# Handle both parameter naming conventions
if (-not $resourceGroup -and $ResourceGroupAlias) {
    $resourceGroup = $ResourceGroupAlias
}

# Variables
$projectEndpoint = ""
$solutionName = ""
$gptModelName = ""
$aiFoundryResourceId = ""
$apiAppName = ""
$searchEndpoint = ""
$azSubscriptionId = ""

$ErrorActionPreference = "Stop"
Write-Host "Started the agent creation script setup..."

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
    
    try {
        $script:projectEndpoint = $(azd env get-value AZURE_AI_AGENT_ENDPOINT 2>$null)
        $script:solutionName = $(azd env get-value SOLUTION_NAME 2>$null)
        $script:gptModelName = $(azd env get-value AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME 2>$null)
        $script:aiFoundryResourceId = $(azd env get-value AI_FOUNDRY_RESOURCE_ID 2>$null)
        $script:apiAppName = $(azd env get-value API_APP_NAME 2>$null)
        $script:resourceGroup = $(azd env get-value AZURE_RESOURCE_GROUP 2>$null)
        $script:searchEndpoint = $(azd env get-value AZURE_AI_SEARCH_ENDPOINT 2>$null)
    } catch {
        Write-Host "Error: Failed to retrieve values from azd environment."
        return $false
    }
    
    # Validate that we got all required values (check for empty or error messages)
    if (-not $script:projectEndpoint -or $script:projectEndpoint -match "ERROR:" -or
        -not $script:solutionName -or $script:solutionName -match "ERROR:" -or
        -not $script:gptModelName -or $script:gptModelName -match "ERROR:" -or
        -not $script:aiFoundryResourceId -or $script:aiFoundryResourceId -match "ERROR:" -or
        -not $script:apiAppName -or $script:apiAppName -match "ERROR:" -or
        -not $script:resourceGroup -or $script:resourceGroup -match "ERROR:" -or
        -not $script:searchEndpoint -or $script:searchEndpoint -match "ERROR:") {
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
    $deploymentName = az group show --name $resourceGroup --query "tags.DeploymentName" -o tsv
    if (-not $deploymentName) {
        Write-Host "Error: Could not find deployment name in resource group tags."
        return $false
    }
    
    Write-Host "Fetching deployment outputs for deployment: $deploymentName"
    $deploymentOutputs = az deployment group show --resource-group $resourceGroup --name $deploymentName --query "properties.outputs" -o json | ConvertFrom-Json
    if (-not $deploymentOutputs) {
        Write-Host "Error: Could not fetch deployment outputs."
        return $false
    }
    
    # Extract all values using the helper function
    $script:projectEndpoint = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "AZURE_AI_AGENT_ENDPOINT" -FallbackKey "azureAiAgentEndpoint"
    $script:solutionName = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "SOLUTION_NAME" -FallbackKey "solutionName"
    $script:gptModelName = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME" -FallbackKey "azureAiAgentModelDeploymentName"
    $script:aiFoundryResourceId = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "AI_FOUNDRY_RESOURCE_ID" -FallbackKey "aiFoundryResourceId"
    $script:apiAppName = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "API_APP_NAME" -FallbackKey "apiAppName"
    $script:searchEndpoint = Get-DeploymentValue -DeploymentOutputs $deploymentOutputs -PrimaryKey "AZURE_AI_SEARCH_ENDPOINT" -FallbackKey "azureAiSearchEndpoint"
    
    # Validate that we extracted all required values
    if (-not $script:projectEndpoint -or -not $script:solutionName -or -not $script:gptModelName -or -not $script:aiFoundryResourceId -or -not $script:apiAppName -or -not $script:searchEndpoint) {
        Write-Host "Error: Could not extract all required values from deployment outputs."
        return $false
    }
    
    Write-Host "Successfully retrieved values from deployment outputs."
    return $true
}

# Authenticate with Azure
try {
    $null = az account show 2>$null
    Write-Host "Already authenticated with Azure."
} catch {
    Write-Host "Not authenticated with Azure. Attempting to authenticate..."
    Write-Host "Authenticating with Azure CLI..."
    az login
}

# Get subscription ID from azd if available
if (Test-AzdInstalled) {
    try {
        $azSubscriptionId = $(azd env get-value AZURE_SUBSCRIPTION_ID 2>$null)
        if (-not $azSubscriptionId -or $azSubscriptionId -match "ERROR:") {
            $azSubscriptionId = $env:AZURE_SUBSCRIPTION_ID
        }
    } catch {
        $azSubscriptionId = $env:AZURE_SUBSCRIPTION_ID
    }
}

# If still no subscription ID, get from current az account
if (-not $azSubscriptionId) {
    $azSubscriptionId = az account show --query id -o tsv
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
if (-not $resourceGroup) {
    # No resource group provided - use azd env
    if (-not (Get-ValuesFromAzdEnv)) {
        Write-Host "Failed to get values from azd environment."
        Write-Host "If you want to use deployment outputs instead, please provide the resource group name as an argument."
        Write-Host "Usage: .\run_create_agents_scripts.ps1 -resourceGroup <ResourceGroupName>"
        exit 1
    }
} else {
    # Resource group provided - use deployment outputs
    Write-Host "Resource group provided: $resourceGroup"
    
    if (-not (Get-ValuesFromAzDeployment)) {
        Write-Host "Failed to get values from deployment outputs."
        exit 1
    }
}

Write-Host ""
Write-Host "==============================================="
Write-Host "Values to be used:"
Write-Host "==============================================="
Write-Host "Resource Group: $resourceGroup"
Write-Host "Project Endpoint: $projectEndpoint"
Write-Host "Solution Name: $solutionName"
Write-Host "GPT Model Name: $gptModelName"
Write-Host "AI Foundry Resource ID: $aiFoundryResourceId"
Write-Host "API App Name: $apiAppName"
Write-Host "Search Endpoint: $searchEndpoint"
Write-Host "Subscription ID: $azSubscriptionId"
Write-Host "==============================================="
Write-Host ""

Write-Host "Getting signed in user id"
$signed_user_id = az ad signed-in-user show --query id -o tsv

Write-Host "Checking if the user has Azure AI User role on the AI Foundry"
$role_assignment = az role assignment list `
  --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" `
  --scope "$aiFoundryResourceId" `
  --assignee "$signed_user_id" `
  --query "[].roleDefinitionId" -o tsv

if ([string]::IsNullOrEmpty($role_assignment)) {
    Write-Host "User does not have the Azure AI User role. Assigning the role..."
    az role assignment create `
      --assignee "$signed_user_id" `
      --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" `
      --scope "$aiFoundryResourceId" `
      --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Azure AI User role assigned successfully."
    } else {
        Write-Host "Failed to assign Azure AI User role."
        exit 1
    }
} else {
    Write-Host "User already has the Azure AI User role."
}

$requirementFile = "infra/scripts/agent_scripts/requirements.txt"

# Download and install Python requirements
Write-Host "Installing Python requirements..."
python -m pip install --upgrade pip
python -m pip install --quiet -r "$requirementFile"

# Execute the Python scripts
Write-Host "Running Python agents creation script..."
$python_output = python infra/scripts/agent_scripts/01_create_agents.py --ai_project_endpoint="$projectEndpoint" --solution_name="$solutionName" --gpt_model_name="$gptModelName" --ai_search_endpoint="$searchEndpoint"

# Parse the output to extract agent IDs
$chatAgentId = ""
$productAgentId = ""
$policyAgentId = ""

foreach ($line in $python_output) {
    if ($line -match "^chatAgentId=(.+)$") {
        $chatAgentId = $Matches[1]
    }
    elseif ($line -match "^productAgentId=(.+)$") {
        $productAgentId = $Matches[1]
    }
    elseif ($line -match "^policyAgentId=(.+)$") {
        $policyAgentId = $Matches[1]
    }
}

Write-Host "Agents creation completed."
Write-Host "Chat Agent ID: $chatAgentId"
Write-Host "Product Agent ID: $productAgentId"
Write-Host "Policy Agent ID: $policyAgentId"

# Update environment variables of API App
Write-Host "Updating environment variables for App Service: $apiAppName"
az webapp config appsettings set `
  --resource-group "$resourceGroup" `
  --name "$apiAppName" `
  --settings FOUNDRY_CHAT_AGENT_ID="$chatAgentId" FOUNDRY_CUSTOM_PRODUCT_AGENT_ID="$productAgentId" FOUNDRY_POLICY_AGENT_ID="$policyAgentId" `
  -o none

Write-Host "Environment variables updated for App Service: $apiAppName"
Write-Host "Agent creation script completed successfully."
