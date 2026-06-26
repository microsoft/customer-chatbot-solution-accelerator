// ============================================================================
// main.bicep — Orchestrator (AVM)
// Description: Pure orchestrator for Customer Chatbot Solution Accelerator
//              All resource names are derived from params — no hardcoded names.
//              This file only calls modules; no inline resource definitions
//              (except role assignments that AVM modules handle via params).
//              Mode: AVM (supports both non-WAF and WAF via feature flags)
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
  'centralus'
  'southindia'
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

@description('Deployment scenario: ecommerce, healthcare, or banking')
@allowed([
  'ecommerce'
  'healthcare'
  'banking'
])
param deploymentScenario string = 'ecommerce'

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
@description('Optional. App Service Plan SKU (non-WAF). WAF overrides to P1v3.')
param appServicePlanSku string = 'B2'

// ============================================================================
// Parameters — Feature Flags (WAF alignment)
// ============================================================================

@description('Optional. Enable monitoring (App Insights + Log Analytics).')
param enableMonitoring bool = false

@description('Optional. Enable scalability for applicable resources (WAF).')
param enableScalability bool = false

@description('Optional. Enable redundancy for applicable resources (WAF).')
param enableRedundancy bool = false

@description('Optional. Enable private networking for applicable resources (WAF).')
param enablePrivateNetworking bool = false

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
// Parameters — WAF: Private Networking
// ============================================================================

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
// Parameters — Telemetry
// ============================================================================

@description('Optional. Enable/Disable usage telemetry for AVM modules.')
param enableTelemetry bool = true

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

// WAF: Replica regions for Log Analytics replication
var replicaRegionPairs = {
  australiaeast: 'australiasoutheast'
  centralus: 'westus'
  eastasia: 'japaneast'
  eastus: 'centralus'
  eastus2: 'centralus'
  japaneast: 'eastasia'
  northeurope: 'westeurope'
  southeastasia: 'eastasia'
  uksouth: 'westeurope'
  westeurope: 'northeurope'
}
var replicaLocation = replicaRegionPairs[location]

// WAF: Private DNS zones for private endpoints
var privateDnsZones = [
  'privatelink.cognitiveservices.azure.com'
  'privatelink.openai.azure.com'
  'privatelink.services.ai.azure.com'
  'privatelink.documents.azure.com'
  'privatelink.search.windows.net'
  'privatelink.azurewebsites.net'
]
var dnsZoneIndex = {
  cognitiveServices: 0
  openAI: 1
  aiServices: 2
  cosmosDb: 3
  search: 4
  webApp: 5
}

// DNS Zone indices for AI-related zones (excluded when using existing Foundry)
var aiRelatedDnsZoneIndices = [
  dnsZoneIndex.cognitiveServices
  dnsZoneIndex.openAI
  dnsZoneIndex.aiServices
]

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

// WAF: Compute SKU override
var effectiveAppServicePlanSku = enableScalability || enableRedundancy ? 'P1v3' : appServicePlanSku

// WAF: Diagnostic settings (applied to all resources when monitoring enabled)
var monitoringDiagnosticSettings = enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : []

