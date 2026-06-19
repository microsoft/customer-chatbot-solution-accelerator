// ============================================================================
// main.bicep — Orchestrator
// Description: Pure orchestrator for Customer Chatbot Solution Accelerator
//              All resource names are derived from params — no hardcoded names.
//              This file only calls modules; no inline resource definitions.
//              Mode: Non-WAF (vanilla Bicep)
// ============================================================================
targetScope = 'resourceGroup'

// ============================================================================
// Parameters — Core
// ============================================================================

@minLength(3)
@maxLength(16)
@description('Optional. A unique application/solution name for all resources in this deployment.')
param solutionName string = 'ccsa'

@maxLength(5)
@description('Optional. A unique text suffix appended to resource names for uniqueness.')
param solutionUniqueText string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@metadata({
  azd: {
    type: 'location'
  }
})
@allowed([
  'australiaeast'
  'centralus'
  'eastasia'
  'eastus2'
  'japaneast'
  'northeurope'
  'southeastasia'
  'uksouth'
])
@description('Required. Primary Azure region for resource deployment.')
param location string

@description('Optional. Tags to apply to all resources.')
param tags object = {}

@allowed([
  'eastus2'
  'francecentral'
  'swedencentral'
])
@metadata({
  azd: {
    type: 'location'
    usageName: [
      'OpenAI.GlobalStandard.gpt4.1-mini,50'
      'OpenAI.GlobalStandard.text-embedding-3-small,10'
      'OpenAI.GlobalStandard.gpt-realtime-mini,1'
    ]
  }
})
@description('Required. Location for AI Foundry and model deployments.')
param azureAiServiceLocation string

// ============================================================================
// Parameters — AI Configuration
// ============================================================================

@allowed([
  'Standard'
  'GlobalStandard'
])
@description('Optional. GPT model deployment type.')
param deploymentType string = 'GlobalStandard'

@description('Optional. Name of the GPT model to deploy.')
param gptModelName string = 'gpt-4.1-mini'

@description('Optional. Version of the GPT model to deploy.')
param gptModelVersion string = '2025-04-14'

@minValue(10)
@description('Optional. Capacity of the GPT deployment (TPM in thousands).')
param gptDeploymentCapacity int = 50

@allowed([
  'text-embedding-3-small'
])
@description('Optional. Name of the embedding model to deploy.')
param embeddingModel string = 'text-embedding-3-small'

@minValue(10)
@description('Optional. Capacity of the embedding model deployment.')
param embeddingDeploymentCapacity int = 10

@allowed([
  'gpt-realtime-mini'
])
@description('Optional. Name of the realtime model to deploy.')
param gptRealtimeModelName string = 'gpt-realtime-mini'

@description('Optional. Version of the realtime model to deploy.')
param gptRealtimeModelVersion string = '2025-10-06'

@minValue(1)
@description('Optional. Capacity of the realtime model deployment.')
param gptRealtimeDeploymentCapacity int = 1

@description('Optional. Azure OpenAI API version.')
param azureOpenaiAPIVersion string = '2025-01-01-preview'

@description('Optional. Azure AI Agent API version.')
param azureAiAgentApiVersion string = '2025-05-01'

// ============================================================================
// Parameters — Compute
// ============================================================================

@description('Optional. Docker image tag for app deployments.')
param imageTag string = 'latest_v2'

@description('Optional. Container registry endpoint used for app images.')
param containerRegistryEndpoint string = 'ccbcontainerreg.azurecr.io'

@allowed(['F1', 'D1', 'B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3', 'P1v3', 'P1v4'])
@description('Optional. App Service Plan SKU.')
param appServicePlanSku string = 'B2'

// ============================================================================
// Parameters — Feature Flags
// ============================================================================

@description('Optional. Enable monitoring (App Insights + Log Analytics).')
param enableMonitoring bool = false

// ============================================================================
// Parameters — Existing Resources
// ============================================================================

@description('Optional. Resource ID of an existing Log Analytics workspace. Empty creates a new one when monitoring is enabled.')
param existingLogAnalyticsWorkspaceId string = ''

@description('Optional. Resource ID of an existing AI Foundry project. Empty creates a new one.')
param existingFoundryProjectResourceId string = ''

// ============================================================================
// Parameters — Identity
// ============================================================================

@allowed(['User', 'ServicePrincipal'])
@description('Optional. Principal type of the deploying user. Use ServicePrincipal for CI/CD pipelines with OIDC.')
param deployingUserPrincipalType string = 'User'

// ============================================================================
// Variables
// ============================================================================

