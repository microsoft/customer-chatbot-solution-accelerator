# Deployment with Entra ID Authentication

This guide explains how to deploy the e-commerce chat application with Microsoft Entra ID authentication to Azure.

## Prerequisites

Before starting, ensure you have:

1. **Azure CLI** installed and logged in (`az login`)
2. **PowerShell** (Windows PowerShell 5.1+ or PowerShell Core 6+)
3. **Azure Subscription** with appropriate permissions
4. **Azure Cosmos DB** account (for data storage)
5. **Azure OpenAI** service (for chat functionality)

## Quick Start

### Option 1: Complete Automated Deployment (Recommended)

Deploy everything including the Azure App Registration automatically:

```powershell
.\deploy-with-auth-complete.ps1 `
    -ResourceGroupName "ecommerce-chat-rg" `
    -Location "West US 2" `
    -Environment "dev" `
    -AppNamePrefix "ecommerce-chat" `
    -CosmosDbEndpoint "https://your-cosmos-account.documents.azure.com:443/" `
    -CosmosDbKey "your-cosmos-key" `
    -OpenAiEndpoint "https://your-openai-service.openai.azure.com/" `
    -OpenAiApiKey "your-openai-api-key" `
    -CreateAppRegistration
```

This script will:
- Create an Azure App Registration automatically
- Deploy all infrastructure (Cosmos DB, Frontend, Backend)
- Configure authentication settings
- Update the app registration with the correct URLs after deployment
- Display all credentials you need to save

### Option 2: Use Existing App Registration

If you already have an Azure App Registration:

```powershell
.\deploy-with-auth-complete.ps1 `
    -ResourceGroupName "ecommerce-chat-rg" `
    -Location "West US 2" `
    -Environment "dev" `
    -AppNamePrefix "ecommerce-chat" `
    -AzureTenantId "your-tenant-id" `
    -AzureClientId "your-client-id" `
    -AzureClientSecret "your-client-secret" `
    -CosmosDbEndpoint "https://your-cosmos-account.documents.azure.com:443/" `
    -CosmosDbKey "your-cosmos-key" `
    -OpenAiEndpoint "https://your-openai-service.openai.azure.com/" `
    -OpenAiApiKey "your-openai-api-key"
```

### Option 3: Manual App Registration Setup

If you prefer to set up the App Registration manually first:

```powershell
# Step 1: Create app registration with placeholder URLs
.\setup-azure-app-registration.ps1 -AppName "E-commerce Chat App" -FrontendUrl "https://placeholder.azurewebsites.net"

# Step 2: Deploy with the generated credentials
.\deploy-with-auth.ps1 `
    -ResourceGroupName "ecommerce-chat-rg" `
    -Location "West US 2" `
    -Environment "dev" `
    -AppNamePrefix "ecommerce-chat" `
    -AzureTenantId "your-tenant-id" `
    -AzureClientId "your-client-id" `
    -AzureClientSecret "your-client-secret" `
    -CosmosDbEndpoint "https://your-cosmos-account.documents.azure.com:443/" `
    -CosmosDbKey "your-cosmos-key" `
    -OpenAiEndpoint "https://your-openai-service.openai.azure.com/" `
    -OpenAiApiKey "your-openai-api-key"

# Step 3: Update app registration with actual URLs (manual step in Azure Portal)
```

## Detailed Setup

### Manual Azure App Registration Setup

If you prefer to set up the App Registration manually:

1. **Go to Azure Portal** → Azure Active Directory → App registrations
2. **Click "New registration"**
3. **Configure the app:**
   - Name: "E-commerce Chat App"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: Single-page application (SPA)
   - Redirect URI: `https://your-app-name-dev-frontend.azurewebsites.net`
   - Redirect URI: `https://your-app-name-dev-frontend.azurewebsites.net/auth/callback`

4. **Configure Authentication:**
   - Platform: Single-page application (SPA)
   - Redirect URIs: Add both frontend URLs
   - Logout URL: `https://your-app-name-dev-frontend.azurewebsites.net`
   - Implicit grant: Enable ID tokens

5. **Add API Permissions:**
   - Microsoft Graph → User.Read
   - Microsoft Graph → openid
   - Microsoft Graph → profile

6. **Create Client Secret:**
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Add description and expiration
   - **Copy the secret value immediately**

7. **Grant Admin Consent:**
   - Go to "API permissions"
   - Click "Grant admin consent for [Your Organization]"

### Environment Variables

The deployment script automatically configures these environment variables:

#### Frontend (App Service)
- `VITE_API_BASE_URL`: Backend API URL
- `VITE_AZURE_CLIENT_ID`: Azure App Registration Client ID
- `VITE_AZURE_TENANT_ID`: Azure Tenant ID
- `VITE_AZURE_AUTHORITY`: Microsoft login authority URL
- `VITE_REDIRECT_URI`: Frontend callback URL
- `VITE_ENVIRONMENT`: Set to "production"

