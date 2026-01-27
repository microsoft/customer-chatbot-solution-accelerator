#!/bin/bash
set -e
echo "Started the agent creation script setup..."

# Variables
projectEndpoint="$1"
solutionName="$2"
gptModelName="$3"
aiFoundryResourceId="$4"
apiAppName="$5"
resourceGroup="$6"
searchEndpoint="$7"

# get parameters from azd env, if not provided
if [ -z "$projectEndpoint" ]; then
    projectEndpoint=$(azd env get-value AZURE_AI_AGENT_ENDPOINT)
fi

if [ -z "$solutionName" ]; then
    solutionName=$(azd env get-value SOLUTION_NAME)
fi

if [ -z "$gptModelName" ]; then
    gptModelName=$(azd env get-value AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME)
fi

if [ -z "$aiFoundryResourceId" ]; then
    aiFoundryResourceId=$(azd env get-value AI_FOUNDRY_RESOURCE_ID)
fi

if [ -z "$apiAppName" ]; then
    apiAppName=$(azd env get-value API_APP_NAME)
fi

if [ -z "$resourceGroup" ]; then
    resourceGroup=$(azd env get-value AZURE_RESOURCE_GROUP)
fi

if [ -z "$searchEndpoint" ]; then
    searchEndpoint=$(azd env get-value AZURE_AI_SEARCH_ENDPOINT)
fi


# Check if all required arguments are provided
if [ -z "$projectEndpoint" ] || [ -z "$solutionName" ] || [ -z "$gptModelName" ] || [ -z "$aiFoundryResourceId" ] || [ -z "$apiAppName" ] || [ -z "$resourceGroup" ] || [ -z "$searchEndpoint" ]; then
    echo "Usage: $0 <projectEndpoint> <solutionName> <gptModelName> <aiFoundryResourceId> <apiAppName> <resourceGroup> <searchEndpoint>"
    exit 1
fi

# Check if user is logged in to Azure
echo "Checking Azure authentication..."
if az account show &> /dev/null; then
    echo "Already authenticated with Azure."
else
    # Use Azure CLI login if running locally
    # echo "Authenticating with Azure CLI..."
    az login
fi

echo "Getting principal id (user or service principal)"
# Temporarily disable exit on error for principal detection
set +e
# Try to get signed-in user first (for interactive logins)
signed_user_id=$(az ad signed-in-user show --query id -o tsv 2>/dev/null)

# If that fails, we're likely using a service principal - get its object ID
if [ -z "$signed_user_id" ]; then
    echo "Not logged in as user, checking for service principal..."
    account_info=$(az account show --query '{name:user.name, type:user.type}' -o json)
    account_type=$(echo "$account_info" | jq -r '.type')
    
    if [ "$account_type" = "servicePrincipal" ]; then
        sp_name=$(echo "$account_info" | jq -r '.name')
        echo "Logged in as service principal: $sp_name"
        signed_user_id=$(az ad sp show --id "$sp_name" --query id -o tsv 2>/dev/null)
        
        if [ -z "$signed_user_id" ]; then
            echo "Warning: Could not get service principal object ID. Attempting to continue without role assignment..."
            echo "Note: Ensure the service principal has necessary permissions assigned at subscription/resource group level."
            SKIP_ROLE_ASSIGNMENT=true
        else
            echo "Service principal object ID: $signed_user_id"
        fi
    else
        echo "Warning: Could not determine principal ID. Attempting to continue without role assignment..."
        SKIP_ROLE_ASSIGNMENT=true
    fi
else
    echo "Logged in as user: $signed_user_id"
fi
# Re-enable exit on error
set -e

echo "Checking if the principal has Azure AI User role on the AI Foundry"

if [ "$SKIP_ROLE_ASSIGNMENT" != "true" ] && [ -n "$signed_user_id" ]; then
    role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
      --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" \
      --scope "$aiFoundryResourceId" \
      --assignee "$signed_user_id" \
      --query "[].roleDefinitionId" -o tsv)

    if [ -z "$role_assignment" ]; then
        echo "Principal does not have the Azure AI User role. Assigning the role..."
        MSYS_NO_PATHCONV=1 az role assignment create \
          --assignee "$signed_user_id" \
          --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" \
          --scope "$aiFoundryResourceId" \
          --output none

        if [ $? -eq 0 ]; then
            echo "Azure AI User role assigned successfully."
        else
            echo "Failed to assign Azure AI User role."
            exit 1
        fi
    else
        echo "Principal already has the Azure AI User role."
    fi
else
    echo "Skipping role assignment (will rely on existing permissions)"
fi


requirementFile="infra/scripts/agent_scripts/requirements.txt"

# Download and install Python requirements
python -m pip install --upgrade pip
python -m pip install --quiet -r "$requirementFile"

# Execute the Python scripts
echo "Running Python agents creation script..."
python_output=$(python infra/scripts/agent_scripts/01_create_agents.py --ai_project_endpoint="$projectEndpoint" --solution_name="$solutionName" --gpt_model_name="$gptModelName" --ai_search_endpoint="$searchEndpoint")
eval $(echo "$python_output" | grep -E "^(chatAgentId|productAgentId|policyAgentId)=")

echo "Agents creation completed."

# Update environment variables of API App
az webapp config appsettings set \
  --resource-group "$resourceGroup" \
  --name "$apiAppName" \
  --settings FOUNDRY_CHAT_AGENT_ID="$chatAgentId" FOUNDRY_CUSTOM_PRODUCT_AGENT_ID="$productAgentId" FOUNDRY_POLICY_AGENT_ID="$policyAgentId" \
  -o none

echo "Environment variables updated for App Service: $apiAppName"