var solutionSuffix = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueText}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

var deployerInfo = deployer()
var deployingUserPrincipalId = deployerInfo.objectId
var createdBy = contains(deployerInfo, 'userPrincipalName') ? split(deployerInfo.userPrincipalName, '@')[0] : deployerInfo.objectId
var existingTags = resourceGroup().tags ?? {}

var useExistingLogAnalytics = !empty(existingLogAnalyticsWorkspaceId)
var useExistingAIProject = !empty(existingFoundryProjectResourceId)

var aiFoundryResourceName = useExistingAIProject ? split(existingFoundryProjectResourceId, '/')[8] : 'aif-${solutionSuffix}'
var aiProjectResourceName = useExistingAIProject ? split(existingFoundryProjectResourceId, '/')[10] : 'proj-${solutionSuffix}'
var aiFoundrySubscriptionId = useExistingAIProject ? split(existingFoundryProjectResourceId, '/')[2] : subscription().subscriptionId
var aiFoundryResourceGroupName = useExistingAIProject ? split(existingFoundryProjectResourceId, '/')[4] : resourceGroup().name

var aiModelDeployments = [
  {
    name: gptModelName
    model: gptModelName
    sku: {
      name: deploymentType
      capacity: gptDeploymentCapacity
    }
    version: gptModelVersion
    raiPolicyName: 'Microsoft.Default'
  }
  {
    name: embeddingModel
    model: embeddingModel
    sku: {
      name: 'GlobalStandard'
      capacity: embeddingDeploymentCapacity
    }
    version: '1'
    raiPolicyName: 'Microsoft.Default'
  }
  {
    name: gptRealtimeModelName
    model: gptRealtimeModelName
    sku: {
      name: 'GlobalStandard'
      capacity: gptRealtimeDeploymentCapacity
    }
    version: gptRealtimeModelVersion
    raiPolicyName: 'Microsoft.Default'
  }
]

// Tags: merge existing RG tags with standard metadata
var resourceTags = union(existingTags, tags, {
  TemplateName: 'Customer Chat bot'
  CreatedBy: createdBy
  DeploymentName: deployment().name
  Type: 'Non-WAF'
})

// ============================================================================
// Resource Group Tags
// ============================================================================
resource resourceGroupTags 'Microsoft.Resources/tags@2025-04-01' = {
  name: 'default'
  properties: {
    tags: resourceTags
  }
}

// ============================================================================
// Module: Monitoring
// ============================================================================

module log_analytics './modules/monitoring/log-analytics.bicep' = if (enableMonitoring && !useExistingLogAnalytics) {
  name: take('module.log-analytics.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
  }
  scope: resourceGroup(resourceGroup().name)
}

var logAnalyticsWorkspaceResourceId = enableMonitoring
  ? (useExistingLogAnalytics ? existingLogAnalyticsWorkspaceId : log_analytics!.outputs.resourceId)
  : ''

module app_insights './modules/monitoring/app-insights.bicep' = if (enableMonitoring) {
  name: take('module.app-insights.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    workspaceResourceId: logAnalyticsWorkspaceResourceId
  }
  scope: resourceGroup(resourceGroup().name)
}

// ============================================================================
// Module: AI Services
// ============================================================================

module ai_foundry_project './modules/ai/ai-foundry-project.bicep' = if (!useExistingAIProject) {
  name: take('module.ai-foundry-project.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: azureAiServiceLocation
  }
  scope: resourceGroup(resourceGroup().name)
}

module existing_project_setup './modules/ai/existing-project-setup.bicep' = if (useExistingAIProject) {
  name: take('module.existing-project-setup.${solutionName}', 64)
  scope: resourceGroup(aiFoundrySubscriptionId, aiFoundryResourceGroupName)
  params: {
    name: aiFoundryResourceName
    projectName: aiProjectResourceName
  }
}

var aiFoundryName = useExistingAIProject ? existing_project_setup!.outputs.name : ai_foundry_project!.outputs.name
var aiProjectName = useExistingAIProject ? existing_project_setup!.outputs.projectName : ai_foundry_project!.outputs.projectName
var projectEndpoint = useExistingAIProject ? existing_project_setup!.outputs.projectEndpoint : ai_foundry_project!.outputs.projectEndpoint
var aiFoundryEndpoint = useExistingAIProject ? existing_project_setup!.outputs.endpoint : ai_foundry_project!.outputs.endpoint
var aiFoundryResourceId = useExistingAIProject ? existing_project_setup!.outputs.resourceId : ai_foundry_project!.outputs.resourceId
var aiProjectPrincipalId = useExistingAIProject ? existing_project_setup!.outputs.projectIdentityPrincipalId : ai_foundry_project!.outputs.projectIdentityPrincipalId

