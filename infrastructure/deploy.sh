#!/bin/bash

# Azure Infrastructure Deployment Script
# This script deploys the e-commerce chat application infrastructure to Azure

set -e

# Default values
RESOURCE_GROUP_NAME="ecommerce-chat-rg"
LOCATION="East US"
ENVIRONMENT="dev"
APP_NAME_PREFIX="ecommerce-chat"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --subscription-id)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        --resource-group)
            RESOURCE_GROUP_NAME="$2"
            shift 2
            ;;
        --location)
            LOCATION="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --app-name-prefix)
            APP_NAME_PREFIX="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --subscription-id <subscription-id> [options]"
            echo "Options:"
            echo "  --subscription-id    Azure subscription ID (required)"
            echo "  --resource-group     Resource group name (default: ecommerce-chat-rg)"
            echo "  --location          Azure location (default: East US)"
            echo "  --environment       Environment name (default: dev)"
            echo "  --app-name-prefix   Application name prefix (default: ecommerce-chat)"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Check required parameters
if [ -z "$SUBSCRIPTION_ID" ]; then
    echo "Error: --subscription-id is required"
    exit 1
fi

echo "🚀 Starting Azure Infrastructure Deployment..."
echo "Subscription ID: $SUBSCRIPTION_ID"
echo "Resource Group: $RESOURCE_GROUP_NAME"
echo "Location: $LOCATION"
echo "Environment: $ENVIRONMENT"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed. Please install it first."
    echo "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure (if not already logged in)
echo "🔐 Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "Not logged in. Please log in to Azure..."
    az login
fi
echo "✅ Successfully logged in to Azure"

# Set subscription
echo "📋 Setting subscription..."
az account set --subscription "$SUBSCRIPTION_ID"
echo "✅ Subscription set to: $SUBSCRIPTION_ID"

# Create resource group if it doesn't exist
echo "📦 Creating resource group..."
if ! az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
    az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION"
    echo "✅ Resource group created: $RESOURCE_GROUP_NAME"
else
    echo "✅ Resource group already exists: $RESOURCE_GROUP_NAME"
fi

# Deploy Bicep template
echo "🏗️ Deploying Bicep template..."
DEPLOYMENT_NAME="ecommerce-chat-deployment-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --template-file "main.bicep" \
    --parameters "parameters.json" \
    --name "$DEPLOYMENT_NAME" \
    --verbose

echo "✅ Bicep template deployed successfully!"
echo "Deployment Name: $DEPLOYMENT_NAME"

# Display outputs
echo "📊 Deployment Outputs:"
az deployment group show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --query "properties.outputs" \
    --output table

# Configure Key Vault access policies
echo "🔑 Configuring Key Vault access policies..."
KEY_VAULT_NAME="$APP_NAME_PREFIX-$ENVIRONMENT-kv"
CURRENT_USER=$(az account show --query user.name --output tsv)

# Get the current user's object ID
USER_OBJECT_ID=$(az ad user show --id "$CURRENT_USER" --query id --output tsv)

# Set Key Vault access policy
az keyvault set-policy \
    --name "$KEY_VAULT_NAME" \
    --object-id "$USER_OBJECT_ID" \
    --secret-permissions get set list delete \
    --key-permissions get list create delete update import backup restore recover purge

echo "✅ Key Vault access policies configured"

# Display next steps
echo ""
echo "🎉 Infrastructure deployment completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Configure Azure OpenAI Service:"
echo "   - Go to Azure Portal > Create Resource > Azure OpenAI"
echo "   - Create a new Azure OpenAI resource"
echo "   - Deploy GPT-4o model"
echo "   - Add secrets to Key Vault"
echo ""
echo "2. Configure Microsoft Entra ID:"
echo "   - Go to Azure Portal > Azure Active Directory > App registrations"
echo "   - Create new app registration"
echo "   - Add secrets to Key Vault"
echo ""
echo "3. Deploy Application Code:"
echo "   - Use Azure CLI or Azure DevOps to deploy frontend and backend"
echo "   - Configure app settings with Key Vault references"
echo ""
echo "4. Test the Application:"
echo "   - Frontend: https://$APP_NAME_PREFIX-$ENVIRONMENT-frontend.azurewebsites.net"
echo "   - Backend: https://$APP_NAME_PREFIX-$ENVIRONMENT-backend.azurewebsites.net"
echo "   - API Docs: https://$APP_NAME_PREFIX-$ENVIRONMENT-backend.azurewebsites.net/docs"
echo ""
echo "🔗 Useful Links:"
echo "Azure Portal: https://portal.azure.com"
echo "Resource Group: https://portal.azure.com/#@/resource/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"
echo ""
echo "✨ Happy coding!"