// ========== main.bicep ========== //
targetScope = 'resourceGroup'
var abbrs = loadJsonContent('./abbreviations.json')
@minLength(3)
@maxLength(20)
@description('A unique prefix for all resources in this deployment. This should be 3-20 characters long:')
param solutionName string

@description('Optional: Existing Log Analytics Workspace Resource ID')
param existingLogAnalyticsWorkspaceId string = ''

@description('Use this parameter to use an existing AI project resource ID')
param existingFoundryProjectResourceId string = ''

// @minLength(1)
// @description('Location for the Content Understanding service deployment:')
// @allowed(['swedencentral', 'australiaeast'])
// @metadata({
//   azd: {
//     type: 'location'
//   }
// })
// param contentUnderstandingLocation string = 'swedencentral'
// var contentUnderstandingLocation = ''

@minLength(1)
@description('Secondary location for databases creation(example:eastus2):')
param secondaryLocation string = 'eastus2'

@minLength(1)
@description('GPT model deployment type:')
@allowed([
  'Standard'
  'GlobalStandard'
])
param deploymentType string = 'GlobalStandard'

@description('Name of the GPT model to deploy:')
param gptModelName string = 'gpt-4o-mini'

@description('Version of the GPT model to deploy:')
param gptModelVersion string = '2024-07-18'

@description('Optional. Version of the OpenAI API.')
param azureOpenaiAPIVersion string = '2025-01-01-preview'

@description('Optional. Version of AI Agent API.')
param azureAiAgentApiVersion string = '2025-05-01'

@minValue(10)
@description('Capacity of the GPT deployment:')
// You can increase this, but capacity is limited per model/region, so you will get errors if you go over
// https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits
param gptDeploymentCapacity int = 10

@minLength(1)
@description('Name of the Text Embedding model to deploy:')
@allowed([
  'text-embedding-3-small'
])
param embeddingModel string = 'text-embedding-3-small'

@minValue(10)
@description('Capacity of the Embedding Model deployment')
param embeddingDeploymentCapacity int = 10

param imageTag string = 'latest_v2'

param chatFrontendImageRepository string = 'ccsa-chat-frontend'

param chatBackendImageRepository string = 'ccsa-chat-backend'

param ecommerceFrontendImageRepository string = 'ccsa-ecom-frontend'

param ecommerceBackendImageRepository string = 'ccsa-ecom-backend'

@metadata({ azd: { type: 'location' } })
@description('Primary Azure region (canonical id such as westus2 or display name such as West US 2).')
param location string

var solutionLocation = toLower(replace(replace(location, ' ', ''), '-', ''))

var uniqueId = toLower(uniqueString(subscription().id, solutionName, solutionLocation))

@metadata({
  azd:{
    type: 'location'
    usageName: [
      'OpenAI.GlobalStandard.gpt-4o-mini,150'
    ]
  }
})
@description('Location for AI Foundry deployment. This is the location where the AI Foundry resources will be deployed.')
param azureAiServiceLocation string

var azureAiServiceLocationCanonical = toLower(
  replace(replace(azureAiServiceLocation, ' ', ''), '-', '')
)

var secondaryLocationCanonical = toLower(
  replace(replace(secondaryLocation, ' ', ''), '-', '')
)

@description('Optional. The tags to apply to all deployed Azure resources.')
param tags object = {}

@description('Optional. created by user name')
param createdBy string = contains(deployer(), 'userPrincipalName')
  ? split(deployer().userPrincipalName, '@')[0]
  : deployer().objectId

var existingTags = resourceGroup().tags ?? {}

var solutionPrefix = 'ccb${padLeft(take(uniqueId, 12), 12, '0')}'

var chatApiWebAppName = 'api-chat-${solutionPrefix}'
var chatFeWebAppName = 'app-chat-${solutionPrefix}'
var ecomApiWebAppName = 'api-ecom-${solutionPrefix}'
var ecomFeWebAppName = 'app-ecom-${solutionPrefix}'