@batchSize(1)
module model_deployments './modules/ai/ai-foundry-model-deployment.bicep' = [for (deployment, i) in aiModelDeployments: {
  name: take('module.model-deployment-${i}.${solutionName}', 64)
  scope: resourceGroup(aiFoundrySubscriptionId, aiFoundryResourceGroupName)
  params: {
    aiServicesAccountName: aiFoundryName
    deploymentName: deployment.name
    modelName: deployment.model
    modelVersion: deployment.version
    raiPolicyName: deployment.raiPolicyName
    skuName: deployment.sku.name
    skuCapacity: deployment.sku.capacity
  }
}]

module ai_search './modules/ai/ai-search.bicep' = {
  name: take('module.ai-search.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    disableLocalAuth: false
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    networkRuleSet: {
      bypass: 'AzureServices'
    }
  }
  scope: resourceGroup(resourceGroup().name)
}

module foundry_search_connection './modules/ai/ai-foundry-connection.bicep' = {
  name: take('module.foundry-search-conn.${solutionName}', 64)
  scope: resourceGroup(aiFoundrySubscriptionId, aiFoundryResourceGroupName)
  params: {
    solutionName: solutionSuffix
    aiServicesAccountName: aiFoundryName
    projectName: aiProjectName
    connectionName: 'aifp-srch-connection-${solutionSuffix}'
    category: 'CognitiveSearch'
    target: ai_search.outputs.endpoint
    authType: 'AAD'
    metadata: {
      ApiType: 'Azure'
      ResourceId: ai_search.outputs.resourceId
    }
  }
}

// ============================================================================
// Module: Data
// ============================================================================

module cosmosDBModule './modules/data/cosmos-db-nosql.bicep' = {
  name: take('module.cosmos-db-nosql.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    name: 'cosmos-${solutionSuffix}'
    location: location
    databaseName: 'ecommerce_db'
    containers: [
      { name: 'carts', partitionKeyPath: '/user_id' }
      { name: 'chat_sessions', partitionKeyPath: '/user_id' }
      { name: 'products', partitionKeyPath: '/productId' }
      { name: 'transactions', partitionKeyPath: '/user_id' }
      { name: 'users', partitionKeyPath: '/email' }
    ]
  }
  scope: resourceGroup(resourceGroup().name)
}

// ============================================================================
// Module: Compute
// ============================================================================

var backendApiImageName = 'DOCKER|${containerRegistryEndpoint}/backend:${imageTag}'
var frontendImageName = 'DOCKER|${containerRegistryEndpoint}/frontend:${imageTag}'
var reactAppLayoutConfig = '''{
  "appConfig": {
      "CHAT_CHATHISTORY": {
        "CHAT": 70,
        "CHATHISTORY": 30
      }
    }
  }
}'''

module hostingplan './modules/compute/app-service-plan.bicep' = {
  name: take('module.app-service-plan.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    skuName: appServicePlanSku
  }
}

