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
  Application: 'E-commerce Chat'
  ManagedBy: 'Bicep'
}

// Variables
var resourceNamePrefix = '${appNamePrefix}-${environment}'
var cosmosDbName = '${resourceNamePrefix}-cosmos'
var keyVaultName = '${resourceNamePrefix}-kv'
var appInsightsName = '${resourceNamePrefix}-insights'
var backendAppServiceName = '${resourceNamePrefix}-backend'
var frontendAppServiceName = '${resourceNamePrefix}-frontend'
var appServicePlanName = '${resourceNamePrefix}-plan'

// Resource Group is created separately

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
  tags: tags
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: '${resourceNamePrefix}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
  tags: tags
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2021-10-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      name: 'standard'
      family: 'A'
    }
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
  }
  tags: tags
}

// Cosmos DB Account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2021-10-15' = {
  name: cosmosDbName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    isVirtualNetworkFilterEnabled: false
    virtualNetworkRules: []
    enableCassandraConnector: false
    disableKeyBasedMetadataWriteAccess: false
    enableFreeTier: false
    capabilities: []
    enableAnalyticalStorage: false
    analyticalStorageConfiguration: {}
    createMode: 'Default'
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: 'Geo'
      }
    }
    networkAclBypass: 'None'
    networkAclBypassResourceIds: []
    disableLocalAuth: false
  }
  tags: tags
}

// Cosmos DB Database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2021-10-15' = {
  parent: cosmosDbAccount
  name: 'ecommerce-db'
  properties: {
    resource: {
      id: 'ecommerce-db'
    }
  }
}

// Cosmos DB Containers
resource productsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-10-15' = {
  parent: cosmosDatabase
  name: 'products'
  properties: {
    resource: {
      id: 'products'
      partitionKey: {
        paths: ['/category']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/id']
          }
        ]
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
    }
  }
}

resource usersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-10-15' = {
  parent: cosmosDatabase
  name: 'users'
  properties: {
    resource: {
      id: 'users'
      partitionKey: {
        paths: ['/email']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
    }
  }
}

resource chatSessionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-10-15' = {
  parent: cosmosDatabase
  name: 'chat_sessions'
  properties: {
    resource: {
      id: 'chat_sessions'
      partitionKey: {
        paths: ['/session_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
    }
  }
}

resource transactionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-10-15' = {
  parent: cosmosDatabase
  name: 'transactions'
  properties: {
    resource: {
      id: 'transactions'
      partitionKey: {
        paths: ['/user_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
    }
  }
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
  tags: tags
}

// Backend App Service
resource backendAppService 'Microsoft.Web/sites@2021-02-01' = {
  name: backendAppServiceName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'PYTHONPATH'
          value: '/home/site/wwwroot'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: '1'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'COSMOS_DB_ENDPOINT'
          value: cosmosDbAccount.properties.documentEndpoint
        }
        {
          name: 'COSMOS_DB_DATABASE_NAME'
          value: 'ecommerce-db'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
      ]
    }
    httpsOnly: true
    clientAffinityEnabled: false
  }
  tags: tags
}

// Frontend App Service
resource frontendAppService 'Microsoft.Web/sites@2021-02-01' = {
  name: frontendAppServiceName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: '1'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'VITE_API_BASE_URL'
          value: 'https://${backendAppService.properties.defaultHostName}'
        }
        {
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '18.17.0'
        }
      ]
    }
    httpsOnly: true
    clientAffinityEnabled: false
  }
  tags: tags
}

// Key Vault Secrets (will be populated by deployment script)
resource cosmosDbKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'cosmos-db-key'
  properties: {
    value: cosmosDbAccount.listKeys().primaryMasterKey
  }
}

// Outputs
output resourceGroupName string = resourceGroupName
output location string = location
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
output cosmosDbName string = cosmosDbAccount.name
output keyVaultName string = keyVault.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output backendAppServiceUrl string = 'https://${backendAppService.properties.defaultHostName}'
output frontendAppServiceUrl string = 'https://${frontendAppService.properties.defaultHostName}'
output backendAppServiceName string = backendAppService.name
output frontendAppServiceName string = frontendAppService.name
