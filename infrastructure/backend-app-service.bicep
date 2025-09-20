@description('The name of the resource group')
param resourceGroupName string = 'ecommerce-chat-rg'

@description('The location for all resources')
param location string = 'West US 2'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Application name prefix')
param appNamePrefix string = 'ecommerce-chat'

@description('App Service Plan name')
param appServicePlanName string

@description('Cosmos DB endpoint')
param cosmosDbEndpoint string

@description('Cosmos DB key')
param cosmosDbKey string

@description('Database name')
param databaseName string = 'ecommerce_db'

@description('Frontend App Service URL for CORS')
param frontendAppServiceUrl string

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Application: 'E-commerce Chat Backend'
  ManagedBy: 'Bicep'
}

// Variables
var resourceNamePrefix = '${appNamePrefix}-${environment}'
var backendAppServiceName = '${resourceNamePrefix}-backend'

// Backend App Service
resource backendAppService 'Microsoft.Web/sites@2023-01-01' = {
  name: backendAppServiceName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlanName
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
          value: cosmosDbEndpoint
        }
        {
          name: 'COSMOS_DB_KEY'
          value: cosmosDbKey
        }
        {
          name: 'COSMOS_DB_DATABASE_NAME'
          value: databaseName
        }
        {
          name: 'PYTHON_VERSION'
          value: '3.11'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'WEBSITE_USE_PLACEHOLDER'
          value: '0'
        }
        {
          name: 'DEBUG'
          value: 'false'
        }
        {
          name: 'HOST'
          value: '0.0.0.0'
        }
        {
          name: 'PORT'
          value: '8000'
        }
        {
          name: 'ALLOWED_ORIGINS'
          value: '${frontendAppServiceUrl},https://${backendAppServiceName}.azurewebsites.net'
        }
        {
          name: 'JWT_SECRET_KEY'
          value: 'your-secret-key-change-in-production-${uniqueString(resourceGroup().id)}'
        }
        {
          name: 'JWT_ALGORITHM'
          value: 'HS256'
        }
        {
          name: 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES'
          value: '30'
        }
        {
          name: 'RATE_LIMIT_REQUESTS'
          value: '100'
        }
        {
          name: 'RATE_LIMIT_WINDOW'
          value: '60'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: 'https://testmodle.openai.azure.com/'
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: 'your_openai_api_key_here'
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: '2025-01-01-preview'
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
          value: 'gpt-4o-mini'
        }
      ]
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      httpLoggingEnabled: true
      logsDirectorySizeLimit: 35
      detailedErrorLoggingEnabled: true
      publishingUsername: '${backendAppServiceName}$'
      scmType: 'None'
      use32BitWorkerProcess: false
      webSocketsEnabled: false
      managedPipelineMode: 'Integrated'
      virtualApplications: [
        {
          virtualPath: '/'
          physicalPath: 'site\\wwwroot'
          preloadEnabled: true
        }
      ]
      loadBalancing: 'LeastRequests'
      experiments: {
        rampUpRules: []
      }
      autoHealEnabled: false
      vnetRouteAllEnabled: false
      vnetPrivatePortsCount: 0
      publicNetworkAccess: 'Enabled'
      keyVaultReferenceIdentity: 'SystemAssigned'
      acrUseManagedIdentityCreds: false
      scmMinTlsVersion: '1.2'
      cors: {
        allowedOrigins: [
          frontendAppServiceUrl
          'https://${backendAppServiceName}.azurewebsites.net'
        ]
        supportCredentials: true
      }
    }
    httpsOnly: true
    clientAffinityEnabled: false
    clientCertEnabled: false
    clientCertMode: 'Required'
    clientCertExclusionPaths: ''
    hostNamesDisabled: false
    redundancyMode: 'None'
    storageAccountRequired: false
    keyVaultReferenceIdentity: 'SystemAssigned'
    publicNetworkAccess: 'Enabled'
    virtualNetworkSubnetId: null
    vnetContentShareEnabled: false
    vnetImagePullEnabled: false
    vnetRouteAllEnabled: false
  }
  tags: tags
}

// Outputs
output backendAppServiceName string = backendAppService.name
output backendAppServiceUrl string = 'https://${backendAppService.properties.defaultHostName}'
output backendAppServiceId string = backendAppService.id