module backend_docker './modules/compute/app-service.bicep' = {
  name: take('module.app-service-backend.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    name: 'api-${solutionSuffix}'
    location: location
    kind: 'app,linux,container'
    serverFarmResourceId: hostingplan.outputs.resourceId
    linuxFxVersion: backendApiImageName
    healthCheckPath: '/health'
    webSocketsEnabled: true
    appSettings: {
      AZURE_OPENAI_DEPLOYMENT_MODEL: gptModelName
      AZURE_OPENAI_ENDPOINT: aiFoundryEndpoint
      AZURE_OPENAI_API_VERSION: azureOpenaiAPIVersion
      AZURE_OPENAI_RESOURCE: aiFoundryName
      AZURE_AI_AGENT_ENDPOINT: projectEndpoint
      AZURE_AI_AGENT_API_VERSION: azureAiAgentApiVersion
      AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME: gptModelName
      USE_CHAT_HISTORY_ENABLED: 'True'
      AZURE_COSMOSDB_ACCOUNT: cosmosDBModule.outputs.name
      AZURE_COSMOSDB_DATABASE: cosmosDBModule.outputs.databaseName
      AZURE_COSMOSDB_ENABLE_FEEDBACK: ''
      REACT_APP_LAYOUT_CONFIG: reactAppLayoutConfig
      AZURE_AI_SEARCH_ENDPOINT: ai_search.outputs.endpoint
      AZURE_AI_SEARCH_INDEX: 'call_transcripts_index'
      AZURE_AI_SEARCH_CONNECTION_NAME: foundry_search_connection.outputs.connectionName
      USE_AI_PROJECT_CLIENT: 'True'
      DISPLAY_CHART_DEFAULT: 'False'
      APPLICATIONINSIGHTS_CONNECTION_STRING: enableMonitoring ? app_insights!.outputs.connectionString : ''
      AZURE_BASIC_LOGGING_LEVEL: 'INFO'
      AZURE_PACKAGE_LOGGING_LEVEL: 'WARNING'
      AZURE_LOGGING_PACKAGES: ''
      DUMMY_TEST: 'True'
      SOLUTION_NAME: solutionSuffix
      APP_ENV: 'Prod'
      ALLOWED_ORIGINS_STR: 'https://app-${solutionSuffix}.azurewebsites.net'
      AZURE_FOUNDRY_ENDPOINT: projectEndpoint
      AZURE_SEARCH_ENDPOINT: ai_search.outputs.endpoint
      AZURE_SEARCH_INDEX: 'policies'
      AZURE_SEARCH_PRODUCT_INDEX: 'products'
      COSMOS_DB_DATABASE_NAME: cosmosDBModule.outputs.databaseName
      COSMOS_DB_ENDPOINT: cosmosDBModule.outputs.endpoint
      AZURE_OPENAI_DEPLOYMENT_NAME: gptModelName
      FOUNDRY_CHAT_AGENT: ''
      FOUNDRY_PRODUCT_AGENT: ''
      FOUNDRY_POLICY_AGENT: ''
      AZURE_VOICELIVE_ENDPOINT: aiFoundryEndpoint
      VOICELIVE_MODEL: gptRealtimeModelName
      VOICELIVE_VOICE: 'alloy'
      VOICELIVE_TRANSCRIBE_MODEL: 'gpt-4o-transcribe'
      VOICELIVE_VAD_SILENCE_MS: '1200'
      VOICELIVE_VAD_THRESHOLD: '0.5'
      VOICELIVE_VAD_PREFIX_PADDING_MS: '300'
    }
  }
  scope: resourceGroup(resourceGroup().name)
}

module frontend_docker './modules/compute/app-service.bicep' = {
  name: take('module.app-service-frontend.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    name: 'app-${solutionSuffix}'
    location: location
    kind: 'app,linux,container'
    serverFarmResourceId: hostingplan.outputs.resourceId
    linuxFxVersion: frontendImageName
    appSettings: {
      NODE_ENV: 'production'
      VITE_API_BASE_URL: backend_docker.outputs.appUrl
      BACKEND_API_URL: ''
    }
  }
  scope: resourceGroup(resourceGroup().name)
}

// ============================================================================
// Module: Role Assignments (centralized)
// ============================================================================

module role_assignments './modules/identity/role-assignments.bicep' = {
  name: take('module.role-assignments.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    useExistingAIProject: useExistingAIProject
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    aiFoundryResourceId: !useExistingAIProject ? aiFoundryResourceId : ''
    aiSearchResourceId: ai_search.outputs.resourceId
    aiProjectPrincipalId: aiProjectPrincipalId
    aiSearchPrincipalId: ai_search.outputs.identityPrincipalId
    deployerPrincipalId: deployingUserPrincipalId
    deployerPrincipalType: deployingUserPrincipalType
    backendAppServicePrincipalId: backend_docker.outputs.identityPrincipalId
    cosmosDbAccountName: cosmosDBModule.outputs.name
  }
  scope: resourceGroup(resourceGroup().name)
}

// ============================================================================
// Outputs
// ============================================================================

@description('Solution suffix used for naming resources.')
output SOLUTION_NAME string = solutionSuffix

@description('Name of the deployed resource group.')
output RESOURCE_GROUP_NAME string = resourceGroup().name

@description('Location of the deployed resource group.')
output RESOURCE_GROUP_LOCATION string = resourceGroup().location

@description('Application Insights instrumentation key.')
output APPINSIGHTS_INSTRUMENTATIONKEY string = enableMonitoring ? app_insights!.outputs.instrumentationKey : ''

@description('Azure AI project endpoint.')
output AZURE_AI_PROJECT_CONN_STRING string = projectEndpoint

@description('API version for Azure AI Agent service.')
output AZURE_AI_AGENT_API_VERSION string = azureAiAgentApiVersion

@description('Name of the Azure AI Foundry project.')
output AZURE_AI_PROJECT_NAME string = aiProjectName