// Tags: merge existing RG tags with standard metadata
var resourceTags = union(existingTags, tags, {
  TemplateName: 'Customer Chat bot'
  CreatedBy: createdBy
  DeploymentName: deployment().name
  Type: enablePrivateNetworking ? 'WAF' : 'Non-WAF'
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

resource existingLogAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2025-07-01' existing = if (useExistingLogAnalytics) {
  name: split(existingLogAnalyticsWorkspaceId, '/')[8]
  scope: resourceGroup(split(existingLogAnalyticsWorkspaceId, '/')[2], split(existingLogAnalyticsWorkspaceId, '/')[4])
}

module log_analytics './modules/monitoring/log-analytics.bicep' = if (enableMonitoring && !useExistingLogAnalytics) {
  name: take('module.log-analytics.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    retentionInDays: 365
    publicNetworkAccessForIngestion: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    publicNetworkAccessForQuery: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    enableReplication: enableRedundancy
    replicationLocation: enableRedundancy ? replicaLocation : ''
    dailyQuotaGb: enableRedundancy ? '150' : ''
    dataSources: enablePrivateNetworking ? [
      {
        tags: tags
        eventLogName: 'Application'
        eventTypes: [
          {
            eventType: 'Error'
          }
          {
            eventType: 'Warning'
          }
          {
            eventType: 'Information'
          }
        ]
        kind: 'WindowsEvent'
        name: 'applicationEvent'
      }
      {
        counterName: '% Processor Time'
        instanceName: '*'
        intervalSeconds: 60
        kind: 'WindowsPerformanceCounter'
        name: 'windowsPerfCounter1'
        objectName: 'Processor'
      }
      {
        kind: 'IISLogs'
        name: 'sampleIISLog1'
        state: 'OnPremiseEnabled'
      }
    ] : []
  }
}

var logAnalyticsWorkspaceResourceId = enableMonitoring
  ? (useExistingLogAnalytics ? existingLogAnalyticsWorkspace!.id : log_analytics!.outputs.resourceId)
  : ''
var logAnalyticsWorkspaceName = enableMonitoring
  ? (useExistingLogAnalytics ? existingLogAnalyticsWorkspace!.name : log_analytics!.outputs.name)
  : ''

module app_insights './modules/monitoring/app-insights.bicep' = if (enableMonitoring) {
  name: take('module.app-insights.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    tags: tags
    workspaceResourceId: logAnalyticsWorkspaceResourceId
    enableTelemetry: enableTelemetry
  }
}

// WAF: Data collection rules use the Log Analytics workspace location
var dataCollectionRulesLocation = useExistingLogAnalytics
  ? existingLogAnalyticsWorkspace!.location
  : (enableMonitoring ? log_analytics!.outputs.location : location)

// ============================================================================
// Module: Networking (WAF — conditional on enablePrivateNetworking)
// ============================================================================

module virtualNetwork './modules/networking/virtual-network.bicep' = if (enablePrivateNetworking) {
  name: take('module.virtual-network.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    addressPrefixes: ['10.0.0.0/8']
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceResourceId
    resourceSuffix: solutionSuffix
  }
}

module bastionHost './modules/networking/bastion-host.bicep' = if (enablePrivateNetworking) {
  name: take('module.bastion-host.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
    publicIPDiagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    scaleUnits: 2
  }
}

module maintenanceConfiguration './modules/compute/maintenance-configuration.bicep' = if (enablePrivateNetworking) {
  name: take('module.maintenance-configuration.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

module windowsVmDataCollectionRules './modules/monitoring/data-collection-rule.bicep' = if (enablePrivateNetworking && enableMonitoring) {
  name: take('module.data-collection-rule.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: dataCollectionRulesLocation
    tags: tags
    enableTelemetry: enableTelemetry
    logAnalyticsWorkspaceResourceId: logAnalyticsWorkspaceResourceId
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
  }
}

var virtualMachineAvailabilityZone = 1

module proximityPlacementGroup './modules/compute/proximity-placement-group.bicep' = if (enablePrivateNetworking) {
  name: take('module.proximity-placement-group.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    availabilityZone: virtualMachineAvailabilityZone
    vmSizes: [vmSize]
  }
}

module virtualMachine './modules/compute/virtual-machine.bicep' = if (enablePrivateNetworking) {
  name: take('module.virtual-machine.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    vmSize: vmSize
    availabilityZone: virtualMachineAvailabilityZone
    adminUsername: vmAdminUsername ?? 'testvmuser'
    adminPassword: vmAdminPassword ?? 'Vm!${uniqueString(subscription().subscriptionId, solutionName)}${guid(subscription().subscriptionId, solutionName, 'vm-admin-password')}'
    subnetResourceId: virtualNetwork!.outputs.administrationSubnetResourceId
    deployingUserPrincipalId: deployingUserPrincipalId
    deployingUserPrincipalType: deployingUserPrincipalType
    roleAssignments: [
      {
        roleDefinitionIdOrName: '1c0163c0-47e6-4577-8991-ea5c82e286e4'
        principalId: deployingUserPrincipalId
        principalType: deployingUserPrincipalType
      }
    ]
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    maintenanceConfigurationResourceId: maintenanceConfiguration!.outputs.resourceId
    proximityPlacementGroupResourceId: proximityPlacementGroup!.outputs.resourceId
    extensionMonitoringAgentConfig: enableMonitoring ? {
      dataCollectionRuleAssociations: [
        {
          dataCollectionRuleResourceId: windowsVmDataCollectionRules!.outputs.resourceId
          name: 'send-${logAnalyticsWorkspaceName}'
        }
      ]
      enabled: true
      tags: tags
    } : null
  }
}

@batchSize(5)
module privateDnsZoneDeployments './modules/networking/private-dns-zone.bicep' = [for (zone, i) in privateDnsZones: if (enablePrivateNetworking && (!useExistingAIProject || !contains(aiRelatedDnsZoneIndices, i))) {
  name: take('module.private-dns-zone.${split(zone, '.')[1]}.${solutionName}', 64)
  params: {
    name: zone
    tags: tags
    enableTelemetry: enableTelemetry
    virtualNetworkLinks: [
      {
        name: take('vnetlink-${virtualNetwork!.outputs.name}-${split(zone, '.')[1]}', 80)
        virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
      }
    ]
  }
}]

// ============================================================================
// Module: AI Services
// ============================================================================

module ai_foundry_project './modules/ai/ai-foundry-project.bicep' = if (!useExistingAIProject) {
  name: take('module.ai-foundry-project.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: azureAiServiceLocation
    tags: tags
    enableTelemetry: enableTelemetry
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    diagnosticSettings: monitoringDiagnosticSettings
    roleAssignments: [
      {
        roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Foundry User
        principalId: deployingUserPrincipalId
        principalType: deployingUserPrincipalType
      }
      {
        roleDefinitionIdOrName: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
        principalId: deployingUserPrincipalId
        principalType: deployingUserPrincipalType
      }
    ]
  }
}

module aiFoundryPrivateEndpoint './modules/networking/private-endpoint.bicep' = if (enablePrivateNetworking && !useExistingAIProject) {
  name: take('module.private-endpoint-ai-foundry.${solutionName}', 64)
  params: {
    name: 'pep-${ai_foundry_project!.outputs.name}'
    location: location
    tags: tags
    customNetworkInterfaceName: 'nic-${ai_foundry_project!.outputs.name}'
    subnetResourceId: virtualNetwork!.outputs.backendSubnetResourceId
    privateLinkServiceConnections: [
      {
        name: 'pep-${ai_foundry_project!.outputs.name}-connection'
        properties: {
          privateLinkServiceId: ai_foundry_project!.outputs.resourceId
          groupIds: ['account']
        }
      }
    ]
    privateDnsZoneGroup: {
      privateDnsZoneGroupConfigs: [
        {
          name: 'ai-services-dns-zone-cognitiveservices'
          privateDnsZoneResourceId: privateDnsZoneDeployments[dnsZoneIndex.cognitiveServices]!.outputs.resourceId
        }
        {
          name: 'ai-services-dns-zone-openai'
          privateDnsZoneResourceId: privateDnsZoneDeployments[dnsZoneIndex.openAI]!.outputs.resourceId
        }
        {
          name: 'ai-services-dns-zone-aiservices'
          privateDnsZoneResourceId: privateDnsZoneDeployments[dnsZoneIndex.aiServices]!.outputs.resourceId
        }
      ]
    }
  }
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
    tags: tags
    enableTelemetry: enableTelemetry
    skuName: enableScalability ? 'standard' : 'basic'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    networkRuleSet: {
      bypass: 'AzureServices'
    }
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
    diagnosticSettings: monitoringDiagnosticSettings
    roleAssignments: [
      {
        principalId: deployingUserPrincipalId
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: deployingUserPrincipalType
      }
      {
        principalId: deployingUserPrincipalId
        roleDefinitionIdOrName: 'Search Service Contributor'
        principalType: deployingUserPrincipalType
      }
      {
        principalId: deployingUserPrincipalId
        roleDefinitionIdOrName: 'Search Index Data Reader'
        principalType: deployingUserPrincipalType
      }
    ]
  }
}

module foundry_search_connection './modules/ai/ai-foundry-connection.bicep' = {
  name: take('module.foundry-search-conn.${solutionName}', 64)
  scope: resourceGroup(aiFoundrySubscriptionId, aiFoundryResourceGroupName)
  params: {
    solutionName: solutionSuffix
    aiServicesAccountName: aiFoundryName
    projectName: aiProjectName
    category: 'CognitiveSearch'
    target: ai_search.outputs.endpoint
    authType: 'AAD'
    metadata: {
      ApiType: 'Azure'
      ResourceId: ai_search.outputs.resourceId
      location: location
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
    location: location
    tags: tags
    databaseName: 'ecommerce_db'
    containers: [
      { name: 'carts', partitionKeyPath: '/user_id' }
      { name: 'chat_sessions', partitionKeyPath: '/user_id' }
      { name: 'products', partitionKeyPath: '/productId' }
      { name: 'transactions', partitionKeyPath: '/user_id' }
      { name: 'users', partitionKeyPath: '/email' }
    ]
    enableTelemetry: enableTelemetry
    diagnosticSettings: monitoringDiagnosticSettings
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    enablePrivateNetworking: enablePrivateNetworking
    privateEndpointSubnetId: enablePrivateNetworking ? virtualNetwork!.outputs.backendSubnetResourceId : ''
    privateDnsZoneResourceIds: enablePrivateNetworking ? [privateDnsZoneDeployments[dnsZoneIndex.cosmosDb]!.outputs.resourceId] : []
    zoneRedundant: enableRedundancy
    enableAutomaticFailover: enableRedundancy
    haLocation: enableRedundancy ? secondaryLocation : ''
  }
}

// ============================================================================
// Module: Compute
// ============================================================================

var chatFrontendImageRepository string = 'chat-frontend'
var chatBackendImageRepository string = 'chat-backend'
var scenarioFrontendImageRepository string = 'scenario-frontend'
var scenarioBackendImageRepository string = 'scenario-backend'
var chatbackendImageName = 'DOCKER|${containerRegistryEndpoint}/${chatBackendImageRepository}:${imageTag}'
var chatfrontendImageName = 'DOCKER|${containerRegistryEndpoint}/${chatFrontendImageRepository}:${imageTag}'
var scenarioBackendImageName = 'DOCKER|${containerRegistryEndpoint}/${scenarioBackendImageRepository}:${imageTag}'
var scenarioFrontendImageName = 'DOCKER|${containerRegistryEndpoint}/${scenarioFrontendImageRepository}:${imageTag}'

var chatApiAppName = 'api-chat-${solutionSuffix}'
var chatWebAppName = 'app-chat-${solutionSuffix}'
var scenarioApiAppName = 'api-scenario-${solutionSuffix}'
var scenarioWebAppName = 'app-scenario-${solutionSuffix}'

var hostAppTitle = deploymentScenario == 'healthcare'
  ? 'Contoso Health'
  : deploymentScenario == 'banking'
    ? 'Contoso Banking'
    : 'Contoso'

var chatWelcomeTitle = deploymentScenario == 'healthcare'
  ? 'How can I help with your care today?'
  : deploymentScenario == 'banking'
    ? 'How can I help with your banking today?'
    : 'Hey! I\'m here to help.'

var chatWelcomeSubtitle = deploymentScenario == 'healthcare'
  ? 'Ask about appointments, departments, visiting hours, or billing questions.'
  : deploymentScenario == 'banking'
    ? 'Ask about accounts, transactions, fees, or digital banking support.'
    : 'Ask me about returns & exchanges, warranties, or general product advice.'

var chatWidgetTheme = deploymentScenario == 'ecommerce' ? 'dark' : 'light'

var catalogSearchIndex = deploymentScenario == 'healthcare'
  ? 'services_index'
  : deploymentScenario == 'banking'
    ? 'accounts_index'
    : 'products_index'

var policiesSearchIndex = deploymentScenario == 'healthcare'
  ? 'care_policies_index'
  : deploymentScenario == 'banking'
    ? 'banking_policies_index'
    : 'policies_index'

var catalogToolName = deploymentScenario == 'healthcare'
  ? 'services_agent'
  : deploymentScenario == 'banking'
    ? 'accounts_agent'
    : 'product_agent'

var policyToolName = deploymentScenario == 'healthcare'
  ? 'care_policy_agent'
  : deploymentScenario == 'banking'
    ? 'banking_policy_agent'
    : 'policy_agent'

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
    tags: tags
    skuName: effectiveAppServicePlanSku
    skuCapacity: enableScalability ? 3 : 1
    zoneRedundant: enableRedundancy
    enableTelemetry: enableTelemetry
    diagnosticSettings: monitoringDiagnosticSettings
  }
}

module chat_backend_app './modules/compute/app-service.bicep' = {
  name: take('module.app-service-chat-backend.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    name: chatApiAppName
    location: location
    tags: tags
    kind: 'app,linux,container'
    linuxFxVersion: chatbackendImageName
    serverFarmResourceId: hostingplan.outputs.resourceId
    webSocketsEnabled: true
    healthCheckPath: '/health'
    enableTelemetry: enableTelemetry
    diagnosticSettings: monitoringDiagnosticSettings
    applicationInsightResourceId: enableMonitoring ? app_insights!.outputs.resourceId : ''
    publicNetworkAccess: 'Enabled' // enablePrivateNetworking ? 'Disabled' : 'Enabled'
    virtualNetworkSubnetId: enablePrivateNetworking ? virtualNetwork!.outputs.webserverfarmSubnetResourceId : ''
    vnetRouteAllEnabled: true
    imagePullTraffic: enablePrivateNetworking
    // privateEndpoints: enablePrivateNetworking
    //   ? [
    //       {
    //         name: 'pep-chat-api-${solutionSuffix}'
    //         customNetworkInterfaceName: 'nic-chat-api-${solutionSuffix}'
    //         privateDnsZoneGroup: {
    //           privateDnsZoneGroupConfigs: [
    //             { privateDnsZoneResourceId: privateDnsZoneDeployments[dnsZoneIndex.webApp]!.outputs.resourceId }
    //           ]
    //         }
    //         service: 'sites'
    //         subnetResourceId: virtualNetwork!.outputs.backendSubnetResourceId
    //       }
    //     ]
    //   : []
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
      AZURE_COSMOSDB_CONVERSATIONS_CONTAINER: cosmosDBModule.outputs.containerName
      AZURE_COSMOSDB_DATABASE: cosmosDBModule.outputs.databaseName
      AZURE_COSMOSDB_ENABLE_FEEDBACK: ''
      AZURE_AI_SEARCH_ENDPOINT: ai_search.outputs.endpoint
      AZURE_AI_SEARCH_INDEX: 'call_transcripts_index'
      AZURE_AI_SEARCH_CONNECTION_NAME: foundry_search_connection.outputs.connectionName
      USE_AI_PROJECT_CLIENT: 'True'
      DISPLAY_CHART_DEFAULT: 'False'
      APPLICATIONINSIGHTS_CONNECTION_STRING: enableMonitoring ? app_insights!.outputs.connectionString : ''
      DUMMY_TEST: 'True'
      SOLUTION_NAME: solutionSuffix
      APP_ENV: 'Prod'
      ALLOWED_ORIGINS_STR: 'https://${chatWebAppName}.azurewebsites.net,https://${scenarioWebAppName}.azurewebsites.net'
      AZURE_FOUNDRY_ENDPOINT: projectEndpoint
      AZURE_SEARCH_ENDPOINT: ai_search.outputs.endpoint
      AZURE_SEARCH_INDEX: 'policies'
      AZURE_SEARCH_PRODUCT_INDEX: 'products'
      COSMOS_DB_DATABASE_NAME: cosmosDBModule.outputs.databaseName
      COSMOS_DB_ENDPOINT: 'https://${cosmosDBModule.outputs.name}.documents.azure.com:443/'
      USE_FOUNDRY_AGENTS: 'True'
      AZURE_OPENAI_DEPLOYMENT_NAME: gptModelName
      RATE_LIMIT_REQUESTS: '100'
      RATE_LIMIT_WINDOW: '60'
      FOUNDRY_CHAT_AGENT: ''
      FOUNDRY_PRODUCT_AGENT: ''
      FOUNDRY_POLICY_AGENT: ''
      AZURE_VOICELIVE_ENDPOINT: aiFoundryEndpoint
      VOICELIVE_MODEL: 'gpt-realtime-mini'
      VOICELIVE_VOICE: 'alloy'
      VOICELIVE_TRANSCRIBE_MODEL: 'gpt-4o-transcribe'
      VOICELIVE_VAD_SILENCE_MS: '1200'
      VOICELIVE_VAD_THRESHOLD: '0.5'
      VOICELIVE_VAD_PREFIX_PADDING_MS: '300'
      DEPLOYMENT_SCENARIO: deploymentScenario
      CHAT_WELCOME_TITLE: chatWelcomeTitle
      CHAT_WELCOME_SUBTITLE: chatWelcomeSubtitle
      AZURE_SEARCH_CATALOG_INDEX: catalogSearchIndex
      AZURE_SEARCH_POLICIES_INDEX: policiesSearchIndex
      FOUNDRY_CATALOG_TOOL_NAME: catalogToolName
      FOUNDRY_POLICY_TOOL_NAME: policyToolName
      APPINSIGHTS_INSTRUMENTATIONKEY: enableMonitoring ? app_insights!.outputs.instrumentationKey : ''
      REACT_APP_LAYOUT_CONFIG: reactAppLayoutConfig
    }
  }
}

