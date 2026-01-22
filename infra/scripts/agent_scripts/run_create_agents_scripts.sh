#!/bin/bash
set -e
echo "Started the agent creation script setup..."

# Parse command line arguments
resource_group=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --resource-group)
            resource_group="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Variables
projectEndpoint=""
solutionName=""
gptModelName=""
aiFoundryResourceId=""
apiAppName=""
searchEndpoint=""
azSubscriptionId=""
original_foundry_public_access=""

function test_azd_installed() {
    if command -v azd &> /dev/null; then
        return 0
    else
        return 1
    fi
}

function get_values_from_azd_env() {
    if ! test_azd_installed; then
        echo "Error: Azure Developer CLI is not installed."
        return 1
    fi

    echo "Getting values from azd environment..."
    
    projectEndpoint=$(azd env get-value AZURE_AI_AGENT_ENDPOINT 2>/dev/null)
    solutionName=$(azd env get-value SOLUTION_NAME 2>/dev/null)
    gptModelName=$(azd env get-value AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME 2>/dev/null)
    aiFoundryResourceId=$(azd env get-value AI_FOUNDRY_RESOURCE_ID 2>/dev/null)
    apiAppName=$(azd env get-value API_APP_NAME 2>/dev/null)
    resource_group=$(azd env get-value AZURE_RESOURCE_GROUP 2>/dev/null)
    searchEndpoint=$(azd env get-value AZURE_AI_SEARCH_ENDPOINT 2>/dev/null)
    
    # Validate that we got all required values
    if [[ -z "$projectEndpoint" || -z "$solutionName" || -z "$gptModelName" || -z "$aiFoundryResourceId" || -z "$apiAppName" || -z "$resource_group" || -z "$searchEndpoint" ]]; then
        echo "Error: Could not retrieve all required values from azd environment."
        return 1
    fi
    
    echo "Successfully retrieved values from azd environment."
    return 0
}

# Helper function to extract value with fallback (case-insensitive)
extract_value() {
    local primary_key="$1"
    local fallback_key="$2"
    local result
    
    # Use case-insensitive grep (-i) to match the key
    result=$(echo "$deploymentOutputs" | grep -i -A 3 "\"$primary_key\"" | grep '"value"' | sed 's/.*"value": *"\([^"]*\)".*/\1/' | head -1)
    if [ -z "$result" ]; then
        result=$(echo "$deploymentOutputs" | grep -i -A 3 "\"$fallback_key\"" | grep '"value"' | sed 's/.*"value": *"\([^"]*\)".*/\1/' | head -1)
    fi
    echo "$result"
}

