#!/bin/bash
echo "Starting the data upload script"

# Variables

solutionName="$1"
aiFoundryName="$2"
backend_app_pid="$3"
backend_app_uid="$4"
app_service="$5"
resource_group="$6"
ai_search_endpoint="$7"
azure_openai_endpoint="$8"
embedding_model_name="${9}"
aiFoundryResourceId="${10}"
aiSearchResourceId="${11}"
cosmosdb_account="${12}"

# get parameters from azd env, if not provided
if [ -z "$solutionName" ]; then
    solutionName=$(azd env get-value SOLUTION_NAME)
fi

if [ -z "$aiFoundryName" ]; then
    aiFoundryName=$(azd env get-value AI_SERVICE_NAME)
fi

if [ -z "$backend_app_pid" ]; then
    backend_app_pid=$(azd env get-value API_PID)
fi

if [ -z "$backend_app_uid" ]; then
    backend_app_uid=$(azd env get-value API_UID)
fi

if [ -z "$app_service" ]; then
    app_service=$(azd env get-value API_APP_NAME)
fi

if [ -z "$resource_group" ]; then
    resource_group=$(azd env get-value RESOURCE_GROUP_NAME)
fi

if [ -z "$ai_search_endpoint" ]; then
    ai_search_endpoint=$(azd env get-value AZURE_AI_SEARCH_ENDPOINT)
fi
if [ -z "$azure_openai_endpoint" ]; then
    azure_openai_endpoint=$(azd env get-value AZURE_OPENAI_ENDPOINT)
fi

if [ -z "$embedding_model_name" ]; then
    embedding_model_name=$(azd env get-value AZURE_OPENAI_EMBEDDING_MODEL)
fi

if [ -z "$aiFoundryResourceId" ]; then
    aiFoundryResourceId=$(azd env get-value AI_FOUNDRY_RESOURCE_ID)
fi

if [ -z "$aiSearchResourceId" ]; then
    aiSearchResourceId=$(azd env get-value AI_SEARCH_SERVICE_RESOURCE_ID)
fi

if [ -z "$cosmosdb_account" ]; then
    cosmosdb_account=$(azd env get-value AZURE_COSMOSDB_ACCOUNT)
fi

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

# Check if user is logged in to Azure
echo "Checking Azure authentication..."
if az account show &> /dev/null; then
    echo "Already authenticated with Azure."
else
    # Use Azure CLI login if running locally
    echo "Authenticating with Azure CLI..."
    az login
fi

echo "Getting principal id (user or service principal)"
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

if [ "$SKIP_ROLE_ASSIGNMENT" != "true" ]; then
    echo "Checking if the principal has Search roles on the AI Search Service"
    # search service contributor role id: 7ca78c08-252a-4471-8644-bb5ff32d4ba0
    # search index data contributor role id: 8ebe5a00-799e-43f5-93ac-243d3dce84a7
    # search index data reader role id: 1407120a-92aa-4202-b7e9-c0e197c71c8f

    role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
      --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" \
      --scope "$aiSearchResourceId" \
      --assignee "$signed_user_id" \
      --query "[].roleDefinitionId" -o tsv)

    if [ -z "$role_assignment" ]; then
        echo "Principal does not have the search service contributor role. Assigning the role..."
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
        echo "Principal already has the search service contributor role."
    fi

    role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
      --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" \
      --scope "$aiSearchResourceId" \
      --assignee "$signed_user_id" \
      --query "[].roleDefinitionId" -o tsv)

    if [ -z "$role_assignment" ]; then
        echo "Principal does not have the search index data contributor role. Assigning the role..."
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
        echo "Principal already has the search index data contributor role."
    fi

    role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list \
      --role "1407120a-92aa-4202-b7e9-c0e197c71c8f" \
      --scope "$aiSearchResourceId" \
      --assignee "$signed_user_id" \
      --query "[].roleDefinitionId" -o tsv)

    if [ -z "$role_assignment" ]; then
        echo "Principal does not have the search index data reader role. Assigning the role..."
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
        echo "Principal already has the search index data reader role."
    fi
else
    echo "Skipping role assignments - assuming permissions are pre-configured"
fi

# Check if the principal has the Cosmos DB Built-in Data Contributor role
if [ "$SKIP_ROLE_ASSIGNMENT" != "true" ]; then
    echo "Checking if principal has the Cosmos DB Built-in Data Contributor role"
    roleExists=$(az cosmosdb sql role assignment list \
        --resource-group $resource_group \
        --account-name $cosmosdb_account \
        --query "[?roleDefinitionId.ends_with(@, '00000000-0000-0000-0000-000000000002') && principalId == '$signed_user_id']" -o tsv)

    # Check if the role exists
    if [ -n "$roleExists" ]; then
        echo "Principal already has the Cosmos DB Built-in Data Contributor role."
    else
        echo "Principal does not have the Cosmos DB Built-in Data Contributor role. Assigning the role."
        MSYS_NO_PATHCONV=1 az cosmosdb sql role assignment create \
            --resource-group $resource_group \
            --account-name $cosmosdb_account \
            --role-definition-id 00000000-0000-0000-0000-000000000002 \
            --principal-id $signed_user_id \
            --scope "/" \
            --output none
        if [ $? -eq 0 ]; then
            echo "Cosmos DB Built-in Data Contributor role assigned successfully."
        else
            echo "Failed to assign Cosmos DB Built-in Data Contributor role."
        fi
    fi
else
    echo "Skipping Cosmos DB role assignment - assuming permissions are pre-configured"
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