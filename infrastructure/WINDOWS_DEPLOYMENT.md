# Windows Deployment Guide

This guide provides comprehensive instructions for deploying the e-commerce chat application on Windows.

## 🖥️ Windows Deployment Options

You have **4 different ways** to deploy on Windows:

### Option 1: PowerShell (Recommended)
**Best for**: Most Windows users, full Azure PowerShell integration

```powershell
# 1. Navigate to infrastructure directory
cd infrastructure

# 2. Deploy infrastructure
.\deploy.ps1 -SubscriptionId "your-subscription-id"

# 3. Configure services
.\configure-services.ps1 -ResourceGroupName "ecommerce-chat-rg"
```

### Option 2: Windows Batch File
**Best for**: Users who prefer traditional Windows batch files

```cmd
# 1. Navigate to infrastructure directory
cd infrastructure

# 2. Deploy infrastructure
deploy.bat --subscription-id "your-subscription-id"

# 3. Configure services (requires PowerShell)
powershell -ExecutionPolicy Bypass -File configure-services.ps1 -ResourceGroupName "ecommerce-chat-rg"
```

### Option 3: WSL (Windows Subsystem for Linux)
**Best for**: Developers who prefer Linux tools

```bash
# 1. Install WSL (if not already installed)
wsl --install

# 2. Open WSL terminal
wsl

# 3. Navigate to infrastructure directory
cd /mnt/c/Users/your-username/OneDrive\ -\ Microsoft/Documents/GitHub/customer-chatbot-solution-accelerator/infrastructure

# 4. Make scripts executable
chmod +x deploy.sh

# 5. Deploy infrastructure
./deploy.sh --subscription-id "your-subscription-id"

# 6. Configure services
pwsh configure-services.ps1 -ResourceGroupName "ecommerce-chat-rg"
```

### Option 4: Azure CLI Direct
**Best for**: Quick deployments, CI/CD pipelines

```cmd
# 1. Login to Azure
az login

# 2. Set subscription
az account set --subscription "your-subscription-id"

# 3. Create resource group
az group create --name "ecommerce-chat-rg" --location "East US"

# 4. Deploy Bicep template
az deployment group create ^
  --resource-group "ecommerce-chat-rg" ^
  --template-file "main.bicep" ^
  --parameters "parameters.json"
```

## 📋 Prerequisites

### Required Software

1. **Azure CLI** (Latest version)
   - Download: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows
   - Verify: `az --version`

2. **PowerShell** (5.1 or later)
   - Windows 10/11: Pre-installed
   - Verify: `$PSVersionTable.PSVersion`

3. **Git** (For cloning repository)
   - Download: https://git-scm.com/download/win
   - Verify: `git --version`

### Optional Software

4. **WSL** (For Linux compatibility)
   - Install: `wsl --install` in PowerShell as Administrator
   - Verify: `wsl --list --verbose`

5. **PowerShell Core** (For cross-platform compatibility)
   - Download: https://github.com/PowerShell/PowerShell/releases
   - Verify: `pwsh --version`

## 🔧 Setup Instructions

### Step 1: Install Azure CLI

1. Download the Azure CLI installer from the official website
2. Run the installer as Administrator
3. Follow the installation wizard
4. Restart your command prompt/PowerShell
5. Verify installation: `az --version`

### Step 2: Login to Azure

```powershell
# Login to Azure
az login

# List available subscriptions
az account list --output table

# Set your subscription (replace with your subscription ID)
az account set --subscription "your-subscription-id"
```

### Step 3: Clone Repository

```cmd
# Clone the repository
git clone https://github.com/your-username/customer-chatbot-solution-accelerator.git

# Navigate to the project directory
cd customer-chatbot-solution-accelerator
```

### Step 4: Deploy Infrastructure

Choose one of the deployment methods above based on your preference.

## 🚀 Deployment Process

### Phase 1: Infrastructure Deployment

1. **Resource Group Creation**
   - Creates Azure resource group
   - Sets up basic Azure resources

2. **Bicep Template Deployment**
   - Deploys all Azure resources
   - Configures networking and security

3. **Key Vault Setup**
   - Creates Azure Key Vault
   - Configures access policies

### Phase 2: Service Configuration

1. **Azure OpenAI Setup**
   - Creates Azure OpenAI service
   - Deploys GPT-4o model
   - Stores API keys in Key Vault