module chat_frontend_app './modules/compute/app-service.bicep' = {
  name: take('module.app-service-chat-frontend.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    name: chatWebAppName
    location: location
    tags: tags
    kind: 'app,linux,container'
    linuxFxVersion: chatfrontendImageName
    serverFarmResourceId: hostingplan.outputs.resourceId
    appSettings: {
      NODE_ENV: 'production'
      VITE_API_BASE_URL: chat_backend_app.outputs.appUrl // enablePrivateNetworking ? '' : chat_backend_app.outputs.appUrl
      // BACKEND_API_URL: enablePrivateNetworking ? chat_backend_app.outputs.appUrl : ''
      DEPLOYMENT_SCENARIO: deploymentScenario
      VITE_SCENARIO: deploymentScenario
      CHAT_WELCOME_TITLE: chatWelcomeTitle
      CHAT_WELCOME_SUBTITLE: chatWelcomeSubtitle
      APPINSIGHTS_INSTRUMENTATIONKEY: enableMonitoring ? app_insights!.outputs.instrumentationKey : ''
    }
  }
  scope: resourceGroup(resourceGroup().name)
}

module scenario_backend_app './modules/compute/app-service.bicep' = {
  name: take('module.app-service-backend.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    name: scenarioApiAppName
    location: location
    tags: tags
    kind: 'app,linux,container'
    serverFarmResourceId: hostingplan.outputs.resourceId
    linuxFxVersion: scenarioBackendImageName
    healthCheckPath: '/health'
    webSocketsEnabled: true
    enableTelemetry: enableTelemetry
    diagnosticSettings: monitoringDiagnosticSettings
    applicationInsightResourceId: enableMonitoring ? app_insights!.outputs.resourceId : ''
    publicNetworkAccess: 'Enabled' //enablePrivateNetworking ? 'Disabled' : 'Enabled'
    virtualNetworkSubnetId: enablePrivateNetworking ? virtualNetwork!.outputs.webserverfarmSubnetResourceId : ''
    vnetRouteAllEnabled: true
    imagePullTraffic: enablePrivateNetworking
    // privateEndpoints: enablePrivateNetworking
    //   ? [
    //       {
    //         name: 'pep-scenario-api-${solutionSuffix}'
    //         customNetworkInterfaceName: 'nic-scenario-api-${solutionSuffix}'
    //         privateDnsZoneGroup: {
    //           privateDnsZoneGroupConfigs: [
    //             { privateDnsZoneResourceId: privateDnsZoneDeployments[dnsZoneIndex.webApp]!.outputs.resourceId }
    //           ]
    //         }
    //         service: 'sites'
    //         subnetResourceId: virtualNetwork!.outputs.backendSubnetResourceId
    //       }
    //     ]
    //   : []
    appSettings: {
      AZURE_OPENAI_DEPLOYMENT_MODEL: gptModelName
      AZURE_OPENAI_ENDPOINT: aiFoundryEndpoint
      AZURE_OPENAI_API_VERSION: azureOpenaiAPIVersion
      AZURE_OPENAI_RESOURCE: aiFoundryName
      AZURE_AI_AGENT_ENDPOINT: projectEndpoint
      AZURE_AI_AGENT_API_VERSION: azureAiAgentApiVersion
      AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME: gptModelName
      USE_CHAT_HISTORY_ENABLED: 'False'
      AZURE_COSMOSDB_ACCOUNT: cosmosDBModule.outputs.name
      AZURE_COSMOSDB_CONVERSATIONS_CONTAINER: cosmosDBModule.outputs.containerName
      AZURE_COSMOSDB_DATABASE: cosmosDBModule.outputs.databaseName
      AZURE_COSMOSDB_ENABLE_FEEDBACK: ''
      AZURE_AI_SEARCH_ENDPOINT: ai_search.outputs.endpoint
      AZURE_AI_SEARCH_INDEX: 'call_transcripts_index'
      AZURE_AI_SEARCH_CONNECTION_NAME: foundry_search_connection.outputs.connectionName
      USE_AI_PROJECT_CLIENT: 'True'
      DISPLAY_CHART_DEFAULT: 'False'
      APPLICATIONINSIGHTS_CONNECTION_STRING: enableMonitoring ? app_insights!.outputs.connectionString : ''
      DUMMY_TEST: 'True'
      SOLUTION_NAME: solutionSuffix
      APP_ENV: 'Prod'
      ALLOWED_ORIGINS_STR: 'https://${scenarioWebAppName}.azurewebsites.net'
      AZURE_FOUNDRY_ENDPOINT: projectEndpoint
      AZURE_SEARCH_ENDPOINT: ai_search.outputs.endpoint
      AZURE_SEARCH_INDEX: 'policies'
      AZURE_SEARCH_PRODUCT_INDEX: 'products'
      COSMOS_DB_DATABASE_NAME: cosmosDBModule.outputs.databaseName
      COSMOS_DB_ENDPOINT: 'https://${cosmosDBModule.outputs.name}.documents.azure.com:443/'
      USE_FOUNDRY_AGENTS: 'False'
      AZURE_OPENAI_DEPLOYMENT_NAME: gptModelName
      RATE_LIMIT_REQUESTS: '100'
      RATE_LIMIT_WINDOW: '60'
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
      DEPLOYMENT_SCENARIO: deploymentScenario
      APPINSIGHTS_INSTRUMENTATIONKEY: enableMonitoring ? app_insights!.outputs.instrumentationKey : ''
      REACT_APP_LAYOUT_CONFIG: reactAppLayoutConfig
    }
  }
}