var acrResourceName = toLower(replace('${abbrs.containers.containerRegistry}${solutionPrefix}', '-', ''))

var deployingUserPrincipalId = deployer().objectId

var acrPullRoleDefinitionResourceId = '/subscriptions/${subscription().subscriptionId}/providers/Microsoft.Authorization/roleDefinitions/7dfe214f-a023-46bf-bd83-e861793bfb76'

// ========== Resource Group Tag ========== //
resource resourceGroupTags 'Microsoft.Resources/tags@2025-04-01' = {
  name: 'default'
  properties: {
    tags: union(
      existingTags,
      tags,
      {
        TemplateName: 'Customer Chat bot'
        Type: 'Non-WAF'
        CreatedBy: createdBy
        DeploymentName: deployment().name
      }
    )
  }
}

// ========== Managed Identity ========== //
module managedIdentityModule 'deploy_managed_identity.bicep' = {
  name: 'deploy_managed_identity'
  params: {
    miName:'${abbrs.security.managedIdentity}${solutionPrefix}'
    solutionName: solutionPrefix
    solutionLocation: solutionLocation
  }
  scope: resourceGroup(resourceGroup().name)
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrResourceName
  location: solutionLocation
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

// ==========Key Vault Module ========== //
// module kvault 'deploy_keyvault.bicep' = {
//   name: 'deploy_keyvault'
//   params: {
//     keyvaultName: '${abbrs.security.keyVault}${solutionPrefix}'
//     solutionLocation: solutionLocation
//     managedIdentityObjectId:managedIdentityModule.outputs.managedIdentityOutput.objectId
//   }
//   scope: resourceGroup(resourceGroup().name)
// }

// ==========AI Foundry and related resources ========== //
module aifoundry 'deploy_ai_foundry.bicep' = {
  name: 'deploy_ai_foundry'
  params: {
    solutionName: solutionPrefix
    solutionLocation: azureAiServiceLocationCanonical
    // keyVaultName: kvault.outputs.keyvaultName
    // cuLocation: contentUnderstandingLocation
    deploymentType: deploymentType
    gptModelName: gptModelName
    gptModelVersion: gptModelVersion
    // azureOpenaiAPIVersion: azureOpenaiAPIVersion
    gptDeploymentCapacity: gptDeploymentCapacity
    embeddingModel: embeddingModel
    embeddingDeploymentCapacity: embeddingDeploymentCapacity
    managedIdentityObjectId: managedIdentityModule.outputs.managedIdentityOutput.objectId
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    azureExistingAIProjectResourceId: existingFoundryProjectResourceId
    deployingUserPrincipalId: deployingUserPrincipalId
  }
  scope: resourceGroup(resourceGroup().name)
}


// ========== Cosmos DB module ========== //
module cosmosDBModule 'deploy_cosmos_db.bicep' = {
  name: 'deploy_cosmos_db'
  params: {
    accountName: '${abbrs.databases.cosmosDBDatabase}${solutionPrefix}'
    solutionLocation: secondaryLocationCanonical
    // keyVaultName: kvault.outputs.keyvaultName
  }
  scope: resourceGroup(resourceGroup().name)
}


module hostingplan 'deploy_app_service_plan.bicep' = {
  name: 'deploy_app_service_plan'
  params: {
    solutionLocation: solutionLocation
    HostingPlanName: '${abbrs.compute.appServicePlan}${solutionPrefix}'
  }
}

module chat_backend_docker 'deploy_backend_docker.bicep' = {
  name: 'deploy_chat_backend_docker'
  params: {
    name: chatApiWebAppName
    solutionLocation: solutionLocation
    imageTag: imageTag
    containerRegistryLoginServer: containerRegistry.properties.loginServer
    imageRepository: chatBackendImageRepository
    azdServiceName: 'chat-backend'
    appServicePlanId: hostingplan.outputs.name
    applicationInsightsId: aifoundry.outputs.applicationInsightsId
    userassignedIdentityId: managedIdentityModule.outputs.managedIdentityBackendAppOutput.id
    aiServicesName: aifoundry.outputs.aiServicesName
    azureExistingAIProjectResourceId: existingFoundryProjectResourceId
    aiSearchName: aifoundry.outputs.aiSearchName
    appSettings: {
      AZURE_OPENAI_DEPLOYMENT_MODEL: gptModelName
      AZURE_OPENAI_ENDPOINT: aifoundry.outputs.aiServicesTarget
      AZURE_OPENAI_API_VERSION: azureOpenaiAPIVersion
      AZURE_OPENAI_RESOURCE: aifoundry.outputs.aiServicesName
      AZURE_AI_AGENT_ENDPOINT: aifoundry.outputs.projectEndpoint
      AZURE_AI_AGENT_API_VERSION: azureAiAgentApiVersion
      AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME: gptModelName
      USE_CHAT_HISTORY_ENABLED: 'True'
      AZURE_COSMOSDB_ACCOUNT: cosmosDBModule.outputs.cosmosAccountName
      AZURE_COSMOSDB_CONVERSATIONS_CONTAINER: cosmosDBModule.outputs.cosmosContainerName
      AZURE_COSMOSDB_DATABASE: cosmosDBModule.outputs.cosmosDatabaseName
      AZURE_COSMOSDB_ENABLE_FEEDBACK: ''
      API_UID: managedIdentityModule.outputs.managedIdentityBackendAppOutput.clientId
      AZURE_AI_SEARCH_ENDPOINT: aifoundry.outputs.aiSearchTarget
      AZURE_AI_SEARCH_INDEX: 'call_transcripts_index'
      AZURE_AI_SEARCH_CONNECTION_NAME: aifoundry.outputs.aiSearchConnectionName
      USE_AI_PROJECT_CLIENT: 'True'
      DISPLAY_CHART_DEFAULT: 'False'
      APPLICATIONINSIGHTS_CONNECTION_STRING: aifoundry.outputs.applicationInsightsConnectionString
      DUMMY_TEST: 'True'
      SOLUTION_NAME: solutionPrefix
      APP_ENV: 'Prod'
      ALLOWED_ORIGINS_STR: 'https://${chatFeWebAppName}.azurewebsites.net,*'
      AZURE_FOUNDRY_ENDPOINT: aifoundry.outputs.projectEndpoint
      AZURE_SEARCH_ENDPOINT: aifoundry.outputs.aiSearchTarget
      AZURE_SEARCH_INDEX: 'policies'
      AZURE_SEARCH_PRODUCT_INDEX: 'products'
      COSMOS_DB_DATABASE_NAME: cosmosDBModule.outputs.cosmosDatabaseName
      COSMOS_DB_ENDPOINT: 'https://${cosmosDBModule.outputs.cosmosAccountName}.documents.azure.com:443/'
      USE_FOUNDRY_AGENTS: 'True'
      AZURE_OPENAI_DEPLOYMENT_NAME: gptModelName
      RATE_LIMIT_REQUESTS: 100
      RATE_LIMIT_WINDOW: 60
      FOUNDRY_CHAT_AGENT: ''
      FOUNDRY_PRODUCT_AGENT: ''
      FOUNDRY_POLICY_AGENT: ''
      AZURE_VOICELIVE_ENDPOINT: aifoundry.outputs.aiServicesTarget
      VOICELIVE_MODEL: 'gpt-realtime-mini'
      VOICELIVE_VOICE: 'alloy'
      VOICELIVE_TRANSCRIBE_MODEL: 'gpt-4o-transcribe'
      VOICELIVE_VAD_SILENCE_MS: '1200'
      VOICELIVE_VAD_THRESHOLD: '0.5'
      VOICELIVE_VAD_PREFIX_PADDING_MS: '300'
    }
  }
  scope: resourceGroup(resourceGroup().name)
}

module ecommerce_backend_docker 'deploy_backend_docker.bicep' = {
  name: 'deploy_ecommerce_backend_docker'
  params: {
    name: ecomApiWebAppName
    solutionLocation: solutionLocation
    imageTag: imageTag
    containerRegistryLoginServer: containerRegistry.properties.loginServer
    imageRepository: ecommerceBackendImageRepository
    azdServiceName: 'ecommerce-backend'
    appServicePlanId: hostingplan.outputs.name
    applicationInsightsId: aifoundry.outputs.applicationInsightsId
    userassignedIdentityId: managedIdentityModule.outputs.managedIdentityBackendAppOutput.id
    aiServicesName: aifoundry.outputs.aiServicesName
    azureExistingAIProjectResourceId: existingFoundryProjectResourceId
    aiSearchName: aifoundry.outputs.aiSearchName
    appSettings: {
      AZURE_OPENAI_DEPLOYMENT_MODEL: gptModelName
      AZURE_OPENAI_ENDPOINT: aifoundry.outputs.aiServicesTarget
      AZURE_OPENAI_API_VERSION: azureOpenaiAPIVersion
      AZURE_OPENAI_RESOURCE: aifoundry.outputs.aiServicesName
      AZURE_AI_AGENT_ENDPOINT: aifoundry.outputs.projectEndpoint
      AZURE_AI_AGENT_API_VERSION: azureAiAgentApiVersion
      AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME: gptModelName
      USE_CHAT_HISTORY_ENABLED: 'False'
      AZURE_COSMOSDB_ACCOUNT: cosmosDBModule.outputs.cosmosAccountName
      AZURE_COSMOSDB_CONVERSATIONS_CONTAINER: cosmosDBModule.outputs.cosmosContainerName
      AZURE_COSMOSDB_DATABASE: cosmosDBModule.outputs.cosmosDatabaseName
      AZURE_COSMOSDB_ENABLE_FEEDBACK: ''
      API_UID: managedIdentityModule.outputs.managedIdentityBackendAppOutput.clientId
      AZURE_AI_SEARCH_ENDPOINT: aifoundry.outputs.aiSearchTarget
      AZURE_AI_SEARCH_INDEX: 'call_transcripts_index'
      AZURE_AI_SEARCH_CONNECTION_NAME: aifoundry.outputs.aiSearchConnectionName
      USE_AI_PROJECT_CLIENT: 'True'
      DISPLAY_CHART_DEFAULT: 'False'
      APPLICATIONINSIGHTS_CONNECTION_STRING: aifoundry.outputs.applicationInsightsConnectionString
      DUMMY_TEST: 'True'
      SOLUTION_NAME: solutionPrefix
      APP_ENV: 'Prod'
      ALLOWED_ORIGINS_STR: 'https://${ecomFeWebAppName}.azurewebsites.net,*'
      AZURE_FOUNDRY_ENDPOINT: aifoundry.outputs.projectEndpoint
      AZURE_SEARCH_ENDPOINT: aifoundry.outputs.aiSearchTarget
      AZURE_SEARCH_INDEX: 'policies'
      AZURE_SEARCH_PRODUCT_INDEX: 'products'
      COSMOS_DB_DATABASE_NAME: cosmosDBModule.outputs.cosmosDatabaseName
      COSMOS_DB_ENDPOINT: 'https://${cosmosDBModule.outputs.cosmosAccountName}.documents.azure.com:443/'
      USE_FOUNDRY_AGENTS: 'False'
      AZURE_OPENAI_DEPLOYMENT_NAME: gptModelName
      RATE_LIMIT_REQUESTS: 100
      RATE_LIMIT_WINDOW: 60
      FOUNDRY_CHAT_AGENT: ''
      FOUNDRY_PRODUCT_AGENT: ''
      FOUNDRY_POLICY_AGENT: ''
      AZURE_VOICELIVE_ENDPOINT: aifoundry.outputs.aiServicesTarget
      VOICELIVE_MODEL: 'gpt-realtime-mini'
      VOICELIVE_VOICE: 'alloy'
      VOICELIVE_TRANSCRIBE_MODEL: 'gpt-4o-transcribe'
      VOICELIVE_VAD_SILENCE_MS: '1200'
      VOICELIVE_VAD_THRESHOLD: '0.5'
      VOICELIVE_VAD_PREFIX_PADDING_MS: '300'
    }
  }
  scope: resourceGroup(resourceGroup().name)
}

module chat_frontend_docker 'deploy_frontend_docker.bicep' = {
  name: 'deploy_chat_frontend_docker'
  params: {
    name: chatFeWebAppName
    solutionLocation: solutionLocation
    imageTag: imageTag
    containerRegistryLoginServer: containerRegistry.properties.loginServer
    imageRepository: chatFrontendImageRepository
    azdServiceName: 'chat-frontend'
    appServicePlanId: hostingplan.outputs.name
    applicationInsightsId: aifoundry.outputs.applicationInsightsId
    appSettings: {
      NODE_ENV: 'production'
      VITE_API_BASE_URL: chat_backend_docker.outputs.appUrl
    }
  }
  scope: resourceGroup(resourceGroup().name)
}

module ecommerce_frontend_docker 'deploy_frontend_docker.bicep' = {
  name: 'deploy_ecommerce_frontend_docker'
  params: {
    name: ecomFeWebAppName
    solutionLocation: solutionLocation
    imageTag: imageTag
    containerRegistryLoginServer: containerRegistry.properties.loginServer
    imageRepository: ecommerceFrontendImageRepository
    azdServiceName: 'ecommerce-frontend'
    appServicePlanId: hostingplan.outputs.name
    applicationInsightsId: aifoundry.outputs.applicationInsightsId
    appSettings: {
      NODE_ENV: 'production'
      VITE_API_BASE_URL: ecommerce_backend_docker.outputs.appUrl
    }
  }
  scope: resourceGroup(resourceGroup().name)
}

resource acrPullChatBackend 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, acrResourceName, chatApiWebAppName, 'pull')
  scope: containerRegistry
  dependsOn: [
    containerRegistry
    chat_backend_docker
  ]
  properties: {
    principalId: chat_backend_docker.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleDefinitionResourceId
  }
}

