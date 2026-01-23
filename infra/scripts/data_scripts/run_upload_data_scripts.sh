#!/bin/bash

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
solutionName=""
aiFoundryName=""
backend_app_pid=""
backend_app_uid=""
app_service=""
ai_search_endpoint=""
azure_openai_endpoint=""
embedding_model_name=""
aiFoundryResourceId=""
aiSearchResourceId=""
cosmosdb_account=""
azSubscriptionId=""

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
    
    solutionName=$(azd env get-value SOLUTION_NAME)
    aiFoundryName=$(azd env get-value AI_SERVICE_NAME)
    backend_app_pid=$(azd env get-value API_PID)
    backend_app_uid=$(azd env get-value API_UID)
    app_service=$(azd env get-value API_APP_NAME)
    resource_group=$(azd env get-value RESOURCE_GROUP_NAME)
    ai_search_endpoint=$(azd env get-value AZURE_AI_SEARCH_ENDPOINT)
    azure_openai_endpoint=$(azd env get-value AZURE_OPENAI_ENDPOINT)
    embedding_model_name=$(azd env get-value AZURE_OPENAI_EMBEDDING_MODEL)
    aiFoundryResourceId=$(azd env get-value AI_FOUNDRY_RESOURCE_ID)
    aiSearchResourceId=$(azd env get-value AI_SEARCH_SERVICE_RESOURCE_ID)
    cosmosdb_account=$(azd env get-value AZURE_COSMOSDB_ACCOUNT)
    
    # Validate that we got all required values
    if [[ -z "$resource_group" || -z "$ai_search_endpoint" || -z "$azure_openai_endpoint" || -z "$cosmosdb_account" ]]; then
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
    
    # Extract all values using the helper function
    solutionName=$(extract_value "solutioN_NAME" "solutionName")
    aiFoundryName=$(extract_value "aI_SERVICE_NAME" "aiServiceName")
    backend_app_pid=$(extract_value "apI_PID" "apiPid")
    backend_app_uid=$(extract_value "apI_UID" "apiUid")
    app_service=$(extract_value "apI_APP_NAME" "apiAppName")
    ai_search_endpoint=$(extract_value "azurE_AI_SEARCH_ENDPOINT" "azureAiSearchEndpoint")
    azure_openai_endpoint=$(extract_value "azurE_OPENAI_ENDPOINT" "azureOpenaiEndpoint")
    embedding_model_name=$(extract_value "azurE_OPENAI_EMBEDDING_MODEL" "azureOpenaiEmbeddingModel")
    aiFoundryResourceId=$(extract_value "aI_FOUNDRY_RESOURCE_ID" "aiFoundryResourceId")
    aiSearchResourceId=$(extract_value "aI_SEARCH_SERVICE_RESOURCE_ID" "aiSearchServiceResourceId")
    cosmosdb_account=$(extract_value "azurE_COSMOSDB_ACCOUNT" "azureCosmosdbAccount")
    
    # Validate that we extracted all required values
    if [[ -z "$ai_search_endpoint" || -z "$azure_openai_endpoint" || -z "$cosmosdb_account" ]]; then
        echo "Error: Could not extract all required values from deployment outputs."
        return 1
    fi
    
    echo "Successfully retrieved values from deployment outputs."
    return 0
}

original_foundry_public_access=""
original_cosmos_public_access=""
original_cosmos_ip_filter=""

