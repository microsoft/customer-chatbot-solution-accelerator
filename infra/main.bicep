targetScope = 'resourceGroup'

@allowed([
  'bicep'
  'avm'
  'avm-waf'
])
@description('Deployment flavor router: bicep, avm, or avm-waf')
param deploymentFlavor string = 'bicep'

@description('Optional. A unique application/solution name for all resources in this deployment. This should be 3-16 characters long.')
@minLength(3)
@maxLength(16)
param solutionName string = 'ccsa'

@maxLength(5)
@description('Optional. A unique text value for the solution.')
param solutionUniqueText string = take(uniqueString(subscription().id, resourceGroup().name, solutionName), 5)

@metadata({ azd: { type: 'location' } })
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
param location string

@allowed(['eastus2', 'francecentral', 'swedencentral'])
@metadata({
  azd:{
    type: 'location'
    usageName: [
      'OpenAI.GlobalStandard.gpt4.1-mini,50'
      'OpenAI.GlobalStandard.gpt-realtime-mini,1'
    ]
  }
})
param azureAiServiceLocation string

param secondaryLocation string = 'canadacentral'
param gptModelName string = 'gpt-4.1-mini'
param gptModelVersion string = '2025-04-14'
param azureOpenaiAPIVersion string = '2025-01-01-preview'
param azureAiAgentApiVersion string = '2025-05-01'
@allowed([
  'Standard'
  'GlobalStandard'
])
param deploymentType string = 'GlobalStandard'
param gptDeploymentCapacity int = 50
@allowed([
  'text-embedding-3-small'
])
param embeddingModel string = 'text-embedding-3-small'
@minValue(10)
param embeddingDeploymentCapacity int = 10
@minValue(1)
param gptRealtimeDeploymentCapacity int = 1

param tags resourceInput<'Microsoft.Resources/resourceGroups@2025-04-01'>.tags = {}
param enableMonitoring bool = false
param enableScalability bool = false
param enableRedundancy bool = false
param enablePrivateNetworking bool = false
@secure()
param vmAdminUsername string?
@secure()
param vmAdminPassword string?
param vmSize string = 'Standard_D2s_v5'
param containerRegistryEndpoint string = 'ccbcontainerreg.azurecr.io'
param imageTag string = 'latest_v2'
param enableTelemetry bool = true
param existingLogAnalyticsWorkspaceId string = ''
param existingFoundryProjectResourceId string = ''
@description('Tag, Created by user name')
param createdBy string = contains(deployer(), 'userPrincipalName') ? split(deployer().userPrincipalName, '@')[0] : deployer().objectId

var isAvm = deploymentFlavor == 'avm' || deploymentFlavor == 'avm-waf'
var isBicep = deploymentFlavor == 'bicep'

module avmDeployment './avm/main.bicep' = if (isAvm) {
  name: 'module-avm-${solutionName}'
  params: {
    solutionName: solutionName
    solutionUniqueText: solutionUniqueText
    location: location
    azureAiServiceLocation: azureAiServiceLocation
    secondaryLocation: secondaryLocation
    gptModelName: gptModelName
    gptModelVersion: gptModelVersion
    azureOpenaiAPIVersion: azureOpenaiAPIVersion
    azureAiAgentApiVersion: azureAiAgentApiVersion
    deploymentType: deploymentType
    gptDeploymentCapacity: gptDeploymentCapacity
    embeddingModel: embeddingModel
    embeddingDeploymentCapacity: embeddingDeploymentCapacity
    gptRealtimeDeploymentCapacity: gptRealtimeDeploymentCapacity
    tags: tags
    enableMonitoring: enableMonitoring
    enableScalability: deploymentFlavor == 'avm-waf' ? true : enableScalability
    enableRedundancy: enableRedundancy
    enablePrivateNetworking: deploymentFlavor == 'avm-waf' ? true : enablePrivateNetworking
    vmAdminUsername: vmAdminUsername
    vmAdminPassword: vmAdminPassword
    vmSize: vmSize
    containerRegistryEndpoint: containerRegistryEndpoint
    imageTag: imageTag
    enableTelemetry: enableTelemetry
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    createdBy: createdBy
  }
}

module bicepDeployment './bicep/main.bicep' = if (isBicep) {
  name: 'module-bicep-${solutionName}'
  params: {
    solutionName: solutionName
    solutionUniqueText: solutionUniqueText
    location: location
    azureAiServiceLocation: azureAiServiceLocation
    secondaryLocation: secondaryLocation
    gptModelName: gptModelName
    gptModelVersion: gptModelVersion
    azureOpenaiAPIVersion: azureOpenaiAPIVersion
    azureAiAgentApiVersion: azureAiAgentApiVersion
    deploymentType: deploymentType
    gptDeploymentCapacity: gptDeploymentCapacity
    embeddingModel: embeddingModel
    embeddingDeploymentCapacity: embeddingDeploymentCapacity
    gptRealtimeDeploymentCapacity: gptRealtimeDeploymentCapacity
    tags: tags
    enableMonitoring: enableMonitoring
    enableScalability: enableScalability
    enableRedundancy: enableRedundancy
    enablePrivateNetworking: enablePrivateNetworking
    vmAdminUsername: vmAdminUsername
    vmAdminPassword: vmAdminPassword
    vmSize: vmSize
    containerRegistryEndpoint: containerRegistryEndpoint
    imageTag: imageTag
    enableTelemetry: enableTelemetry
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    createdBy: createdBy
  }
}

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
