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
  Application: 'E-commerce Chat Static Website'
  ManagedBy: 'Bicep'
}

// Variables  
var resourceNamePrefix = '${appNamePrefix}${environment}'
// Storage account names must be 3-24 chars, lowercase letters and numbers only
var storageAccountName = take(toLower(replace('${appNamePrefix}${environment}st', '-', '')), 24)

// Storage Account for Static Website
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: true
    allowSharedKeyAccess: true
  }
  tags: tags
}

// Enable static website
resource staticWebsite 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
  properties: {
    cors: {
      corsRules: [
        {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          exposedHeaders: ['*']
          maxAgeInSeconds: 86400
        }
      ]
    }
  }
}

// Outputs
output storageAccountName string = storageAccount.name
output staticWebsiteUrl string = 'https://${storageAccount.name}.z22.web.core.windows.net'
output storageAccountId string = storageAccount.id
