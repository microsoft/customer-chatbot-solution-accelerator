@description('The name of the resource group')
param resourceGroupName string = 'ecommerce-chat-rg'

@description('The location for all resources')
param location string = 'West US 2'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Application name prefix')
param appNamePrefix string = 'ecommerce-chat'

@description('Cosmos DB account name')
param cosmosDbName string

@description('Database name')
param databaseName string = 'ecommerce_db'

@description('App Service Plan SKU')
param skuName string = 'B1'

@description('App Service Plan tier')
param skuTier string = 'Basic'

@description('App Service Plan capacity')
param skuCapacity int = 1

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Application: 'E-commerce Chat'
  ManagedBy: 'Bicep'
}

// Variables
var resourceNamePrefix = '${appNamePrefix}-${environment}'

// Deploy Cosmos DB
module cosmosDb 'cosmos-db.bicep' = {
  name: 'cosmos-db-deployment'
  params: {
    resourceGroupName: resourceGroupName
    location: location
    environment: environment
    cosmosDbName: cosmosDbName
    databaseName: databaseName
    tags: tags
  }
}

// Deploy App Service Plan
module appServicePlan 'app-service-plan.bicep' = {
  name: 'app-service-plan-deployment'
  params: {
    resourceGroupName: resourceGroupName
    location: location
    environment: environment
    appNamePrefix: appNamePrefix
    skuName: skuName
    skuTier: skuTier
    skuCapacity: skuCapacity
    tags: tags
  }
}

// Deploy Backend App Service
module backendAppService 'backend-app-service.bicep' = {
  name: 'backend-app-service-deployment'
  params: {
    resourceGroupName: resourceGroupName
    location: location
    environment: environment
    appNamePrefix: appNamePrefix
    appServicePlanName: appServicePlan.outputs.appServicePlanName
    cosmosDbEndpoint: cosmosDb.outputs.cosmosDbEndpoint
    cosmosDbKey: cosmosDb.outputs.cosmosDbKey
    databaseName: databaseName
    frontendAppServiceUrl: 'https://${resourceNamePrefix}-frontend.azurewebsites.net'
    tags: tags
  }
}

// Deploy Frontend App Service
module frontendAppService 'frontend-app-service.bicep' = {
  name: 'frontend-app-service-deployment'
  params: {
    resourceGroupName: resourceGroupName
    location: location
    environment: environment
    appNamePrefix: appNamePrefix
    appServicePlanName: appServicePlan.outputs.appServicePlanName
    backendAppServiceUrl: backendAppService.outputs.backendAppServiceUrl
    tags: tags
  }
}

// Outputs
output resourceGroupName string = resourceGroupName
output location string = location
output environment string = environment

// Cosmos DB outputs
output cosmosDbEndpoint string = cosmosDb.outputs.cosmosDbEndpoint
output cosmosDbName string = cosmosDb.outputs.cosmosDbName
output cosmosDbKey string = cosmosDb.outputs.cosmosDbKey
output databaseName string = cosmosDb.outputs.databaseName

// App Service Plan outputs
output appServicePlanName string = appServicePlan.outputs.appServicePlanName
output appServicePlanId string = appServicePlan.outputs.appServicePlanId

// Backend outputs
output backendAppServiceName string = backendAppService.outputs.backendAppServiceName
output backendAppServiceUrl string = backendAppService.outputs.backendAppServiceUrl
output backendAppServiceId string = backendAppService.outputs.backendAppServiceId

// Frontend outputs
output frontendAppServiceName string = frontendAppService.outputs.frontendAppServiceName
output frontendAppServiceUrl string = frontendAppService.outputs.frontendAppServiceUrl
output frontendAppServiceId string = frontendAppService.outputs.frontendAppServiceId

// Connection information
output connectionInfo object = {
  cosmosDb: {
    endpoint: cosmosDb.outputs.cosmosDbEndpoint
    key: cosmosDb.outputs.cosmosDbKey
    database: cosmosDb.outputs.databaseName
  }
  backend: {
    url: backendAppService.outputs.backendAppServiceUrl
    name: backendAppService.outputs.backendAppServiceName
  }
  frontend: {
    url: frontendAppService.outputs.frontendAppServiceUrl
    name: frontendAppService.outputs.frontendAppServiceName
  }
}