resource acrPullEcommerceBackend 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, acrResourceName, ecomApiWebAppName, 'pull')
  scope: containerRegistry
  dependsOn: [
    containerRegistry
    ecommerce_backend_docker
  ]
  properties: {
    principalId: ecommerce_backend_docker.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleDefinitionResourceId
  }
}

resource acrPullChatFrontend 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, acrResourceName, chatFeWebAppName, 'pull')
  scope: containerRegistry
  dependsOn: [
    containerRegistry
    chat_frontend_docker
  ]
  properties: {
    principalId: chat_frontend_docker.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleDefinitionResourceId
  }
}

resource acrPullEcommerceFrontend 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, acrResourceName, ecomFeWebAppName, 'pull')
  scope: containerRegistry
  dependsOn: [
    containerRegistry
    ecommerce_frontend_docker
  ]
  properties: {
    principalId: ecommerce_frontend_docker.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleDefinitionResourceId
  }
}

output SOLUTION_NAME string = solutionPrefix
output RESOURCE_GROUP_NAME string = resourceGroup().name
output RESOURCE_GROUP_LOCATION string = solutionLocation
// output AZURE_CONTENT_UNDERSTANDING_LOCATION string = contentUnderstandingLocation
output AZURE_SECONDARY_LOCATION string = secondaryLocation
output APPINSIGHTS_INSTRUMENTATIONKEY string = chat_backend_docker.outputs.appInsightInstrumentationKey
output AZURE_AI_PROJECT_CONN_STRING string = aifoundry.outputs.projectEndpoint
output AZURE_AI_AGENT_API_VERSION string = azureAiAgentApiVersion
output AZURE_AI_PROJECT_NAME string = aifoundry.outputs.aiProjectName
output AZURE_COSMOSDB_ACCOUNT string = cosmosDBModule.outputs.cosmosAccountName
output AZURE_COSMOSDB_CONVERSATIONS_CONTAINER string = cosmosDBModule.outputs.cosmosContainerName
output AZURE_COSMOSDB_DATABASE string = cosmosDBModule.outputs.cosmosDatabaseName
output AZURE_COSMOSDB_ENABLE_FEEDBACK string = 'True'
output AZURE_OPENAI_DEPLOYMENT_MODEL string = gptModelName
output AZURE_OPENAI_EMBEDDING_MODEL string = embeddingModel
output AZURE_OPENAI_EMBEDDING_MODEL_CAPACITY int = embeddingDeploymentCapacity
output AZURE_OPENAI_ENDPOINT string = aifoundry.outputs.aiServicesTarget
output AZURE_OPENAI_MODEL_DEPLOYMENT_TYPE string = deploymentType