function get_values_from_az_deployment() {
    echo "Getting values from Azure deployment outputs..."
    
    echo "Fetching deployment name..."
    deploymentName=$(az group show --name "$resource_group" --query "tags.DeploymentName" -o tsv)
    if [[ -z "$deploymentName" ]]; then
        echo "Error: Could not find deployment name in resource group tags."
        return 1
    fi
    
    echo "Fetching deployment outputs for deployment: $deploymentName"
    deploymentOutputs=$(az deployment group show --resource-group "$resource_group" --name "$deploymentName" --query "properties.outputs" -o json)
    if [[ -z "$deploymentOutputs" ]]; then
        echo "Error: Could not fetch deployment outputs."
        return 1
    fi
    
    # Extract all values using the helper function (keys are case-insensitive)
    projectEndpoint=$(extract_value "azurE_AI_AGENT_ENDPOINT" "AZURE_AI_AGENT_ENDPOINT")
    solutionName=$(extract_value "solutioN_NAME" "SOLUTION_NAME")
    gptModelName=$(extract_value "azurE_AI_AGENT_MODEL_DEPLOYMENT_NAME" "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
    aiFoundryResourceId=$(extract_value "aI_FOUNDRY_RESOURCE_ID" "AI_FOUNDRY_RESOURCE_ID")
    apiAppName=$(extract_value "apI_APP_NAME" "API_APP_NAME")
    searchEndpoint=$(extract_value "azurE_AI_SEARCH_ENDPOINT" "AZURE_AI_SEARCH_ENDPOINT")
    
    # Debug output
    echo "Extracted values:"
    echo "  projectEndpoint: $projectEndpoint"
    echo "  solutionName: $solutionName"
    echo "  gptModelName: $gptModelName"
    echo "  aiFoundryResourceId: $aiFoundryResourceId"
    echo "  apiAppName: $apiAppName"
    echo "  searchEndpoint: $searchEndpoint"
    
    # Validate that we extracted all required values
    if [[ -z "$projectEndpoint" || -z "$solutionName" || -z "$gptModelName" || -z "$aiFoundryResourceId" || -z "$apiAppName" || -z "$searchEndpoint" ]]; then
        echo "Error: Could not extract all required values from deployment outputs."
        return 1
    fi
    
    echo "Successfully retrieved values from deployment outputs."
    return 0
}

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
	
	# Wait a bit for changes to take effect
	echo "Waiting for network access changes to propagate..."
	sleep 10
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

# Authenticate with Azure
if az account show &> /dev/null; then
    echo "Already authenticated with Azure."
else
    echo "Not authenticated with Azure. Attempting to authenticate..."
    echo "Authenticating with Azure CLI..."
    az login
fi

# Get subscription ID from azd if available
if test_azd_installed; then
    azSubscriptionId=$(azd env get-value AZURE_SUBSCRIPTION_ID 2>/dev/null || echo "")
    if [[ -z "$azSubscriptionId" ]]; then
        azSubscriptionId="$AZURE_SUBSCRIPTION_ID"
    fi
fi

# If still no subscription ID, get from current az account
if [[ -z "$azSubscriptionId" ]]; then
    azSubscriptionId=$(az account show --query id -o tsv)
fi

# Check if user has selected the correct subscription
currentSubscriptionId=$(az account show --query id -o tsv)
currentSubscriptionName=$(az account show --query name -o tsv)

if [[ "$currentSubscriptionId" != "$azSubscriptionId" && -n "$azSubscriptionId" ]]; then
    echo "Current selected subscription is $currentSubscriptionName ( $currentSubscriptionId )."
    read -p "Do you want to continue with this subscription?(y/n): " confirmation
    if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
        echo "Fetching available subscriptions..."
        availableSubscriptions=$(az account list --query "[?state=='Enabled'].[name,id]" --output tsv)
        
        # Convert to array
        IFS=$'\n' read -d '' -r -a subscriptions <<< "$availableSubscriptions"
        
        while true; do
            echo ""
            echo "Available Subscriptions:"
            echo "========================"
            index=1
            for ((i=0; i<${#subscriptions[@]}; i++)); do
                IFS=$'\t' read -r name id <<< "${subscriptions[i]}"
                echo "$index. $name ( $id )"
                ((index++))
            done
            echo "========================"
            echo ""
            
            read -p "Enter the number of the subscription (1-$((${#subscriptions[@]}))) to use: " subscriptionIndex
            
            if [[ "$subscriptionIndex" =~ ^[0-9]+$ ]] && [[ "$subscriptionIndex" -ge 1 ]] && [[ "$subscriptionIndex" -le "${#subscriptions[@]}" ]]; then
                selectedIndex=$((subscriptionIndex - 1))
                IFS=$'\t' read -r selectedSubscriptionName selectedSubscriptionId <<< "${subscriptions[selectedIndex]}"
                
                if az account set --subscription "$selectedSubscriptionId"; then
                    echo "Switched to subscription: $selectedSubscriptionName ( $selectedSubscriptionId )"
                    azSubscriptionId="$selectedSubscriptionId"
                    break
                else
                    echo "Failed to switch to subscription: $selectedSubscriptionName ( $selectedSubscriptionId )."
                fi
            else
                echo "Invalid selection. Please try again."
            fi
        done
    else
        echo "Proceeding with the current subscription: $currentSubscriptionName ( $currentSubscriptionId )"
        az account set --subscription "$currentSubscriptionId"
        azSubscriptionId="$currentSubscriptionId"
    fi
else
    echo "Proceeding with the subscription: $currentSubscriptionName ( $currentSubscriptionId )"
    az account set --subscription "$currentSubscriptionId"
    azSubscriptionId="$currentSubscriptionId"
fi

# Get configuration values based on strategy
if [[ -z "$resource_group" ]]; then
    # No resource group provided - use azd env
    if ! get_values_from_azd_env; then
        echo "Failed to get values from azd environment."
        echo "If you want to use deployment outputs instead, please provide the resource group name as an argument."
        echo "Usage: ./run_create_agents_scripts.sh --resource-group <ResourceGroupName>"
        exit 1
    fi
else
    # Resource group provided - use deployment outputs
    echo "Resource group provided: $resource_group"
    
    if ! get_values_from_az_deployment; then
        echo "Failed to get values from deployment outputs."
        exit 1
    fi
fi

echo ""
echo "==============================================="
echo "Values to be used:"
echo "==============================================="
echo "Resource Group: $resource_group"
echo "Project Endpoint: $projectEndpoint"
echo "Solution Name: $solutionName"
echo "GPT Model Name: $gptModelName"
echo "AI Foundry Resource ID: $aiFoundryResourceId"
echo "API App Name: $apiAppName"
echo "Search Endpoint: $searchEndpoint"
echo "Subscription ID: $azSubscriptionId"
echo "==============================================="
echo ""

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
eval $(echo "$python_output" | grep -E "^(chatAgentId|productAgentId|policyAgentId)=")

echo "Agents creation completed."

# Update environment variables of API App
az webapp config appsettings set \
  --resource-group "$resource_group" \
  --name "$apiAppName" \
  --settings FOUNDRY_CHAT_AGENT_ID="$chatAgentId" FOUNDRY_CUSTOM_PRODUCT_AGENT_ID="$productAgentId" FOUNDRY_POLICY_AGENT_ID="$policyAgentId" \
  -o none

echo "Environment variables updated for App Service: $apiAppName"
echo "Network access will be restored to original settings..."