module scenario_frontend_app './modules/compute/app-service.bicep' = {
  name: take('module.app-service-frontend.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    name: scenarioWebAppName
    location: location
    tags: tags
    kind: 'app,linux,container'
    serverFarmResourceId: hostingplan.outputs.resourceId
    linuxFxVersion: scenarioFrontendImageName
    enableTelemetry: enableTelemetry
    diagnosticSettings: monitoringDiagnosticSettings
    applicationInsightResourceId: enableMonitoring ? app_insights!.outputs.resourceId : ''
    publicNetworkAccess: 'Enabled'
    virtualNetworkSubnetId: enablePrivateNetworking ? virtualNetwork!.outputs.webserverfarmSubnetResourceId : ''
    vnetRouteAllEnabled: enablePrivateNetworking
    imagePullTraffic: enablePrivateNetworking
    appSettings: {
      NODE_ENV: 'production'
      VITE_API_BASE_URL: scenario_backend_app.outputs.appUrl // enablePrivateNetworking ? '' : scenario_backend_app.outputs.appUrl
      VITE_CHAT_API_BASE_URL: chat_backend_app.outputs.appUrl
      // BACKEND_API_URL: enablePrivateNetworking ? scenario_backend_app.outputs.appUrl : ''
      DEPLOYMENT_SCENARIO: deploymentScenario
      VITE_SCENARIO: deploymentScenario
      VITE_HOST_APP_TITLE: hostAppTitle
      VITE_CHAT_WIDGET_THEME: chatWidgetTheme
      APPINSIGHTS_INSTRUMENTATIONKEY: enableMonitoring ? app_insights!.outputs.instrumentationKey : ''
    }
  }
}

