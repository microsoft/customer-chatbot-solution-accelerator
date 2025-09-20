# Proper React Frontend Deployment - Azure App Service

## 🎯 **Why App Service (Not Storage)**

Your React app needs App Service because it:
- Makes API calls to backend (`VITE_API_BASE_URL`)
- Uses authentication (MSAL + mock auth)
- Needs environment variables
- Requires SPA routing support
- Is a dynamic app, not static files

## 🚀 **Correct Deployment Strategy**

### **Option 1: Node.js App Service (Recommended)**

```bash
# Create App Service Plan
az appservice plan create \
    --name "frontend-plan" \
    --resource-group "ecommerce-chat-rg" \
    --location "West US 2" \
    --sku B1 \
    --is-linux

# Create Web App
az webapp create \
    --name "ecommerce-frontend-$(date +%Y%m%d)" \
    --resource-group "ecommerce-chat-rg" \
    --plan "frontend-plan" \
    --runtime "NODE:18-lts"
```

### **Option 2: Container Deployment (Better for Complex Apps)**

Your app already has a Dockerfile - this is the cleanest approach:

```bash
# Build and push to Azure Container Registry
az acr build \
    --registry "ecommerceregistry" \
    --image "frontend:latest" \
    --file "modern-e-commerce-ch/Dockerfile" \
    modern-e-commerce-ch/

# Create container-based web app
az webapp create \
    --name "ecommerce-frontend-$(date +%Y%m%d)" \
    --resource-group "ecommerce-chat-rg" \
    --plan "frontend-plan" \
    --deployment-container-image-name "ecommerceregistry.azurecr.io/frontend:latest"
```

## 🔧 **Environment Configuration**

Your app needs these environment variables:

```bash
# Set environment variables for the web app
WEBAPP_NAME="ecommerce-frontend-$(date +%Y%m%d)"

az webapp config appsettings set \
    --name $WEBAPP_NAME \
    --resource-group "ecommerce-chat-rg" \
    --settings \
    VITE_API_BASE_URL="https://your-backend-app.azurewebsites.net" \
    VITE_AZURE_CLIENT_ID="your-azure-client-id" \
    NODE_ENV="production"
```

## 📁 **Required Files Check**

Your app structure is correct:
- ✅ `package.json` with build script
- ✅ `vite.config.ts` configured
- ✅ `Dockerfile` exists
- ✅ Built files in `dist/`

## 🛠 **Complete PowerShell Script**

```powershell
# Frontend Deployment Script
param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$BackendUrl = "https://your-backend-app.azurewebsites.net"
)

$timestamp = Get-Date -Format "yyyyMMdd"
$webAppName = "ecommerce-frontend-$timestamp"
$planName = "frontend-plan"

Write-Host "🚀 Deploying React Frontend to Azure App Service"
Write-Host "Web App: $webAppName"

# Create App Service Plan (if not exists)
az appservice plan create `
    --name $planName `
    --resource-group $ResourceGroupName `
    --location $Location `
    --sku B1 `
    --is-linux

# Create Web App
az webapp create `
    --name $webAppName `
    --resource-group $ResourceGroupName `
    --plan $planName `
    --runtime "NODE:18-lts"

# Configure environment variables
az webapp config appsettings set `
    --name $webAppName `
    --resource-group $ResourceGroupName `
    --settings `
    VITE_API_BASE_URL=$BackendUrl `
    NODE_ENV="production" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"

# Deploy code
cd modern-e-commerce-ch
zip -r ../frontend-deploy.zip . -x "node_modules/*" "dist/*"
cd ..

az webapp deployment source config-zip `
    --name $webAppName `
    --resource-group $ResourceGroupName `
    --src "frontend-deploy.zip"

# Show URL
$frontendUrl = "https://$webAppName.azurewebsites.net"
Write-Host "✅ Frontend deployed: $frontendUrl"
```

## 🔄 **Integration Steps**

1. **Deploy Backend First** - Get the backend URL
2. **Update Frontend Config** - Set `VITE_API_BASE_URL` to backend URL
3. **Configure CORS** - Backend must allow frontend domain
4. **Test Authentication** - Verify MSAL configuration

## ⚠️ **Why Storage Account Won't Work**

- ❌ No environment variables
- ❌ No server-side routing for SPA
- ❌ Can't make API calls to different domains easily
- ❌ No authentication flow support
- ❌ No build process integration

Your app is a **dynamic web application**, not static files!

