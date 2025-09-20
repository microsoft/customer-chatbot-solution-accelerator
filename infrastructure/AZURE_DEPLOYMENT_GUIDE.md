# Azure Deployment Guide for E-commerce Chat Application

This guide provides step-by-step instructions for deploying your React frontend and FastAPI backend to Azure using Bicep templates.

## 🏗️ Architecture Overview

The deployment creates the following Azure resources:

- **Cosmos DB Account** - NoSQL database for storing products, users, chat sessions, carts, and transactions
- **App Service Plan** - Linux-based hosting plan for both frontend and backend
- **Frontend App Service** - React/Vite application hosted on Azure
- **Backend App Service** - FastAPI application hosted on Azure

## 📋 Prerequisites

1. **Azure CLI** installed and configured
2. **PowerShell** (Windows) or **PowerShell Core** (cross-platform)
3. **Node.js** (for frontend build)
4. **Python** (for backend deployment)
5. **Azure subscription** with appropriate permissions

## 🚀 Quick Start

### Option 1: Complete Deployment (Recommended)

Run the complete deployment script that handles all phases automatically:

```powershell
# Navigate to the infrastructure directory
cd infrastructure

# Run the complete deployment
.\deploy-complete.ps1
```

### Option 2: Phase-by-Phase Deployment

If you prefer to run each phase separately:

```powershell
# Phase 1: Deploy Cosmos DB
.\deploy-phase1-cosmos.ps1

# Phase 2: Deploy Frontend
.\deploy-phase2-frontend.ps1

# Phase 3: Deploy Backend
.\deploy-phase3-backend.ps1

# Phase 4: Integration Test
.\deploy-phase4-integration.ps1
```

## 📁 File Structure

```
infrastructure/
├── bicep-templates/
│   ├── cosmos-db.bicep              # Cosmos DB configuration
│   ├── app-service-plan.bicep       # App Service Plan configuration
│   ├── frontend-app-service.bicep   # Frontend App Service configuration
│   ├── backend-app-service.bicep    # Backend App Service configuration
│   └── main-deployment.bicep        # Main orchestration template
├── deployment-scripts/
│   ├── deploy-complete.ps1          # Complete deployment script
│   ├── deploy-phase1-cosmos.ps1     # Phase 1: Cosmos DB
│   ├── deploy-phase2-frontend.ps1   # Phase 2: Frontend
│   ├── deploy-phase3-backend.ps1    # Phase 3: Backend
│   └── deploy-phase4-integration.ps1 # Phase 4: Integration test
└── AZURE_DEPLOYMENT_GUIDE.md        # This guide
```

## 🔧 Configuration

### Environment Variables

The deployment automatically configures the following environment variables:

#### Frontend (App Service)
- `VITE_API_URL` - Backend API URL
- `NODE_ENV` - Set to 'production'
- `WEBSITES_PORT` - Set to 5173

#### Backend (App Service)
- `COSMOS_DB_ENDPOINT` - Cosmos DB endpoint
- `COSMOS_DB_KEY` - Cosmos DB access key
- `COSMOS_DB_DATABASE_NAME` - Database name (ecommerce_db)
- `ALLOWED_ORIGINS` - CORS allowed origins
- `JWT_SECRET_KEY` - JWT secret for authentication
- `HOST` - Set to 0.0.0.0
- `PORT` - Set to 8000

### Customization

You can customize the deployment by modifying the script parameters:

```powershell
.\deploy-complete.ps1 -ResourceGroupName "my-rg" -Location "East US" -Environment "prod"
```

## 📊 Phase Details

### Phase 1: Cosmos DB Deployment
- Creates Cosmos DB account with unique name
- Creates database and all required containers
- Seeds initial data (products, sample transactions)
- Saves connection string for reference

### Phase 2: Frontend Deployment
- Creates App Service Plan (Linux, Basic B1)
- Deploys React/Vite frontend to App Service
- Configures build process and environment variables
- Sets up CORS for backend communication

### Phase 3: Backend Deployment
- Deploys FastAPI backend to App Service
- Configures Python runtime and dependencies
- Sets up environment variables for Cosmos DB
- Configures CORS for frontend communication

### Phase 4: Integration Test
- Tests backend health and API endpoints
- Verifies frontend accessibility
- Checks CORS configuration
- Validates database connectivity

## 🔍 Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check Azure CLI login: `az login`
   - Verify resource group permissions
   - Check for naming conflicts

2. **Frontend Not Loading**
   - Check App Service logs in Azure portal
   - Verify build process completed successfully
   - Check environment variables

3. **Backend API Errors**
   - Check App Service logs
   - Verify Cosmos DB connection
   - Check CORS configuration

4. **Database Connection Issues**
   - Verify Cosmos DB account is running
   - Check connection string and keys
   - Verify database and containers exist

### Debugging Commands

```powershell
# Check resource group
az group show --name ecommerce-chat-rg

# List App Services
az webapp list --resource-group ecommerce-chat-rg

# Check App Service logs
az webapp log tail --name <app-service-name> --resource-group ecommerce-chat-rg

# Test backend health
Invoke-RestMethod -Uri "https://<backend-url>/health"
```

## 🧪 Testing

After deployment, test your application:

1. **Frontend**: Visit the frontend URL
2. **Backend API**: Check `/health` endpoint
3. **API Documentation**: Visit `/docs` endpoint
4. **Database**: Verify data seeding worked

## 🔒 Security Considerations

- Cosmos DB keys are stored securely in App Service configuration
- CORS is configured to allow only specific origins
- HTTPS is enforced for all App Services
- JWT secrets are generated with unique values

## 💰 Cost Optimization

- Uses Basic B1 App Service Plan (shared resources)
- Cosmos DB uses provisioned throughput
- Consider upgrading to Standard tier for production

## 🚀 Production Deployment

For production deployment:

1. Change `Environment` parameter to "prod"
2. Use Standard or Premium App Service Plan
3. Configure custom domain names
4. Set up SSL certificates
5. Configure monitoring and alerts
6. Set up backup and disaster recovery

## 📞 Support

If you encounter issues:

1. Check the Azure portal for detailed error messages
2. Review App Service logs
3. Verify all prerequisites are installed
4. Check network connectivity and firewall rules

## 🎉 Success!

Once deployment is complete, you'll have:

- ✅ A fully functional e-commerce chat application
- ✅ React frontend hosted on Azure
- ✅ FastAPI backend with Cosmos DB integration
- ✅ Proper CORS configuration for communication
- ✅ Seeded data for testing

Your application URLs will be displayed at the end of the deployment process.
