# Cosmos DB Deployment with Seeded Data

This directory contains scripts to deploy a new Azure Cosmos DB account with pre-seeded data for local testing.

## Quick Start

### Prerequisites
- Azure CLI installed and configured
- Logged in to Azure (`az login`)
- Resource group `ecommerce-chat-rg` exists

### Deploy Cosmos DB with Data

```powershell
# Navigate to the infrastructure directory
cd infrastructure

# Run the quick deployment script
.\quick-deploy-cosmos.ps1
```

This will:
1. Create a new Cosmos DB account in the `ecommerce-chat-rg` resource group
2. Set up the correct database schema matching your backend models
3. Seed the database with:
   - 54 paint products (matching your existing data)
   - 3 sample users
   - 3 sample transactions
4. Save connection details to `cosmos-connection-string.txt`

## Manual Deployment

If you prefer to run the deployment manually:

```powershell
# Deploy with custom parameters
.\deploy-cosmos-with-data.ps1 -ResourceGroupName "ecommerce-chat-rg" -Location "West US 2" -Environment "dev"

# Deploy without seeding data
.\deploy-cosmos-with-data.ps1 -SkipSeeding
```

## Schema Details

The deployment creates the following containers with the correct partition keys:

- **products**: Partition key `/category` (matches backend models)
- **users**: Partition key `/email` (matches backend models)  
- **chat_sessions**: Partition key `/user_id` (matches backend models)
- **carts**: Partition key `/user_id` (matches backend models)
- **transactions**: Partition key `/user_id` (matches backend models)

## Seeded Data

### Products (54 items)
- Paint shades, sprayers, and accessories
- Matches your existing product data structure
- Includes proper pricing, ratings, and descriptions

### Sample Users (3 users)
- `john.doe@example.com` - John Doe
- `jane.smith@example.com` - Jane Smith  
- `bob.johnson@example.com` - Bob Johnson

### Sample Transactions (3 orders)
- Various order statuses (delivered, shipped, processing)
- Realistic pricing and tax calculations
- Complete shipping addresses and payment info

## After Deployment

1. **Update your backend configuration**:
   ```bash
   # Copy the connection details from cosmos-connection-string.txt
   # Update your backend .env file with:
   COSMOS_DB_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
   COSMOS_DB_KEY=your-cosmos-key
   COSMOS_DB_DATABASE_NAME=ecommerce_db
   ```

2. **Test the connection**:
   ```bash
   cd backend
   python -c "from app.config import has_cosmos_db_config; print('Has config:', has_cosmos_db_config())"
   ```

3. **Run your backend**:
   ```bash
   cd backend
   python app/main.py
   ```

## Troubleshooting

### Common Issues

1. **"Resource group not found"**
   - Ensure the `ecommerce-chat-rg` resource group exists
   - Check you're in the correct Azure subscription

2. **"Not logged in to Azure"**
   - Run `az login` to authenticate

3. **"Deployment failed"**
   - Check the Azure Portal for detailed error messages
   - Ensure you have sufficient permissions in the resource group

4. **"Seeding failed"**
   - Check the connection string in `cosmos-connection-string.txt`
   - Verify the Cosmos DB account is accessible

### Verification

To verify the deployment worked:

1. **Check Azure Portal**:
   - Navigate to your Cosmos DB account
   - Open Data Explorer
   - Verify containers and data are present

2. **Test API endpoints**:
   ```bash
   # Test products endpoint
   curl http://localhost:8000/api/products
   
   # Test health endpoint
   curl http://localhost:8000/health
   ```

## Cleanup

To remove the deployed resources:

```bash
# Delete the resource group (WARNING: This deletes everything!)
az group delete --name "ecommerce-chat-rg" --yes

# Or delete just the Cosmos DB account
az cosmosdb delete --name "your-cosmos-account-name" --resource-group "ecommerce-chat-rg" --yes
```

## Cost Considerations

- The Cosmos DB account uses the Standard tier
- Provisioned throughput is set to 400 RU/s per container
- Estimated cost: ~$25-30/month for all containers
- Consider switching to Serverless for lower costs during development

## Support

If you encounter issues:
1. Check the Azure Portal for detailed error messages
2. Verify your Azure permissions
3. Ensure the resource group exists and is accessible
4. Check the connection string format
