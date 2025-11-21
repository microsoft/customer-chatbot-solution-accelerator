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


# Check if user is logged in to Azure
echo "Checking Azure authentication..."
if az account show &> /dev/null; then
    echo "Already authenticated with Azure."
else
    # Use Azure CLI login if running locally
    echo "Authenticating with Azure CLI..."
    az login
fi

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


# python pip install -r infra/scripts/data_scripts/requirements.txt --quiet
python infra/scripts/data_scripts/01_create_products_search_index.py --ai_search_endpoint="$ai_search_endpoint" --azure_openai_endpoint="$azure_openai_endpoint" --embedding_model_name="$embedding_model_name"
python infra/scripts/data_scripts/02_create_policies_search_index.py --ai_search_endpoint="$ai_search_endpoint" --azure_openai_endpoint="$azure_openai_endpoint" --embedding_model_name="$embedding_model_name"
python infra/scripts/data_scripts/03_write_products_to_cosmos.py --cosmosdb_account="$cosmosdb_account"