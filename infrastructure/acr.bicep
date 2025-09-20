@description('The name of the resource group')
param resourceGroupName string = 'ecommerce-chat-rg'

@description('The location for all resources')
param location string = 'West US 2'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Application name prefix')
param appNamePrefix string = 'ecommerce-chat'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Application: 'E-commerce Chat ACR'
  ManagedBy: 'Bicep'
}

// Variables
var resourceNamePrefix = '${appNamePrefix}${environment}'
var acrName = '${resourceNamePrefix}acr'

// Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
  tags: tags
}

// Outputs
output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
output acrId string = acr.id