output AZURE_AI_SEARCH_ENDPOINT string = aifoundry.outputs.aiSearchTarget


output AZURE_OPENAI_API_VERSION string = azureOpenaiAPIVersion
output AZURE_OPENAI_RESOURCE string = aifoundry.outputs.aiServicesName
output REACT_APP_LAYOUT_CONFIG string = chat_backend_docker.outputs.reactAppLayoutConfig

output API_UID string = managedIdentityModule.outputs.managedIdentityBackendAppOutput.clientId
output USE_AI_PROJECT_CLIENT string = 'False'
output USE_CHAT_HISTORY_ENABLED string = 'True'
output DISPLAY_CHART_DEFAULT string = 'False'
output AZURE_AI_AGENT_ENDPOINT string = aifoundry.outputs.projectEndpoint
output AZURE_FOUNDRY_ENDPOINT string = aifoundry.outputs.projectEndpoint
output AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME string = gptModelName
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output ACR_NAME string = containerRegistry.name
output AZURE_ENV_IMAGETAG string = imageTag

output AI_SERVICE_NAME string = aifoundry.outputs.aiServicesName
output API_APP_NAME string = chat_backend_docker.outputs.appName
output API_PID string = managedIdentityModule.outputs.managedIdentityBackendAppOutput.objectId

