# React Frontend Deployment Plan - Azure

## 📋 **Frontend Analysis**

**Your App:**
- **Framework:** React 19 + TypeScript + Vite
- **Build System:** Vite 6.3.5
- **Styling:** TailwindCSS 4.1.11
- **Build Command:** `tsc -b --noCheck && vite build`
- **Output:** Static files in `dist/` folder
- **Current Status:** Built files exist in `dist/` (index.html, CSS, JS)

## 🎯 **Recommended Deployment Strategy**

**Azure Storage Static Website** - The right tool for React apps.

### Why This Approach:
- ✅ **Perfect for React:** Designed for static files
- ✅ **No servers needed:** Direct file serving
- ✅ **Cost effective:** Pennies per month
- ✅ **Fast:** Global CDN available
- ✅ **Reliable:** No container startup issues
- ✅ **Simple:** Uses your existing `dist/` files

## 🚀 **Step-by-Step Deployment**

### **Prerequisites**
```bash
# Ensure you're logged in
az login

# Verify you have built files
cd modern-e-commerce-ch
ls dist/  # Should show: index.html, assets/
```

### **Step 1: Create Storage Account**
```bash
# Set variables
RESOURCE_GROUP="ecommerce-chat-rg"
LOCATION="West US 2"
STORAGE_NAME="frontend$(date +%Y%m%d)"  # Creates unique name

# Create storage account
az storage account create \
    --name $STORAGE_NAME \
    --resource-group $RESOURCE_GROUP \
    --location "$LOCATION" \
    --sku Standard_LRS \
    --kind StorageV2 \
    --access-tier Hot \
    --allow-blob-public-access true
```

### **Step 2: Enable Static Website**
```bash
# Enable static website hosting
az storage blob service-properties update \
    --account-name $STORAGE_NAME \
    --auth-mode login \
    --static-website true \
    --index-document index.html \
    --404-document index.html
```

### **Step 3: Upload Your Built Files**
```bash
# Upload all files from dist/ to $web container
az storage blob upload-batch \
    --account-name $STORAGE_NAME \
    --auth-mode login \
    --destination '$web' \
    --source modern-e-commerce-ch/dist/ \
    --overwrite
```

### **Step 4: Get Your URL**
```bash
# Get the static website URL
echo "Your React app is live at:"
echo "https://$STORAGE_NAME.z22.web.core.windows.net"
```

## 📝 **Complete PowerShell Script**

```powershell
# Frontend Deployment Script
param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2"
)

# Generate unique storage name
$timestamp = Get-Date -Format "yyyyMMdd"
$storageAccountName = "frontend$timestamp"

Write-Host "🚀 Deploying React Frontend to Azure Storage"
Write-Host "Storage Account: $storageAccountName"

# Create storage account
az storage account create `
    --name $storageAccountName `
    --resource-group $ResourceGroupName `
    --location $Location `
    --sku Standard_LRS `
    --kind StorageV2 `
    --access-tier Hot `
    --allow-blob-public-access true

# Enable static website
az storage blob service-properties update `
    --account-name $storageAccountName `
    --auth-mode login `
    --static-website true `
    --index-document index.html `
    --404-document index.html

# Upload files
az storage blob upload-batch `
    --account-name $storageAccountName `
    --auth-mode login `
    --destination '$web' `
    --source "modern-e-commerce-ch\dist" `
    --overwrite

# Show URL
$frontendUrl = "https://$storageAccountName.z22.web.core.windows.net"
Write-Host "✅ Frontend deployed: $frontendUrl"
```

## 🔧 **Alternative: Azure Static Web Apps**

If you prefer Static Web Apps (more features but more complex):

```bash
# Create Static Web App
az staticwebapp create \
    --name "ecommerce-frontend" \
    --resource-group $RESOURCE_GROUP \
    --location "West US 2" \
    --sku Free

# Get deployment token
TOKEN=$(az staticwebapp secrets list \
    --name "ecommerce-frontend" \
    --resource-group $RESOURCE_GROUP \
    --query "properties.apiKey" -o tsv)

# Deploy using SWA CLI
npx @azure/static-web-apps-cli deploy modern-e-commerce-ch/dist/ --deployment-token $TOKEN
```

## ⚠️ **What NOT to Do**

- ❌ **Don't use App Service** for static files (overkill)
- ❌ **Don't run `npm run dev`** in production (dev server)
- ❌ **Don't create Express.js servers** for static files
- ❌ **Don't use containers** for React static files

## 🎯 **Expected Results**

After deployment:
- **URL:** `https://frontend[timestamp].z22.web.core.windows.net`
- **Load Time:** < 2 seconds globally
- **Cost:** ~$0.01-0.10/month
- **Uptime:** 99.9%+
- **Features:** Your full React app with routing

## 🔄 **Updates**

To update your app:
1. Run `npm run build` locally
2. Re-upload files:
   ```bash
   az storage blob upload-batch \
       --account-name $STORAGE_NAME \
       --auth-mode login \
       --destination '$web' \
       --source modern-e-commerce-ch/dist/ \
       --overwrite
   ```

## 📊 **Integration with Phase Plan**

- **Phase 1:** Cosmos DB ✅
- **Phase 2:** Frontend (This deployment) 
- **Phase 3:** Backend API (App Service)
- **Phase 4:** Integration testing

Your frontend will be ready for Phase 3 backend integration with proper CORS configuration.