# Function to enable public network access temporarily
enable_public_access() {
	echo "=== Temporarily enabling public network access for services ==="

	# Enable public access for Cosmos DB
	echo "Configuring Cosmos DB network access: $cosmosdb_account"
	
	# Get Cosmos DB resource ID  
	subscription_id=$(az account show --query id -o tsv)
	cosmos_resource_id="/subscriptions/${subscription_id}/resourceGroups/${resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/${cosmosdb_account}"
	
	original_cosmos_public_access=$(MSYS_NO_PATHCONV=1 az resource show \
		--ids "$cosmos_resource_id" \
		--api-version 2021-04-15 \
		--query "properties.publicNetworkAccess" \
		--output tsv 2>/dev/null)
	echo "Original Cosmos DB public access: $original_cosmos_public_access"
	
	# Only modify Cosmos DB if it's not already enabled
	if [ "$original_cosmos_public_access" = "Enabled" ]; then
		echo "✓ Cosmos DB public access already enabled - no changes needed"
	else
		echo "Getting current IP address..."
		current_ip=$(curl -s https://ipinfo.io/ip)
		echo "Current IP: $current_ip"
        # Get current firewall rules and public network access setting
        echo "Getting current firewall configuration..."
        original_cosmos_ip_filter=$(MSYS_NO_PATHCONV=1 az resource show \
            --ids "$cosmos_resource_id" \
            --api-version 2021-04-15 \
            --query "properties.ipRules" \
            --output json 2>/dev/null || echo "[]")

		echo "Cosmos DB public access is '$original_cosmos_public_access' - enabling access"
		
		# Add current IP to firewall rules and enable public network access
		echo "Adding current IP ($current_ip) to Cosmos DB firewall..."
		if MSYS_NO_PATHCONV=1 az resource update \
			--ids "$cosmos_resource_id" \
			--api-version 2021-04-15 \
			--set "properties.ipRules=[{\"ipAddressOrRange\":\"$current_ip\"}]" \
			--set "properties.publicNetworkAccess=Enabled" \
			--output none; then
			echo "✓ Cosmos DB firewall updated to allow current IP"
			echo "✓ Cosmos DB public network access enabled"
			
			# Wait longer for changes to propagate
			echo "Waiting for Cosmos DB network changes to take effect..."
			sleep 30
			echo "Network configuration should now be active"
		else
			echo "⚠ Warning: Failed to update Cosmos DB firewall. You may need to manually add IP $current_ip"
			echo "  Please add this IP address in Azure Portal: Cosmos DB > $cosmosdb_account > Networking > Firewall"
		fi
	fi

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

	# Restore Cosmos DB settings only if it was changed from the original state
	if [ -n "$original_cosmos_public_access" ] && [ "$original_cosmos_public_access" != "Enabled" ]; then
		echo "Restoring Cosmos DB settings..."
		subscription_id=$(az account show --query id -o tsv)
		cosmos_resource_id="/subscriptions/${subscription_id}/resourceGroups/${resource_group}/providers/Microsoft.DocumentDB/databaseAccounts/${cosmosdb_account}"
		
		# Prepare restore command with both firewall rules and public access setting
		restore_command="--set properties.ipRules=$original_cosmos_ip_filter"
		if [ -n "$original_cosmos_public_access" ] && [ "$original_cosmos_public_access" != "null" ]; then
			restore_command="$restore_command --set properties.publicNetworkAccess=$original_cosmos_public_access"
			echo "Restoring Cosmos DB public access to: $original_cosmos_public_access"
		fi
		
		if MSYS_NO_PATHCONV=1 az resource update \
			--ids "$cosmos_resource_id" \
			--api-version 2021-04-15 \
			$restore_command \
			--output none; then
			echo "✓ Cosmos DB settings restored"
		else
			echo "⚠ Warning: Failed to restore Cosmos DB settings automatically."
			echo "  Please manually check firewall and network settings in the Azure portal."
		fi
	else
		echo "Cosmos DB unchanged (no restoration needed)"
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
        echo "Usage: ./run_upload_data_scripts.sh --resource-group <ResourceGroupName>"
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
echo "AI Search Endpoint: $ai_search_endpoint"
echo "Azure OpenAI Endpoint: $azure_openai_endpoint"
echo "Cosmos DB Account: $cosmosdb_account"
echo "Subscription ID: $azSubscriptionId"
echo "==============================================="
echo ""

echo "Getting signed in user id"
signed_user_id=$(az ad signed-in-user show --query id -o tsv)

echo "Checking if the user has Search roles on the AI Search Service"
# search service contributor role id: 7ca78c08-252a-4471-8644-bb5ff32d4ba0
# search index data contributor role id: 8ebe5a00-799e-43f5-93ac-243d3dce84a7
# search index data reader role id: 1407120a-92aa-4202-b7e9-c0e197c71c8f

role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
  --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" \
  --scope "$aiSearchResourceId" \
  --assignee "$signed_user_id" \
  --query "[].roleDefinitionId" -o tsv)

if [ -z "$role_assignment" ]; then
    echo "User does not have the search service contributor role. Assigning the role..."
    MSYS_NO_PATHCONV=1 az role assignment create \
      --assignee "$signed_user_id" \
      --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" \
      --scope "$aiSearchResourceId" \
      --output none

    if [ $? -eq 0 ]; then
        echo "Search service contributor role assigned successfully."
    else
        echo "Failed to assign search service contributor role."
        exit 1
    fi
else
    echo "User already has the search service contributor role."
fi

role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
  --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" \
  --scope "$aiSearchResourceId" \
  --assignee "$signed_user_id" \
  --query "[].roleDefinitionId" -o tsv)

if [ -z "$role_assignment" ]; then
    echo "User does not have the search index data contributor role. Assigning the role..."
    MSYS_NO_PATHCONV=1 az role assignment create \
      --assignee "$signed_user_id" \
      --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" \
      --scope "$aiSearchResourceId" \
      --output none

    if [ $? -eq 0 ]; then
        echo "Search index data contributor role assigned successfully."
    else
        echo "Failed to assign search index data contributor role."
        exit 1
    fi
else
    echo "User already has the search index data contributor role."
fi

role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
  --role "1407120a-92aa-4202-b7e9-c0e197c71c8f" \
  --scope "$aiSearchResourceId" \
  --assignee "$signed_user_id" \
  --query "[].roleDefinitionId" -o tsv)

if [ -z "$role_assignment" ]; then
    echo "User does not have the search index data reader role. Assigning the role..."
    MSYS_NO_PATHCONV=1 az role assignment create \
      --assignee "$signed_user_id" \
      --role "1407120a-92aa-4202-b7e9-c0e197c71c8f" \
      --scope "$aiSearchResourceId" \
      --output none

    if [ $? -eq 0 ]; then
        echo "Search index data reader role assigned successfully."
    else
        echo "Failed to assign search index data reader role."
        exit 1
    fi
else
    echo "User already has the search index data reader role."
fi

# Check if the user has the Cosmos DB Built-in Data Contributor role
echo "Checking if user has the Cosmos DB Built-in Data Contributor role"
roleExists=$(az cosmosdb sql role assignment list \
    --resource-group $resource_group \
    --account-name $cosmosdb_account \
    --query "[?roleDefinitionId.ends_with(@, '00000000-0000-0000-0000-000000000002') && principalId == '$signed_user_id']" -o tsv)

# Check if the role exists
if [ -n "$roleExists" ]; then
    echo "User already has the Cosmos DB Built-in Data Contributer role."
else
    echo "User does not have the Cosmos DB Built-in Data Contributer role. Assigning the role."
    MSYS_NO_PATHCONV=1 az cosmosdb sql role assignment create \
        --resource-group $resource_group \
        --account-name $cosmosdb_account \
        --role-definition-id 00000000-0000-0000-0000-000000000002 \
        --principal-id $signed_user_id \
        --scope "/" \
        --output none
    if [ $? -eq 0 ]; then
        echo "Cosmos DB Built-in Data Contributer role assigned successfully."
    else
        echo "Failed to assign Cosmos DB Built-in Data Contributer role."
    fi
fi

# role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
#   --role "00000000-0000-0000-0000-000000000002" \
#   --scope "$cosmosdbAccountId" \
#   --assignee "$signed_user_id" \
#   --query "[].roleDefinitionId" -o tsv)

# if [ -z "$role_assignment" ]; then
#     echo "User does not have the Cosmos DB account contributor role. Assigning the role..."
#     MSYS_NO_PATHCONV=1 az role assignment create \
#       --assignee "$signed_user_id" \
#       --role "00000000-0000-0000-0000-000000000002" \
#       --scope "$cosmosdbAccountId" \
#       --output none

#     if [ $? -eq 0 ]; then
#         echo "Cosmos DB account contributor role assigned successfully."
#     else
#         echo "Failed to assign Cosmos DB account contributor role."
#         exit 1
#     fi
# else
#     echo "User already has the Cosmos DB account contributor role."
# fi

# role_assignment=$(MSYS_NO_PATHCONV=1 az cosmosdb sql role assignment list \
#   --account-name "$cosmosdb_account" \
#   --resource-group "$resource_group" \
#   --scope "$cosmosdbAccountId" \
#   --principal-id "$signed_user_id" \
#   --query "[].roleDefinitionId" -o tsv)

# if [ -z "$role_assignment" ]; then
#     echo "User does not have the Cosmos DB SQL role. Assigning the role..."
#     MSYS_NO_PATHCONV=1 az cosmosdb sql role assignment create \
#       --account-name "$cosmosdb_account" \
#       --resource-group "$resource_group" \
#       --principal-id "$signed_user_id" \
#       --role-definition-id "00000000-0000-0000-0000-000000000002" \
#       --scope "$cosmosdbAccountId" \
#       --output none

#     if [ $? -eq 0 ]; then
#         echo "Cosmos DB SQL role assigned successfully."
#     else
#         echo "Failed to assign Cosmos DB SQL role."
#         exit 1
#     fi
# else
#     echo "User already has the Cosmos DB SQL role."
# fi

# python -m venv .venv

# .venv\Scripts\activate

requirementFile="infra/scripts/data_scripts/requirements.txt"

# Download and install Python requirements
python -m pip install --upgrade pip
python -m pip install --quiet -r "$requirementFile"

# Enable public network access for required services
enable_public_access
if [ $? -ne 0 ]; then
	echo "Error: Failed to enable public network access for services."
	exit 1
fi

# python pip install -r infra/scripts/data_scripts/requirements.txt --quiet
python infra/scripts/data_scripts/01_create_products_search_index.py --ai_search_endpoint="$ai_search_endpoint" --azure_openai_endpoint="$azure_openai_endpoint" --embedding_model_name="$embedding_model_name"
python infra/scripts/data_scripts/02_create_policies_search_index.py --ai_search_endpoint="$ai_search_endpoint" --azure_openai_endpoint="$azure_openai_endpoint" --embedding_model_name="$embedding_model_name"
python infra/scripts/data_scripts/03_write_products_to_cosmos.py --cosmosdb_account="$cosmosdb_account"

echo "Network access will be restored to original settings..."