// ============================================================================
// main.bicep — Deployment Router
// Description: Routes deployment to the appropriate infrastructure flavor.
//   - 'bicep'   → Vanilla Bicep modules (Docker deployment)
//   - 'avm'     → AVM-based modules (non-WAF)
//   - 'avm-waf' → AVM-based modules with WAF-aligned features
//              (monitoring, private networking, scalability, redundancy)
// ============================================================================
targetScope = 'resourceGroup'

// ============================================================================
// Routing Parameter
// ============================================================================

@allowed(['bicep', 'avm', 'avm-waf'])
@description('Required. Deployment flavor: bicep (vanilla Docker), avm (AVM non-WAF), or avm-waf (AVM WAF-aligned).')
param deploymentFlavor string

// ============================================================================
// Parameters — Core (shared across all flavors)
// ============================================================================

@description('Optional. A unique application/solution name for all resources in this deployment. This should be 3-16 characters long.')
@minLength(3)
@maxLength(16)
param solutionName string = 'ccsa'

@maxLength(5)
@description('Optional. A unique text suffix appended to resource names for uniqueness.')
param solutionUniqueText string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@metadata({
  azd: { type: 'location' }
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
// Parameters — Monitoring & Telemetry
// ============================================================================

@description('Optional. Enable monitoring (App Insights + Log Analytics).')
param enableMonitoring bool = false

@description('Optional. Enable/Disable usage telemetry for AVM modules.')
param enableTelemetry bool = true

// ============================================================================
// Parameters — WAF-specific (private networking, scalability, redundancy)
// ============================================================================

@description('Optional. Enable private networking (VNet, private endpoints, DNS zones).')
param enablePrivateNetworking bool = false

@description('Optional. Enable scalability features (zone redundant App Service Plan).')
param enableScalability bool = false

@description('Optional. Enable redundancy (zone redundant Cosmos DB, multi-region failover).')
param enableRedundancy bool = false

@description('Optional. Secondary CosmosDB location for high availability.')
param secondaryLocation string = 'canadacentral'

@secure()
@description('Optional. VM admin username for jumpbox (required when enablePrivateNetworking is true).')
param vmAdminUsername string?

@secure()
@description('Optional. VM admin password for jumpbox (required when enablePrivateNetworking is true).')
param vmAdminPassword string?

@description('Optional. Jumpbox VM size.')
param vmSize string = 'Standard_D2s_v5'

// ============================================================================
// Derived Variables
// ============================================================================

var isAvm = deploymentFlavor == 'avm' || deploymentFlavor == 'avm-waf'
var isBicep = deploymentFlavor == 'bicep'

// ========== Bicep (vanilla) deployment ========== //
module bicepDeployment './bicep/main.bicep' = if (isBicep) {
  name: 'module-bicep-${solutionName}'
  params: {
    solutionName: solutionName
    solutionUniqueText: solutionUniqueText
    location: location
    tags: tags
    azureAiServiceLocation: azureAiServiceLocation
    deploymentType: deploymentType
    gptModelName: gptModelName
    gptModelVersion: gptModelVersion
    gptDeploymentCapacity: gptDeploymentCapacity
    embeddingModel: embeddingModel
    embeddingDeploymentCapacity: embeddingDeploymentCapacity
    gptRealtimeModelName: gptRealtimeModelName
    gptRealtimeModelVersion: gptRealtimeModelVersion
    gptRealtimeDeploymentCapacity: gptRealtimeDeploymentCapacity
    azureOpenaiAPIVersion: azureOpenaiAPIVersion
    azureAiAgentApiVersion: azureAiAgentApiVersion
    imageTag: imageTag
    containerRegistryEndpoint: containerRegistryEndpoint
    appServicePlanSku: appServicePlanSku
    enableMonitoring: enableMonitoring
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    deployingUserPrincipalType: deployingUserPrincipalType
  }
}

// ========== AVM deployment ========== //
module avmDeployment './avm/main.bicep' = if (isAvm) {
  name: 'module-avm-${solutionName}'
  params: {
    solutionName: solutionName
    solutionUniqueText: solutionUniqueText
    location: location
    tags: tags
    azureAiServiceLocation: azureAiServiceLocation
    deploymentType: deploymentType
    gptModelName: gptModelName
    gptModelVersion: gptModelVersion
    gptDeploymentCapacity: gptDeploymentCapacity
    embeddingModel: embeddingModel
    embeddingDeploymentCapacity: embeddingDeploymentCapacity
    gptRealtimeDeploymentCapacity: gptRealtimeDeploymentCapacity
    azureOpenaiAPIVersion: azureOpenaiAPIVersion
    azureAiAgentApiVersion: azureAiAgentApiVersion
    imageTag: imageTag
    containerRegistryEndpoint: containerRegistryEndpoint
    appServicePlanSku: appServicePlanSku
    enableMonitoring: enableMonitoring
    enableScalability: enableScalability
    enableRedundancy: enableRedundancy
    enablePrivateNetworking: enablePrivateNetworking
    enableTelemetry: enableTelemetry
    secondaryLocation: secondaryLocation
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    deployingUserPrincipalType: deployingUserPrincipalType
    vmAdminUsername: vmAdminUsername
    vmAdminPassword: vmAdminPassword
    vmSize: vmSize
  }
}

// ============================================================================
// Outputs (unified across flavors)
// ============================================================================

output SOLUTION_NAME string = isAvm ? avmDeployment!.outputs.SOLUTION_NAME : bicepDeployment!.outputs.SOLUTION_NAME
output RESOURCE_GROUP_NAME string = isAvm ? avmDeployment!.outputs.RESOURCE_GROUP_NAME : bicepDeployment!.outputs.RESOURCE_GROUP_NAME
output RESOURCE_GROUP_LOCATION string = isAvm ? avmDeployment!.outputs.RESOURCE_GROUP_LOCATION : bicepDeployment!.outputs.RESOURCE_GROUP_LOCATION
output ACR_NAME string = isAvm ? avmDeployment!.outputs.ACR_NAME : bicepDeployment!.outputs.ACR_NAME
output AI_SERVICE_NAME string = isAvm ? avmDeployment!.outputs.AI_SERVICE_NAME : bicepDeployment!.outputs.AI_SERVICE_NAME
output AI_FOUNDRY_RESOURCE_ID string = isAvm ? avmDeployment!.outputs.AI_FOUNDRY_RESOURCE_ID : bicepDeployment!.outputs.AI_FOUNDRY_RESOURCE_ID
output AI_SEARCH_SERVICE_RESOURCE_ID string = isAvm ? avmDeployment!.outputs.AI_SEARCH_SERVICE_RESOURCE_ID : bicepDeployment!.outputs.AI_SEARCH_SERVICE_RESOURCE_ID
output API_APP_NAME string = isAvm ? avmDeployment!.outputs.API_APP_NAME : bicepDeployment!.outputs.API_APP_NAME
output API_APP_URL string = isAvm ? avmDeployment!.outputs.API_APP_URL : bicepDeployment!.outputs.API_APP_URL
output API_PID string = isAvm ? avmDeployment!.outputs.API_PID : bicepDeployment!.outputs.API_PID
output APP_ENV string = isAvm ? avmDeployment!.outputs.APP_ENV : bicepDeployment!.outputs.APP_ENV
output APPINSIGHTS_INSTRUMENTATIONKEY string = isAvm ? avmDeployment!.outputs.APPINSIGHTS_INSTRUMENTATIONKEY : bicepDeployment!.outputs.APPINSIGHTS_INSTRUMENTATIONKEY
output APPLICATIONINSIGHTS_CONNECTION_STRING string = isAvm ? avmDeployment!.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING : bicepDeployment!.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
output AZURE_AI_AGENT_API_VERSION string = isAvm ? avmDeployment!.outputs.AZURE_AI_AGENT_API_VERSION : bicepDeployment!.outputs.AZURE_AI_AGENT_API_VERSION
output AZURE_AI_AGENT_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_AI_AGENT_ENDPOINT : bicepDeployment!.outputs.AZURE_AI_AGENT_ENDPOINT
output AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME string = isAvm ? avmDeployment!.outputs.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME : bicepDeployment!.outputs.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME
output AZURE_AI_PROJECT_CONN_STRING string = isAvm ? avmDeployment!.outputs.AZURE_AI_PROJECT_CONN_STRING : bicepDeployment!.outputs.AZURE_AI_PROJECT_CONN_STRING
output AZURE_AI_PROJECT_NAME string = isAvm ? avmDeployment!.outputs.AZURE_AI_PROJECT_NAME : bicepDeployment!.outputs.AZURE_AI_PROJECT_NAME
output AZURE_AI_SEARCH_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_AI_SEARCH_ENDPOINT : bicepDeployment!.outputs.AZURE_AI_SEARCH_ENDPOINT
output AZURE_COSMOSDB_ACCOUNT string = isAvm ? avmDeployment!.outputs.AZURE_COSMOSDB_ACCOUNT : bicepDeployment!.outputs.AZURE_COSMOSDB_ACCOUNT
output AZURE_COSMOSDB_CONVERSATIONS_CONTAINER string = isAvm ? avmDeployment!.outputs.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER : bicepDeployment!.outputs.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER
output AZURE_COSMOSDB_DATABASE string = isAvm ? avmDeployment!.outputs.AZURE_COSMOSDB_DATABASE : bicepDeployment!.outputs.AZURE_COSMOSDB_DATABASE
output AZURE_ENV_IMAGETAG string = isAvm ? avmDeployment!.outputs.AZURE_ENV_IMAGETAG : bicepDeployment!.outputs.AZURE_ENV_IMAGETAG
output AZURE_FOUNDRY_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_FOUNDRY_ENDPOINT : bicepDeployment!.outputs.AZURE_FOUNDRY_ENDPOINT
output AZURE_OPENAI_API_VERSION string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_API_VERSION : bicepDeployment!.outputs.AZURE_OPENAI_API_VERSION
output AZURE_OPENAI_DEPLOYMENT_MODEL string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_DEPLOYMENT_MODEL : bicepDeployment!.outputs.AZURE_OPENAI_DEPLOYMENT_MODEL
output AZURE_OPENAI_EMBEDDING_MODEL string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_EMBEDDING_MODEL : bicepDeployment!.outputs.AZURE_OPENAI_EMBEDDING_MODEL
output AZURE_OPENAI_EMBEDDING_MODEL_CAPACITY int = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_EMBEDDING_MODEL_CAPACITY : bicepDeployment!.outputs.AZURE_OPENAI_EMBEDDING_MODEL_CAPACITY
output AZURE_OPENAI_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_ENDPOINT : bicepDeployment!.outputs.AZURE_OPENAI_ENDPOINT
output AZURE_OPENAI_MODEL_DEPLOYMENT_TYPE string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_MODEL_DEPLOYMENT_TYPE : bicepDeployment!.outputs.AZURE_OPENAI_MODEL_DEPLOYMENT_TYPE
output AZURE_OPENAI_RESOURCE string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_RESOURCE : bicepDeployment!.outputs.AZURE_OPENAI_RESOURCE
output COSMOS_DB_DATABASE_NAME string = isAvm ? avmDeployment!.outputs.COSMOS_DB_DATABASE_NAME : bicepDeployment!.outputs.COSMOS_DB_DATABASE_NAME
output COSMOS_DB_ENDPOINT string = isAvm ? avmDeployment!.outputs.COSMOS_DB_ENDPOINT : bicepDeployment!.outputs.COSMOS_DB_ENDPOINT
output DISPLAY_CHART_DEFAULT string = isAvm ? avmDeployment!.outputs.DISPLAY_CHART_DEFAULT : bicepDeployment!.outputs.DISPLAY_CHART_DEFAULT
output FOUNDRY_CHAT_AGENT string = isAvm ? avmDeployment!.outputs.FOUNDRY_CHAT_AGENT : bicepDeployment!.outputs.FOUNDRY_CHAT_AGENT
output FOUNDRY_POLICY_AGENT string = isAvm ? avmDeployment!.outputs.FOUNDRY_POLICY_AGENT : bicepDeployment!.outputs.FOUNDRY_POLICY_AGENT
output FOUNDRY_PRODUCT_AGENT string = isAvm ? avmDeployment!.outputs.FOUNDRY_PRODUCT_AGENT : bicepDeployment!.outputs.FOUNDRY_PRODUCT_AGENT
output AGENT_ID_CHAT string = isAvm ? avmDeployment!.outputs.AGENT_ID_CHAT : bicepDeployment!.outputs.AGENT_ID_CHAT
output REACT_APP_LAYOUT_CONFIG string = isAvm ? avmDeployment!.outputs.REACT_APP_LAYOUT_CONFIG : bicepDeployment!.outputs.REACT_APP_LAYOUT_CONFIG
output USE_AI_PROJECT_CLIENT string = isAvm ? avmDeployment!.outputs.USE_AI_PROJECT_CLIENT : bicepDeployment!.outputs.USE_AI_PROJECT_CLIENT
output USE_CHAT_HISTORY_ENABLED string = isAvm ? avmDeployment!.outputs.USE_CHAT_HISTORY_ENABLED : bicepDeployment!.outputs.USE_CHAT_HISTORY_ENABLED
output WEB_APP_URL string = isAvm ? avmDeployment!.outputs.WEB_APP_URL : bicepDeployment!.outputs.WEB_APP_URL
