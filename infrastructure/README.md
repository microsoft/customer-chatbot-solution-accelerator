# Azure Infrastructure for E-commerce Chat Application

This directory contains the infrastructure as code (IaC) for deploying the e-commerce chat application to Azure.

## 🏗️ Architecture

The infrastructure deploys the following Azure resources:

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Resource Group                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   App Services  │  │   Cosmos DB     │  │  Key Vault  │ │
│  │                 │  │                 │  │             │ │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────┐ │ │
│  │ │  Frontend   │ │  │ │  Database   │ │  │ │ Secrets │ │ │
│  │ │  (React)    │ │  │ │  Account    │ │  │ │         │ │ │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────┘ │ │
│  │                 │  │                 │  │             │ │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │             │ │
│  │ │  Backend    │ │  │ │ Containers  │ │  │             │ │
│  │ │  (FastAPI)  │ │  │ │             │ │  │             │ │
│  │ └─────────────┘ │  │ │ • products  │ │  │             │ │
│  └─────────────────┘  │ │ • users     │ │  │             │ │
│                       │ │ • chat      │ │  │             │ │
│  ┌─────────────────┐  │ │ • trans     │ │  │             │ │
│  │  App Service    │  │ └─────────────┘ │  │             │ │
│  │  Plan (Linux)   │  │                 │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Application    │  │  Log Analytics  │  │  Azure      │ │
│  │  Insights       │  │  Workspace      │  │  OpenAI     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Files

- **`main.bicep`** - Main Bicep template defining all Azure resources
- **`parameters.json`** - Parameter values for the Bicep template
- **`deploy.ps1`** - PowerShell deployment script
- **`deploy.sh`** - Bash deployment script
- **`configure-services.ps1`** - Script to configure Azure OpenAI and Entra ID

## 🚀 Quick Start

### Prerequisites

1. **Azure CLI** installed and configured
2. **Azure subscription** with appropriate permissions
3. **PowerShell** (for Windows) or **Bash** (for Linux/Mac)

### Option 1: PowerShell (Windows)

```powershell
# 1. Navigate to infrastructure directory
cd infrastructure

# 2. Deploy infrastructure
.\deploy.ps1 -SubscriptionId "your-subscription-id"

# 3. Configure services
.\configure-services.ps1 -ResourceGroupName "ecommerce-chat-rg"
```

### Option 2: Bash (Linux/Mac)

```bash
# 1. Navigate to infrastructure directory
cd infrastructure

# 2. Make scripts executable
chmod +x deploy.sh

# 3. Deploy infrastructure
./deploy.sh --subscription-id "your-subscription-id"

# 4. Configure services (requires PowerShell Core)
pwsh configure-services.ps1 -ResourceGroupName "ecommerce-chat-rg"
```

### Option 3: Azure CLI Direct

```bash
# 1. Login to Azure
az login

# 2. Set subscription
az account set --subscription "your-subscription-id"

# 3. Create resource group
az group create --name "ecommerce-chat-rg" --location "East US"

# 4. Deploy Bicep template
az deployment group create \
  --resource-group "ecommerce-chat-rg" \
  --template-file "main.bicep" \
  --parameters "parameters.json"
```

## 🔧 Configuration

### Environment Variables