2. **Microsoft Entra ID Configuration**
   - Creates app registration
   - Generates client secrets
   - Configures authentication

3. **App Service Configuration**
   - Updates app settings
   - Links to Key Vault secrets
   - Configures CORS and security

## 🔍 Verification

### Check Deployment Status

```powershell
# Check resource group
az group show --name "ecommerce-chat-rg"

# Check App Services
az webapp list --resource-group "ecommerce-chat-rg" --output table

# Check Key Vault
az keyvault list --resource-group "ecommerce-chat-rg" --output table

# Check Cosmos DB
az cosmosdb list --resource-group "ecommerce-chat-rg" --output table
```

### Test Application Endpoints

1. **Frontend**: https://ecommerce-chat-dev-frontend.azurewebsites.net
2. **Backend**: https://ecommerce-chat-dev-backend.azurewebsites.net
3. **API Docs**: https://ecommerce-chat-dev-backend.azurewebsites.net/docs

## 🐛 Troubleshooting

### Common Issues

#### 1. Azure CLI Not Found
```cmd
# Solution: Add Azure CLI to PATH
# Or reinstall Azure CLI
```

#### 2. PowerShell Execution Policy
```powershell
# Solution: Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. Permission Denied
```powershell
# Solution: Run as Administrator
# Or check Azure permissions
```

#### 4. Resource Already Exists
```powershell
# Solution: Use different names or delete existing resources
az group delete --name "ecommerce-chat-rg" --yes
```

### Debug Commands

```powershell
# Check Azure login status
az account show

# Check subscription
az account list --output table

# Check resource group
az group show --name "ecommerce-chat-rg"

# Check deployment logs
az deployment group list --resource-group "ecommerce-chat-rg"

# Check App Service logs
az webapp log tail --name "ecommerce-chat-dev-backend" --resource-group "ecommerce-chat-rg"
```

## 📊 Resource Costs

### Estimated Monthly Costs (East US)

| Resource | Tier | Cost (USD) |
|----------|------|------------|
| App Service Plan | Basic B1 | ~$13 |
| Cosmos DB | 400 RU/s | ~$24 |
| Key Vault | Standard | ~$1 |
| Application Insights | Basic | ~$2 |
| **Total** | | **~$40/month** |

### Cost Optimization

1. **Use Free Tier** where possible
2. **Stop resources** when not in use
3. **Monitor costs** with Azure Cost Management
4. **Set up alerts** for spending limits

## 🔐 Security Considerations

### Windows-Specific Security

1. **Execution Policy**: Set appropriate PowerShell execution policy
2. **User Permissions**: Run with minimal required permissions
3. **Credential Storage**: Use Windows Credential Manager
4. **Network Security**: Configure Windows Firewall if needed

### Azure Security

1. **RBAC**: Use role-based access control
2. **Key Vault**: Store all secrets in Key Vault
3. **Managed Identity**: Use managed identities for App Services
4. **HTTPS**: Enforce HTTPS for all endpoints

## 📚 Additional Resources

### Windows-Specific Documentation

- [Azure CLI for Windows](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows)
- [PowerShell on Windows](https://docs.microsoft.com/en-us/powershell/scripting/overview)
- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)

### Azure Documentation

- [Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Cosmos DB](https://docs.microsoft.com/en-us/azure/cosmos-db/)
- [Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/)

## 🆘 Support

### Getting Help

1. **Check logs**: Use Azure Portal or CLI commands
2. **Review documentation**: Check this guide and Azure docs
3. **Community support**: GitHub Issues or Stack Overflow
4. **Microsoft support**: Azure support plans

### Useful Commands

```powershell
# Get help for any Azure CLI command
az [command] --help

# Get help for PowerShell cmdlets
Get-Help [cmdlet-name] -Full

# Check Azure CLI version
az --version

# Check PowerShell version
$PSVersionTable.PSVersion
```

## 🔄 Updates and Maintenance

### Updating Infrastructure

1. **Modify Bicep templates**
2. **Update parameters**
3. **Run deployment script**
4. **Verify changes**

### Updating Application

1. **Deploy new code**
2. **Update app settings**
3. **Test functionality**
4. **Monitor performance**

---

**Happy deploying on Windows! 🚀**
