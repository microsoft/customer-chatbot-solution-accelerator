@description('The name of the resource group')
param resourceGroupName string = 'ecommerce-chat-rg'

@description('The location for all resources')
param location string = 'West US 2'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Application name prefix')
param appNamePrefix string = 'ecommerce-chat'

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
var resourceNamePrefix = '${appNamePrefix}${environment}'
var appServicePlanName = '${resourceNamePrefix}-plan'

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: skuName
    tier: skuTier
    capacity: skuCapacity
  }
  kind: 'linux'
  properties: {
    reserved: true
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    spotExpirationTime: null
    freeOfferExpirationTime: null
    hyperV: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
    zoneRedundant: false
  }
  tags: tags
}

// Outputs
output appServicePlanName string = appServicePlan.name
output appServicePlanId string = appServicePlan.id