The deployment uses the following parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resourceGroupName` | Azure resource group name | `ecommerce-chat-rg` |
| `location` | Azure region | `East US` |
| `environment` | Environment name (dev/staging/prod) | `dev` |
| `appNamePrefix` | Application name prefix | `ecommerce-chat` |

### Key Vault Secrets

The following secrets are automatically configured:

| Secret Name | Description |
|-------------|-------------|
| `cosmos-db-key` | Cosmos DB primary key |
| `azure-openai-endpoint` | Azure OpenAI endpoint |
| `azure-openai-api-key` | Azure OpenAI API key |
| `azure-openai-api-version` | Azure OpenAI API version |
| `azure-client-id` | Microsoft Entra ID client ID |
| `azure-client-secret` | Microsoft Entra ID client secret |
| `azure-tenant-id` | Microsoft Entra ID tenant ID |

## 📊 Resources Created

### Core Resources

- **Resource Group**: `ecommerce-chat-rg`
- **App Service Plan**: Linux-based, Basic tier
- **App Services**: Frontend and Backend applications
- **Cosmos DB**: Database with 4 containers
- **Key Vault**: Secrets management
- **Application Insights**: Monitoring and logging

### Cosmos DB Containers

1. **`products`** - Product catalog
2. **`users`** - User profiles
3. **`chat_sessions`** - Chat messages and sessions
4. **`transactions`** - Order and transaction data

### Monitoring

- **Application Insights**: Application performance monitoring
- **Log Analytics**: Centralized logging
- **Health Checks**: Built-in health endpoints

## 🔐 Security

### Network Security

- **HTTPS Only**: All App Services enforce HTTPS
- **CORS**: Configured for frontend domains
- **Key Vault**: Centralized secrets management

### Access Control

- **RBAC**: Role-based access control for Key Vault
- **Managed Identity**: App Services use managed identities
- **Secret References**: App settings use Key Vault references

## 📈 Scaling

### Horizontal Scaling

- **App Service Plan**: Can be scaled up/down
- **Cosmos DB**: Auto-scaling enabled
- **Load Balancing**: Built-in with App Service

### Vertical Scaling

- **App Service Plan**: Can be upgraded to higher tiers
- **Cosmos DB**: Can be upgraded to higher throughput
- **Storage**: Can be increased as needed

## 🔄 CI/CD Integration

### GitHub Actions

The repository includes GitHub Actions workflows for:

- **Automated Testing**: Backend and frontend tests
- **Security Scanning**: Vulnerability scanning
- **Automated Deployment**: Deploy on push to main
- **Infrastructure Updates**: Deploy infrastructure changes

### Manual Deployment

```bash
# Deploy only infrastructure
az deployment group create \
  --resource-group "ecommerce-chat-rg" \
  --template-file "main.bicep" \
  --parameters "parameters.json"

# Deploy only backend
az webapp deployment source config-zip \
  --resource-group "ecommerce-chat-rg" \
  --name "ecommerce-chat-dev-backend" \
  --src "backend.zip"

# Deploy only frontend
az webapp deployment source config-zip \
  --resource-group "ecommerce-chat-rg" \
  --name "ecommerce-chat-dev-frontend" \
  --src "frontend.zip"
```

## 🐛 Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check Azure CLI login status
   - Verify subscription permissions
   - Check resource group exists

2. **Key Vault Access Denied**
   - Run `configure-services.ps1` to set access policies
   - Verify user has Key Vault permissions

3. **App Service Not Starting**
   - Check application logs in Azure Portal
   - Verify environment variables are set
   - Check Key Vault secret references

4. **Cosmos DB Connection Issues**
   - Verify Cosmos DB is created
   - Check connection string in Key Vault
   - Verify network access rules

### Debug Commands

```bash
# Check resource group
az group show --name "ecommerce-chat-rg"

# Check App Service status
az webapp show --name "ecommerce-chat-dev-backend" --resource-group "ecommerce-chat-rg"

# Check Key Vault secrets
az keyvault secret list --vault-name "ecommerce-chat-dev-kv"

# Check deployment logs
az deployment group list --resource-group "ecommerce-chat-rg"
```

## 📚 Additional Resources

- [Azure Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Cosmos DB Documentation](https://docs.microsoft.com/en-us/azure/cosmos-db/)
- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)

## 🆘 Support

For issues with the infrastructure:

1. Check the troubleshooting section above
2. Review Azure Portal logs and metrics
3. Check GitHub Actions workflow logs
4. Create an issue in the repository

## 🔄 Updates

To update the infrastructure:

1. Modify the Bicep template
2. Update parameters if needed
3. Run the deployment script
4. Verify changes in Azure Portal

## 📝 Notes

- The infrastructure is designed for development/staging environments
- For production, consider additional security measures
- Monitor costs regularly using Azure Cost Management
- Set up alerts for resource usage and costs