output API_APP_URL string = chat_backend_docker.outputs.appUrl
output WEB_APP_URL string = chat_frontend_docker.outputs.appUrl
output CHAT_API_APP_URL string = chat_backend_docker.outputs.appUrl
output CHAT_WEB_APP_URL string = chat_frontend_docker.outputs.appUrl
output ECOMMERCE_API_APP_URL string = ecommerce_backend_docker.outputs.appUrl
output ECOMMERCE_WEB_APP_URL string = ecommerce_frontend_docker.outputs.appUrl
output CHAT_API_APP_NAME string = chat_backend_docker.outputs.appName
output CHAT_WEB_APP_NAME string = chatFeWebAppName
output ECOMMERCE_API_APP_NAME string = ecommerce_backend_docker.outputs.appName
output ECOMMERCE_WEB_APP_NAME string = ecomFeWebAppName
output APPLICATIONINSIGHTS_CONNECTION_STRING string = aifoundry.outputs.applicationInsightsConnectionString
output AGENT_ID_CHAT string = ''
output FOUNDRY_CHAT_AGENT string = '<populate manually after running post-deployment create agent script>'
output FOUNDRY_PRODUCT_AGENT string = '<populate manually after running post-deployment create agent script>'
output FOUNDRY_POLICY_AGENT string = '<populate manually after running post-deployment create agent script>'

output MANAGED_IDENTITY_CLIENT_ID string = managedIdentityModule.outputs.managedIdentityOutput.clientId
output AI_FOUNDRY_RESOURCE_ID string = aifoundry.outputs.aiFoundryResourceId
output AI_SEARCH_SERVICE_RESOURCE_ID string = aifoundry.outputs.searchServiceResourceId
output COSMOS_DB_ENDPOINT string = 'https://${cosmosDBModule.outputs.cosmosAccountName}.documents.azure.com:443/'
output COSMOS_DB_DATABASE_NAME string = cosmosDBModule.outputs.cosmosDatabaseName
output APP_ENV string = 'Prod'