#### Backend (App Service)
- `AZURE_TENANT_ID`: Azure Tenant ID
- `AZURE_CLIENT_ID`: Azure App Registration Client ID
- `AZURE_CLIENT_SECRET`: Azure App Registration Client Secret
- `COSMOS_DB_ENDPOINT`: Cosmos DB endpoint
- `COSMOS_DB_KEY`: Cosmos DB primary key
- `COSMOS_DB_DATABASE_NAME`: Database name (ecommerce-db)
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: OpenAI deployment name
- `AZURE_OPENAI_API_VERSION`: API version (2025-01-01-preview)
- `ALLOWED_ORIGINS_STR`: Frontend URL for CORS

## Deployment Phases

The deployment script runs these phases:

### Phase 1: Cosmos DB
- Creates Cosmos DB account
- Sets up database and containers
- Configures indexing policies

### Phase 2: Frontend
- Builds React application
- Deploys to Azure App Service
- Configures Entra ID settings
- Sets up custom domain (if specified)

### Phase 3: Backend
- Builds FastAPI application
- Deploys to Azure App Service
- Configures Entra ID settings
- Sets up environment variables

### Phase 4: Integration Test
- Tests API endpoints
- Verifies authentication flow
- Checks database connectivity

## Post-Deployment Verification

After deployment, verify everything works:

1. **Open the frontend URL** in your browser
2. **Click "Login"** and authenticate with Microsoft
3. **Test the chat functionality**
4. **Add items to cart** and test checkout
5. **Check API documentation** at `https://your-backend-url/docs`

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
**Problem**: Users can't log in
**Solutions**:
- Verify redirect URIs in Azure App Registration match exactly
- Check that the app is configured as "Single-page application (SPA)"
- Ensure admin consent is granted for API permissions

#### 2. CORS Errors
**Problem**: Frontend can't call backend API
**Solutions**:
- Verify `ALLOWED_ORIGINS_STR` includes the frontend URL
- Check that the backend is running and accessible

#### 3. Token Validation Failures
**Problem**: Backend rejects authentication tokens
**Solutions**:
- Verify `AZURE_TENANT_ID` and `AZURE_CLIENT_ID` are correct
- Check that the client secret is valid and not expired
- Ensure the token audience matches the client ID

#### 4. Database Connection Issues
**Problem**: Backend can't connect to Cosmos DB
**Solutions**:
- Verify Cosmos DB endpoint and key are correct
- Check that the database and containers exist
- Ensure the Cosmos DB account is accessible

### Debug Commands

```powershell
# Check app registration
az ad app show --id $CLIENT_ID

# Check app service configuration
az webapp config appsettings list --name $APP_NAME --resource-group $RG_NAME

# Check app service logs
az webapp log tail --name $APP_NAME --resource-group $RG_NAME

# Test backend health
curl https://your-backend.azurewebsites.net/health

# Test authentication endpoint
curl https://your-backend.azurewebsites.net/api/auth/config
```

## Security Best Practices

### Production Considerations

1. **Use Certificates Instead of Secrets**:
   ```powershell
   # Generate certificate
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   
   # Upload to app registration
   az ad app credential reset --id $CLIENT_ID --cert @cert.pem
   ```

2. **Rotate Secrets Regularly**:
   - Set up secret rotation schedule
   - Monitor secret expiration dates
   - Update deployment scripts with new secrets

3. **Monitor Authentication**:
   - Enable Azure AD sign-in logs
   - Set up alerts for failed authentication attempts
   - Monitor app registration usage

4. **Network Security**:
   - Use Azure Front Door for DDoS protection
   - Configure IP restrictions if needed
   - Enable HTTPS only

## Scaling and Performance

### Horizontal Scaling
- Configure auto-scaling rules for App Services
- Use Azure Application Gateway for load balancing
- Consider Azure Container Instances for burst capacity

### Database Optimization
- Configure Cosmos DB autoscale
- Optimize query patterns
- Use appropriate consistency levels

### Caching
- Implement Redis cache for session data
- Use CDN for static assets
- Cache API responses where appropriate

## Monitoring and Logging

### Application Insights
- Enable Application Insights for both frontend and backend
- Set up custom metrics and alerts
- Monitor authentication success rates

### Log Analytics
- Configure centralized logging
- Set up log queries for troubleshooting
- Create dashboards for key metrics

## Support and Maintenance

### Regular Tasks
- Monitor application health
- Review authentication logs
- Update dependencies regularly
- Test disaster recovery procedures

### Backup and Recovery
- Configure automated backups for Cosmos DB
- Test restore procedures regularly
- Document recovery processes

## Cost Optimization

### Resource Sizing
- Right-size App Service plans
- Use reserved instances for predictable workloads
- Monitor and optimize Cosmos DB RU consumption

### Monitoring Costs
- Set up cost alerts
- Review usage patterns regularly
- Use Azure Cost Management tools

---

For additional support or questions, refer to the main project documentation or create an issue in the project repository.
