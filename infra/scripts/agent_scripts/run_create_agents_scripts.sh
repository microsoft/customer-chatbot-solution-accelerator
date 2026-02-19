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
    projectEndpoint=$(extract_value "azureAiAgentEndpoint" "AZURE_AI_AGENT_ENDPOINT")
    solutionName=$(extract_value "solutionName" "SOLUTION_NAME")
    gptModelName=$(extract_value "azureAiAgentModelDeploymentName" "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
    aiFoundryResourceId=$(extract_value "aiFoundryResourceId" "AI_FOUNDRY_RESOURCE_ID")
    apiAppName=$(extract_value "apiAppName" "API_APP_NAME")
    searchEndpoint=$(extract_value "azureAiSearchEndpoint" "AZURE_AI_SEARCH_ENDPOINT")
    
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

# Function to assign RBAC roles to the AI Foundry Agent Identity
# The agent identity is created automatically by AI Foundry with the naming pattern:
# {aiServicesName}-{projectName}-AgentIdentity
assign_agent_identity_roles() {
	echo "=== Assigning RBAC roles to Agent Identity ==="
	
	# Extract AI Services account name from aiFoundryResourceId
	# Handles both formats:
	#   - With project: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}
	#   - Without project: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}
	
	# Try to extract from full path first (with /projects/)
	ai_services_name=$(echo "$aiFoundryResourceId" | sed -n 's|.*/accounts/\([^/]*\)/projects/.*|\1|p')
	project_name=$(echo "$aiFoundryResourceId" | sed -n 's|.*/projects/\([^/]*\).*|\1|p')
	
	# If no project in path, extract AI Services name from account-only path
	if [[ -z "$ai_services_name" ]]; then
		ai_services_name=$(echo "$aiFoundryResourceId" | sed -n 's|.*/accounts/\([^/]*\)$|\1|p')
	fi
	
	if [[ -z "$ai_services_name" ]]; then
		echo "⚠ Warning: Could not extract AI Services name from resource ID."
		echo "  Resource ID: $aiFoundryResourceId"
		return 1
	fi
	
	# If project name not in resource ID, query Azure for it
	if [[ -z "$project_name" ]]; then
		echo "Project name not in resource ID, querying Azure for projects..."
		ai_services_resource_id="/subscriptions/$azSubscriptionId/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$ai_services_name"
		
		# List projects under the AI Services account and get the first one
		# Note: 'name' returns full path like "account/project", so extract just the project part
		full_project_name=$(az resource list \
			--resource-type "Microsoft.CognitiveServices/accounts/projects" \
			--query "[?starts_with(id, '${ai_services_resource_id}/')].name | [0]" \
			-o tsv 2>/dev/null)
		
		if [[ -z "$full_project_name" ]]; then
			echo "⚠ Warning: No projects found under AI Services account '$ai_services_name'."
			echo "  Agent identity roles cannot be assigned until a project exists."
			return 0
		fi
		
		# Extract just the project name (after the /)
		project_name=$(basename "$full_project_name")
		echo "Found project: $project_name"
	fi
	
	# Construct the agent identity display name
	agent_identity_name="${ai_services_name}-${project_name}-AgentIdentity"
	echo "Looking for agent identity: $agent_identity_name"
	
	# Get the agent identity principal ID from Microsoft Entra ID
	agent_principal_id=$(az ad sp list --display-name "$agent_identity_name" --query "[0].id" -o tsv 2>/dev/null)
	
	if [[ -z "$agent_principal_id" ]]; then
		echo "⚠ Warning: Agent identity '$agent_identity_name' not found."
		echo "  This identity is created automatically by AI Foundry. It may take a few minutes to appear."
		echo "  If agents fail with RBAC errors, run this script again or manually assign roles."
		return 0  # Don't fail the script - identity might be created async
	fi
	
	echo "Found agent identity with principal ID: $agent_principal_id"
	
	# Extract AI Services account resource ID (remove /projects/... if present)
	ai_services_resource_id=$(echo "$aiFoundryResourceId" | sed 's|/projects/.*||')
	
	# Extract Search service name from searchEndpoint (format: https://{name}.search.windows.net)
	search_service_name=$(echo "$searchEndpoint" | sed -n 's|https://\([^.]*\)\..*|\1|p')
	search_resource_id="/subscriptions/$azSubscriptionId/resourceGroups/$resource_group/providers/Microsoft.Search/searchServices/$search_service_name"

	# Assign Cognitive Services OpenAI User on AI Services account
	echo "Assigning 'Cognitive Services OpenAI User' role to agent identity on AI Services..."
	if MSYS_NO_PATHCONV=1 az role assignment create \
		--assignee "$agent_principal_id" \
		--role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" \
		--scope "$ai_services_resource_id" \
		--output none 2>/dev/null; then
		echo "✓ Cognitive Services OpenAI User role assigned"
	else
		echo "  Role may already exist or failed to assign"
	fi
	
	# Assign Search Index Data Reader on AI Search service
	echo "Assigning 'Search Index Data Reader' role to agent identity on AI Search..."
	if MSYS_NO_PATHCONV=1 az role assignment create \
		--assignee "$agent_principal_id" \
		--role "1407120a-92aa-4202-b7e9-c0e197c71c8f" \
		--scope "$search_resource_id" \
		--output none 2>/dev/null; then
		echo "✓ Search Index Data Reader role assigned"
	else
		echo "  Role may already exist or failed to assign"
	fi
	
	echo "=== Agent Identity RBAC roles assignment completed ==="
	return 0
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
        
        # Convert to array using readarray (works with set -e, unlike read -d '')
        readarray -t subscriptions <<< "$availableSubscriptions"
        
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
eval $(echo "$python_output" | grep -E "^(chatAgentName|productAgentName|policyAgentName)=")

echo "Agents creation completed."

# Assign RBAC roles to the Agent Identity for OpenAI and Search access
assign_agent_identity_roles

# Update environment variables of API App
az webapp config appsettings set \
  --resource-group "$resource_group" \
  --name "$apiAppName" \
  --settings FOUNDRY_CHAT_AGENT="$chatAgentName" FOUNDRY_PRODUCT_AGENT="$productAgentName" FOUNDRY_POLICY_AGENT="$policyAgentName" \
  -o none

echo "Environment variables updated for App Service: $apiAppName"
echo "Network access will be restored to original settings..."
