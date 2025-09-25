# Example Deployment Script
# This script shows how to use the new deployment with authentication

# Example 1: Complete deployment with all parameters
Write-Host "🚀 Example 1: Complete Deployment" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

Write-Host "`nFirst, set up your Azure App Registration:" -ForegroundColor Yellow
Write-Host ".\setup-azure-app-registration.ps1 -AppName 'E-commerce Chat App' -FrontendUrl 'https://ecommerce-chat-dev-frontend.azurewebsites.net'" -ForegroundColor Cyan

Write-Host "`nThen deploy with authentication:" -ForegroundColor Yellow
Write-Host ".\deploy-with-auth.ps1 \`" -ForegroundColor Cyan
Write-Host "    -ResourceGroupName 'ecommerce-chat-rg' \`" -ForegroundColor Cyan
Write-Host "    -Location 'West US 2' \`" -ForegroundColor Cyan
Write-Host "    -Environment 'dev' \`" -ForegroundColor Cyan
Write-Host "    -AppNamePrefix 'ecommerce-chat' \`" -ForegroundColor Cyan
Write-Host "    -AzureTenantId 'your-tenant-id-here' \`" -ForegroundColor Cyan
Write-Host "    -AzureClientId 'your-client-id-here' \`" -ForegroundColor Cyan
Write-Host "    -AzureClientSecret 'your-client-secret-here' \`" -ForegroundColor Cyan
Write-Host "    -CosmosDbEndpoint 'https://your-cosmos-account.documents.azure.com:443/' \`" -ForegroundColor Cyan
Write-Host "    -CosmosDbKey 'your-cosmos-key-here' \`" -ForegroundColor Cyan
Write-Host "    -OpenAiEndpoint 'https://your-openai-service.openai.azure.com/' \`" -ForegroundColor Cyan
Write-Host "    -OpenAiApiKey 'your-openai-api-key-here' \`" -ForegroundColor Cyan
Write-Host "    -OpenAiDeploymentName 'gpt-4o-mini'" -ForegroundColor Cyan

Write-Host "`n" -ForegroundColor White

# Example 2: Skip certain phases
Write-Host "🚀 Example 2: Skip Certain Phases" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

Write-Host "`nDeploy only frontend and backend (skip Cosmos DB and integration test):" -ForegroundColor Yellow
Write-Host ".\deploy-with-auth.ps1 \`" -ForegroundColor Cyan
Write-Host "    -ResourceGroupName 'ecommerce-chat-rg' \`" -ForegroundColor Cyan
Write-Host "    -Location 'West US 2' \`" -ForegroundColor Cyan
Write-Host "    -Environment 'prod' \`" -ForegroundColor Cyan
Write-Host "    -AppNamePrefix 'ecommerce-chat' \`" -ForegroundColor Cyan
Write-Host "    -AzureTenantId 'your-tenant-id-here' \`" -ForegroundColor Cyan
Write-Host "    -AzureClientId 'your-client-id-here' \`" -ForegroundColor Cyan
Write-Host "    -AzureClientSecret 'your-client-secret-here' \`" -ForegroundColor Cyan
Write-Host "    -CosmosDbEndpoint 'https://your-cosmos-account.documents.azure.com:443/' \`" -ForegroundColor Cyan
Write-Host "    -CosmosDbKey 'your-cosmos-key-here' \`" -ForegroundColor Cyan
Write-Host "    -OpenAiEndpoint 'https://your-openai-service.openai.azure.com/' \`" -ForegroundColor Cyan
Write-Host "    -OpenAiApiKey 'your-openai-api-key-here' \`" -ForegroundColor Cyan
Write-Host "    -SkipCosmos \`" -ForegroundColor Cyan
Write-Host "    -SkipIntegration" -ForegroundColor Cyan

Write-Host "`n" -ForegroundColor White

# Example 3: Production deployment
Write-Host "🚀 Example 3: Production Deployment" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

Write-Host "`nFor production, use a more secure approach:" -ForegroundColor Yellow
Write-Host "1. Create app registration with production URLs" -ForegroundColor White
Write-Host "2. Use certificates instead of secrets" -ForegroundColor White
Write-Host "3. Configure custom domains" -ForegroundColor White
Write-Host "4. Set up monitoring and alerting" -ForegroundColor White

