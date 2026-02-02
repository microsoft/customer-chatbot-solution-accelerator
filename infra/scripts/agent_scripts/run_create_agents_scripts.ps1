#!/usr/bin/env pwsh

# Variables
param(
    [string]$projectEndpoint,
    [string]$solutionName,
    [string]$gptModelName,
    [string]$aiFoundryResourceId,
    [string]$apiAppName,
    [string]$resourceGroup,
    [string]$searchEndpoint
)

$ErrorActionPreference = "Stop"
Write-Host "Started the agent creation script setup..."

# Get parameters from azd env, if not provided
if ([string]::IsNullOrEmpty($projectEndpoint)) {
    $projectEndpoint = azd env get-value AZURE_AI_AGENT_ENDPOINT
}

if ([string]::IsNullOrEmpty($solutionName)) {
    $solutionName = azd env get-value SOLUTION_NAME
}

if ([string]::IsNullOrEmpty($gptModelName)) {
    $gptModelName = azd env get-value AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME
}

if ([string]::IsNullOrEmpty($aiFoundryResourceId)) {
    $aiFoundryResourceId = azd env get-value AI_FOUNDRY_RESOURCE_ID
}

if ([string]::IsNullOrEmpty($apiAppName)) {
    $apiAppName = azd env get-value API_APP_NAME
}

if ([string]::IsNullOrEmpty($resourceGroup)) {
    $resourceGroup = azd env get-value AZURE_RESOURCE_GROUP
}

if ([string]::IsNullOrEmpty($searchEndpoint)) {
    $searchEndpoint = azd env get-value AZURE_AI_SEARCH_ENDPOINT
}

# Check if all required arguments are provided
if ([string]::IsNullOrEmpty($projectEndpoint) -or 
    [string]::IsNullOrEmpty($solutionName) -or 
    [string]::IsNullOrEmpty($gptModelName) -or 
    [string]::IsNullOrEmpty($aiFoundryResourceId) -or 
    [string]::IsNullOrEmpty($apiAppName) -or 
    [string]::IsNullOrEmpty($resourceGroup) -or 
    [string]::IsNullOrEmpty($searchEndpoint)) {
    Write-Host "Usage: $PSCommandPath <projectEndpoint> <solutionName> <gptModelName> <aiFoundryResourceId> <apiAppName> <resourceGroup> <searchEndpoint>"
    exit 1
}

# Check if user is logged in to Azure
Write-Host "Checking Azure authentication..."
try {
    $null = az account show 2>&1
    Write-Host "Already authenticated with Azure."
} catch {
    # Use Azure CLI login if running locally
    az login
}

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

# Parse the output to extract agent names
$chatAgentName = ""
$productAgentName = ""
$policyAgentName = ""

foreach ($line in $python_output) {
    if ($line -match "^chatAgentName=(.+)$") {
        $chatAgentName = $Matches[1]
    }
    elseif ($line -match "^productAgentName=(.+)$") {
        $productAgentName = $Matches[1]
    }
    elseif ($line -match "^policyAgentName=(.+)$") {
        $policyAgentName = $Matches[1]
    }
}

Write-Host "Agents creation completed."
Write-Host "Chat Agent Name: $chatAgentName"
Write-Host "Product Agent Name: $productAgentName"
Write-Host "Policy Agent Name: $policyAgentName"

# Update environment variables of API App
Write-Host "Updating environment variables for App Service: $apiAppName"
az webapp config appsettings set `
  --resource-group "$resourceGroup" `
  --name "$apiAppName" `
  --settings FOUNDRY_CHAT_AGENT="$chatAgentName" FOUNDRY_PRODUCT_AGENT="$productAgentName" FOUNDRY_POLICY_AGENT="$policyAgentName" `
  -o none

Write-Host "Environment variables updated for App Service: $apiAppName"
Write-Host "Agent creation script completed successfully."