// ============================================================================
// Module: Role Assignments (centralized — service-to-service)
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
    appServicePrincipalIds: {
      chatBackendApp: chat_backend_app.outputs.identityPrincipalId
      scenarioBackendApp: scenario_backend_app.outputs.identityPrincipalId
    }
    deployerPrincipalId: deployingUserPrincipalId
    cosmosDbAccountName: cosmosDBModule.outputs.name
  }
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

@description('Name of the chat backend API App Service.')
output API_APP_NAME string = chat_backend_app.outputs.name

@description('Principal ID of the chat backend system-assigned managed identity.')
output API_PID string = chat_backend_app.outputs.identityPrincipalId

@description('API App Service URL.')
output API_APP_URL string = chat_backend_app.outputs.appUrl

@description('Web App Service URL.')
output WEB_APP_URL string = chat_frontend_app.outputs.appUrl

@description('Chat API App Service URL.')
output CHAT_API_APP_URL string = chat_backend_app.outputs.appUrl

@description('Chat Web App Service URL.')
output CHAT_WEB_APP_URL string = chat_frontend_app.outputs.appUrl

@description('E-commerce API App Service URL.')
output SCENARIO_API_APP_URL string = scenario_backend_app.outputs.appUrl

@description('E-commerce Web App Service URL.')
output SCENARIO_WEB_APP_URL string = scenario_frontend_app.outputs.appUrl

@description('Chat API App Service Name.')
output CHAT_API_APP_NAME string = chat_backend_app.outputs.name

@description('Chat Web App Service Name.')
output CHAT_WEB_APP_NAME string = chat_frontend_app.outputs.name

@description('E-commerce API App Service Name.')
output SCENARIO_API_APP_NAME string = scenario_backend_app.outputs.name

@description('E-commerce Web App Service Name.')
output SCENARIO_WEB_APP_NAME string = scenario_frontend_app.outputs.name

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
