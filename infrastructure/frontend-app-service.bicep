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

@description('Backend App Service URL for API calls')
param backendAppServiceUrl string

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Application: 'E-commerce Chat Frontend'
  ManagedBy: 'Bicep'
}

// Variables
var resourceNamePrefix = '${appNamePrefix}-${environment}'
var frontendAppServiceName = '${resourceNamePrefix}-frontend'

// Frontend App Service
resource frontendAppService 'Microsoft.Web/sites@2023-01-01' = {
  name: frontendAppServiceName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlanName
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'VITE_API_URL'
          value: backendAppServiceUrl
        }
        {
          name: 'WEBSITE_USE_PLACEHOLDER'
          value: '0'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'WEBSITES_PORT'
          value: '80'
        }
        {
          name: 'WEBSITE_DISABLE_SCM_SEED'
          value: 'true'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'false'
        }
        {
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '18.19.0'
        }
      ]
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      httpLoggingEnabled: true
      logsDirectorySizeLimit: 35
      detailedErrorLoggingEnabled: true
      publishingUsername: '${frontendAppServiceName}$'
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
            backendAppServiceUrl
            'https://${frontendAppServiceName}.azurewebsites.net'
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
output frontendAppServiceName string = frontendAppService.name
output frontendAppServiceUrl string = 'https://${frontendAppService.properties.defaultHostName}'
output frontendAppServiceId string = frontendAppService.id
