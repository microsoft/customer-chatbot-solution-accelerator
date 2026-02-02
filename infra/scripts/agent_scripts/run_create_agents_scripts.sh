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

original_foundry_public_access=""

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

# Function to enable public network access temporarily
enable_public_access() {
	echo "=== Temporarily enabling public network access for services ==="
	# Enable public access for AI Foundry
	# Extract the account resource ID (remove /projects/... part if present)
	aif_account_resource_id=$(echo "$aiFoundryResourceId" | sed 's|/projects/.*||')
	aif_resource_name=$(basename "$aif_account_resource_id")
	# Extract resource group from the AI Foundry account resource ID
	aif_resource_group=$(echo "$aif_account_resource_id" | sed -n 's|.*/resourceGroups/\([^/]*\)/.*|\1|p')
	# Extract subscription ID from the AI Foundry account resource ID
	aif_subscription_id=$(echo "$aif_account_resource_id" | sed -n 's|.*/subscriptions/\([^/]*\)/.*|\1|p')

	original_foundry_public_access=$(az cognitiveservices account show \
		--name "$aif_resource_name" \
		--resource-group "$aif_resource_group" \
		--subscription "$aif_subscription_id" \
		--query "properties.publicNetworkAccess" \
		--output tsv)
	if [ -z "$original_foundry_public_access" ] || [ "$original_foundry_public_access" = "null" ]; then
		echo "⚠ Info: Could not retrieve AI Foundry network access status."
		echo "  AI Foundry network access might be managed differently."
	elif [ "$original_foundry_public_access" != "Enabled" ]; then
		echo "Current AI Foundry public access: $original_foundry_public_access"
		echo "Enabling public access for AI Foundry resource: $aif_resource_name (Resource Group: $aif_resource_group)"
		if MSYS_NO_PATHCONV=1 az resource update \
			--ids "$aif_account_resource_id" \
			--api-version 2024-10-01 \
			--set properties.publicNetworkAccess=Enabled properties.apiProperties="{}" \
			--output none; then
			echo "✓ AI Foundry public access enabled"
		else
			echo "⚠ Warning: Failed to enable AI Foundry public access automatically."
		fi
	else
		echo "✓ AI Foundry public access already enabled - no changes needed"
	fi
	
	if [ -n "$original_foundry_public_access" ] && [ "$original_foundry_public_access" != "Enabled" ]; then
		# Wait for changes to take effect - Azure network changes can take 30-60 seconds to propagate
		echo "Waiting for network access changes to propagate (this may take up to 60 seconds)..."
		sleep 30
		
		# Verify that public access is actually enabled by checking the current state
		echo "Verifying public network access is enabled..."
		current_access=$(az cognitiveservices account show \
			--name "$aif_resource_name" \
			--resource-group "$aif_resource_group" \
			--subscription "$aif_subscription_id" \
			--query "properties.publicNetworkAccess" \
			--output tsv 2>/dev/null || echo "Unknown")
		
		if [ "$current_access" = "Enabled" ]; then
			echo "✓ Verified: Public network access is enabled"
		else
			echo "⚠ Warning: Public access verification returned: $current_access"
			echo "  Waiting additional 30 seconds for propagation..."
			sleep 30
		fi
	fi
	echo "=== Public network access enabled successfully ==="
	return 0
}

# Function to restore original network access settings
restore_network_access() {
	echo "=== Restoring original network access settings ==="
	
	# Restore AI Foundry access only if it was changed from the original state
	if [ -n "$original_foundry_public_access" ] && [ "$original_foundry_public_access" != "Enabled" ]; then
		echo "Restoring AI Foundry public access to: $original_foundry_public_access"
		# Reconstruct the AI Foundry resource ID for restoration
		aif_account_resource_id=$(echo "$aiFoundryResourceId" | sed 's|/projects/.*||')
		# Try using the working approach to restore the original setting
		if MSYS_NO_PATHCONV=1 az resource update \
			--ids "$aif_account_resource_id" \
			--api-version 2024-10-01 \
			--set properties.publicNetworkAccess="$original_foundry_public_access" \
        	--set properties.apiProperties.qnaAzureSearchEndpointKey="" \
        	--set properties.networkAcls.bypass="AzureServices" \
			--output none 2>/dev/null; then
			echo "✓ AI Foundry access restored"
		else
			echo "⚠ Warning: Failed to restore AI Foundry access automatically."
			echo "  Please manually restore network access in the Azure portal if needed."
		fi
	else
		echo "AI Foundry access unchanged (no restoration needed)"
	fi

	echo "=== Network access restoration completed ==="
}

# Function to handle script cleanup on exit
cleanup_on_exit() {
	exit_code=$?
	echo ""
	if [ $exit_code -ne 0 ]; then
		echo "Script failed with exit code: $exit_code"
	fi
	echo "Performing cleanup..."
	restore_network_access
	exit $exit_code
}

# Set up trap to ensure cleanup happens on exit
trap cleanup_on_exit EXIT INT TERM

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

echo "Getting signed in user id"
signed_user_id=$(az ad signed-in-user show --query id -o tsv)

echo "Checking if the user has Azure AI User role on the AI Foundry"
role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
  --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" \
  --scope "$aiFoundryResourceId" \
  --assignee "$signed_user_id" \
  --query "[].roleDefinitionId" -o tsv)

if [ -z "$role_assignment" ]; then
    echo "User does not have the Azure AI User role. Assigning the role..."
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
    echo "User already has the Azure AI User role."
fi


requirementFile="infra/scripts/agent_scripts/requirements.txt"

# Download and install Python requirements
python -m pip install --upgrade pip
python -m pip install --quiet -r "$requirementFile"

# Enable public network access for required services
enable_public_access
if [ $? -ne 0 ]; then
	echo "Error: Failed to enable public network access for services."
	exit 1
fi

# Execute the Python scripts
echo "Running Python agents creation script..."
python_output=$(python infra/scripts/agent_scripts/01_create_agents.py --ai_project_endpoint="$projectEndpoint" --solution_name="$solutionName" --gpt_model_name="$gptModelName" --ai_search_endpoint="$searchEndpoint")
eval $(echo "$python_output" | grep -E "^(chatAgentName|productAgentName|policyAgentName)=")

echo "Agents creation completed."

# Update environment variables of API App
az webapp config appsettings set \
  --resource-group "$resourceGroup" \
  --name "$apiAppName" \
  --settings FOUNDRY_CHAT_AGENT="$chatAgentName" FOUNDRY_PRODUCT_AGENT="$productAgentName" FOUNDRY_POLICY_AGENT="$policyAgentName" \
  -o none

echo "Environment variables updated for App Service: $apiAppName"
echo "Network access will be restored to original settings..."