Write-Host "`nProduction deployment command:" -ForegroundColor Yellow
Write-Host ".\deploy-with-auth.ps1 \`" -ForegroundColor Cyan
Write-Host "    -ResourceGroupName 'ecommerce-chat-prod-rg' \`" -ForegroundColor Cyan
Write-Host "    -Location 'East US' \`" -ForegroundColor Cyan
Write-Host "    -Environment 'prod' \`" -ForegroundColor Cyan
Write-Host "    -AppNamePrefix 'ecommerce-chat' \`" -ForegroundColor Cyan
Write-Host "    -AzureTenantId 'your-tenant-id-here' \`" -ForegroundColor Cyan
Write-Host "    -AzureClientId 'your-client-id-here' \`" -ForegroundColor Cyan
Write-Host "    -AzureClientSecret 'your-client-secret-here' \`" -ForegroundColor Cyan
Write-Host "    -CosmosDbEndpoint 'https://your-cosmos-account.documents.azure.com:443/' \`" -ForegroundColor Cyan
Write-Host "    -CosmosDbKey 'your-cosmos-key-here' \`" -ForegroundColor Cyan
Write-Host "    -OpenAiEndpoint 'https://your-openai-service.openai.azure.com/' \`" -ForegroundColor Cyan
Write-Host "    -OpenAiApiKey 'your-openai-api-key-here'" -ForegroundColor Cyan

Write-Host "`n" -ForegroundColor White

# Example 4: Environment variables
Write-Host "🚀 Example 4: Using Environment Variables" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

Write-Host "`nYou can also set environment variables instead of passing parameters:" -ForegroundColor Yellow
Write-Host '$env:AZURE_TENANT_ID = "your-tenant-id-here"' -ForegroundColor Cyan
Write-Host '$env:AZURE_CLIENT_ID = "your-client-id-here"' -ForegroundColor Cyan
Write-Host '$env:AZURE_CLIENT_SECRET = "your-client-secret-here"' -ForegroundColor Cyan
Write-Host '$env:COSMOS_DB_ENDPOINT = "https://your-cosmos-account.documents.azure.com:443/"' -ForegroundColor Cyan
Write-Host '$env:COSMOS_DB_KEY = "your-cosmos-key-here"' -ForegroundColor Cyan
Write-Host '$env:AZURE_OPENAI_ENDPOINT = "https://your-openai-service.openai.azure.com/"' -ForegroundColor Cyan
Write-Host '$env:AZURE_OPENAI_API_KEY = "your-openai-api-key-here"' -ForegroundColor Cyan

Write-Host "`nThen run the deployment:" -ForegroundColor Yellow
Write-Host ".\deploy-with-auth.ps1 -ResourceGroupName 'ecommerce-chat-rg' -Location 'West US 2' -Environment 'dev' -AppNamePrefix 'ecommerce-chat'" -ForegroundColor Cyan

Write-Host "`n" -ForegroundColor White

# Example 5: Troubleshooting
Write-Host "🚀 Example 5: Troubleshooting" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green

Write-Host "`nIf deployment fails, check these common issues:" -ForegroundColor Yellow
Write-Host "1. Verify you're logged in to Azure: az login" -ForegroundColor White
Write-Host "2. Check resource group exists: az group show --name 'ecommerce-chat-rg'" -ForegroundColor White
Write-Host "3. Verify app registration exists: az ad app show --id 'your-client-id'" -ForegroundColor White
Write-Host "4. Check Cosmos DB is accessible: az cosmosdb show --name 'your-cosmos-account'" -ForegroundColor White
Write-Host "5. Verify OpenAI service: az cognitiveservices account show --name 'your-openai-service'" -ForegroundColor White

Write-Host "`nFor detailed troubleshooting, see DEPLOYMENT_WITH_AUTH.md" -ForegroundColor Yellow

Write-Host "`n✨ Ready to deploy with authentication!" -ForegroundColor Green