@description('Name of the Cosmos DB account.')
output AZURE_COSMOSDB_ACCOUNT string = cosmosDBModule.outputs.name

@description('Cosmos DB endpoint URL.')
output COSMOS_DB_ENDPOINT string = cosmosDBModule.outputs.endpoint

@description('Name of the Cosmos DB database.')
output COSMOS_DB_DATABASE_NAME string = cosmosDBModule.outputs.databaseName

@description('Name of the Cosmos DB container for chat conversations.')
output AZURE_COSMOSDB_CONVERSATIONS_CONTAINER string = 'chat_sessions'

@description('Name of the Cosmos DB database (alias).')
output AZURE_COSMOSDB_DATABASE string = cosmosDBModule.outputs.databaseName

@description('Azure OpenAI GPT model deployment name.')
output AZURE_OPENAI_DEPLOYMENT_MODEL string = gptModelName

@description('Azure OpenAI embedding model name.')
output AZURE_OPENAI_EMBEDDING_MODEL string = embeddingModel

@description('Azure OpenAI embedding model deployment capacity.')
output AZURE_OPENAI_EMBEDDING_MODEL_CAPACITY int = embeddingDeploymentCapacity

@description('Azure OpenAI service endpoint URL.')
output AZURE_OPENAI_ENDPOINT string = aiFoundryEndpoint

@description('Azure OpenAI model deployment type.')
output AZURE_OPENAI_MODEL_DEPLOYMENT_TYPE string = deploymentType

@description('Azure AI Search service endpoint URL.')
output AZURE_AI_SEARCH_ENDPOINT string = ai_search.outputs.endpoint

@description('API version for Azure OpenAI service.')
output AZURE_OPENAI_API_VERSION string = azureOpenaiAPIVersion

@description('Name of the Azure OpenAI resource.')
output AZURE_OPENAI_RESOURCE string = aiFoundryName

@description('React application layout configuration JSON.')
output REACT_APP_LAYOUT_CONFIG string = reactAppLayoutConfig

@description('Flag indicating whether to use AI Project client.')
output USE_AI_PROJECT_CLIENT string = 'False'

@description('Flag indicating whether chat history is enabled.')
output USE_CHAT_HISTORY_ENABLED string = 'True'

@description('Flag indicating whether to display charts by default.')
output DISPLAY_CHART_DEFAULT string = 'False'

@description('Azure AI Agent service endpoint URL.')
output AZURE_AI_AGENT_ENDPOINT string = projectEndpoint

@description('Azure AI Foundry project endpoint URL.')
output AZURE_FOUNDRY_ENDPOINT string = projectEndpoint

@description('Azure AI Agent model deployment name.')
output AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME string = gptModelName

@description('Name of the Azure Container Registry.')
output ACR_NAME string = split(containerRegistryEndpoint, '.')[0]

@description('Container image tag for app deployments.')
output AZURE_ENV_IMAGETAG string = imageTag

@description('Name of the Azure AI Services resource.')
output AI_SERVICE_NAME string = aiFoundryName

@description('Name of the backend API App Service.')
output API_APP_NAME string = 'api-${solutionSuffix}'

@description('Principal ID of the backend system-assigned managed identity.')
output API_PID string = backend_docker.outputs.identityPrincipalId

@description('URL of the backend API application.')
output API_APP_URL string = backend_docker.outputs.appUrl

@description('URL of the frontend web application.')
output WEB_APP_URL string = frontend_docker.outputs.appUrl

@description('Application Insights connection string.')
output APPLICATIONINSIGHTS_CONNECTION_STRING string = enableMonitoring ? app_insights!.outputs.connectionString : ''

@description('Chat agent ID (set by post-deployment script)')
output AGENT_ID_CHAT string = ''

@description('Foundry chat agent name')
output FOUNDRY_CHAT_AGENT string = '<populate manually after running post-deployment create agent script>'

@description('Foundry product agent name')
output FOUNDRY_PRODUCT_AGENT string = '<populate manually after running post-deployment create agent script>'

@description('Foundry policy agent name')
output FOUNDRY_POLICY_AGENT string = '<populate manually after running post-deployment create agent script>'

@description('Resource ID of the Azure AI Foundry account.')
output AI_FOUNDRY_RESOURCE_ID string = aiFoundryResourceId

@description('Resource ID of the Azure AI Search service.')
output AI_SEARCH_SERVICE_RESOURCE_ID string = ai_search.outputs.resourceId

@description('Application environment (Production)')
output APP_ENV string = 'Prod'
