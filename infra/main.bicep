// ========== main.bicep ========== //
targetScope = 'resourceGroup'
var abbrs = loadJsonContent('./abbreviations.json')
@minLength(3)
@maxLength(20)
@description('A unique prefix for all resources in this deployment. This should be 3-20 characters long:')
param environmentName string

@description('Optional: Existing Log Analytics Workspace Resource ID')
param existingLogAnalyticsWorkspaceId string = ''

@description('Use this parameter to use an existing AI project resource ID')
param azureExistingAIProjectResourceId string = ''
param AZURE_LOCATION string=''
var solutionLocation = empty(AZURE_LOCATION) ? resourceGroup().location : AZURE_LOCATION
var uniqueId = toLower(uniqueString(subscription().id, environmentName, solutionLocation))
var solutionPrefix = 'da${padLeft(take(uniqueId, 12), 12, '0')}'

//Get the current deployer's information
var deployerInfo = deployer()
var deployingUserPrincipalId = deployerInfo.objectId

@description('Location for AI Foundry deployment. This is the location where the AI Foundry resources will be deployed.')
param aiDeploymentsLocation string
@description('Optional. Enable scalability for applicable resources, aligned with the Well Architected Framework recommendations. Defaults to false.')
param enableScalability bool = false
@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true
@description('Optional. Enable scaling for the container apps. Defaults to false.')
param enableScaling bool = false 
@description('Optional. Enable monitoring for the resources. This will enable Application Insights and Log Analytics. Defaults to false.')
param enableMonitoring bool = false 
@description('Optional. Enable private networking for the resources. Set to true to enable private networking. Defaults to false.')
param enablePrivateNetworking bool = false 
@description('Optional. Enable redundancy for applicable resources. Defaults to false.')
param enableRedundancy bool = false
@description('Database name')
param databaseName string = 'ecommerce_db'
@minLength(1)
@description('Secondary location for databases creation(example:eastus2):')
param secondaryLocation string = 'eastus2'
@description('Optional. Size of the Jumpbox Virtual Machine when created. Set to custom value if enablePrivateNetworking is true.')
param vmSize string? 
param imageVersion string = 'latest'
@minLength(1)
@description('GPT model deployment type:')
@allowed([
  'Standard'
  'GlobalStandard'
])
param deploymentType string = 'GlobalStandard'

@description('Optional. AI model deployment token capacity. Defaults to 150K tokens per minute.')
param capacity int = 10
@description('Name of the GPT model to deploy:')
param gptModelName string = 'gpt-4o-mini'

@description('Version of the GPT model to deploy:')
param gptModelVersion string = '2024-07-18'

@minValue(10)
@description('Capacity of the GPT deployment:')
// You can increase this, but capacity is limited per model/region, so you will get errors if you go over
// https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits
param gptDeploymentCapacity int = 10

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

var modelDeployment = {
  name: gptModelName
  model: {
    name: gptModelName
    format: 'OpenAI'
    version: gptModelVersion
  }
  sku: {
    name: deploymentType
    capacity: capacity
  }
  raiPolicyName: 'Microsoft.Default'
}

// ==========AI Foundry and related resources ========== //
module aiServices 'modules/ai-foundry/aifoundry.bicep' = {
  name: take('avm.res.cognitive-services.account.${solutionPrefix}', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: '${abbrs.ai.aiFoundry}${solutionPrefix}'
    location: aiDeploymentsLocation
    sku: 'S0'
    kind: 'AIServices'
    deployments: [ modelDeployment ]
    projectName: '${abbrs.ai.aiFoundryProject}${solutionPrefix}'
    projectDescription: '${abbrs.ai.aiFoundryProject}${solutionPrefix}'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: network.outputs.vnetResourceId
          subnetResourceId: network.outputs.subnetPrivateEndpointsResourceId
        }
      : null
    existingFoundryProjectResourceId: azureExistingAIProjectResourceId
    disableLocalAuth: true //Should be set to true for WAF aligned configuration
    customSubDomainName: 'ais-${solutionPrefix}'
    apiProperties: {
      //staticsEnabled: false
    }
    allowProjectManagement: true
    managedIdentities: {
      systemAssigned: true
    }
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    privateEndpoints: []
    roleAssignments: [
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
      }
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
      }
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
      }
    ]
    //tags: allTags
    enableTelemetry: enableTelemetry
  }
}


//==========Key Vault Module ========== //
module kvault 'deploy_keyvault.bicep' = {
  name: 'deploy_keyvault'
  params: {
    keyvaultName: '${abbrs.security.keyVault}${solutionPrefix}'
    solutionLocation: solutionLocation
    managedIdentityObjectId:managedIdentityModule.outputs.managedIdentityOutput.objectId
  }
  scope: resourceGroup(resourceGroup().name)
}


// //========== SQL DB module ========== //
// module sqlDBModule 'deploy_sql_db.bicep' = {
//   name: 'deploy_sql_db'
//   params: {
//     serverName: '${abbrs.databases.sqlDatabaseServer}${solutionPrefix}'
//     sqlDBName: 'products-${solutionPrefix}'
//     solutionLocation: secondaryLocation
//     // Removed keyVaultName as it is not allowed in params
//     managedIdentityName: managedIdentityModule.outputs.managedIdentityOutput.name
//     sqlUsers: [
//       {
//         principalId: managedIdentityModule.outputs.managedIdentityBackendAppOutput.clientId
//         principalName: managedIdentityModule.outputs.managedIdentityBackendAppOutput.name
//         databaseRoles: ['db_datareader']
//       }
//     ]
//   }
//   scope: resourceGroup(resourceGroup().name)
// }

//========== AVM WAF ========== //
//========== SQL Database module ========== //
// var sqlServerResourceName = 'sql-${solutionPrefix}'
// var sqlDbModuleName = 'sqldb-${solutionPrefix}'
// module sqlDBModule 'br/public:avm/res/sql/server:0.20.1' = {
//   name: take('avm.res.sql.server.${sqlServerResourceName}', 64)
//   params: {
//     // Required parameters
//     name: sqlServerResourceName
//     // Non-required parameters
//     administrators: {
//       azureADOnlyAuthentication: true
//       login: userAssignedIdentity.outputs.name
//       principalType: 'Application'
//       sid: userAssignedIdentity.outputs.principalId
//       tenantId: subscription().tenantId
//     }
//     connectionPolicy: 'Redirect'
//     databases: [
//       {
//         availabilityZone: enableRedundancy ? 1 : -1
//         collation: 'SQL_Latin1_General_CP1_CI_AS'
//         diagnosticSettings: enableMonitoring
//           ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }]
//           : null
//         licenseType: 'LicenseIncluded'
//         maxSizeBytes: 34359738368
//         name: sqlDbModuleName
//         minCapacity: '1'
//         sku: {
//           name: 'GP_S_Gen5'
//           tier: 'GeneralPurpose'
//           family: 'Gen5'
//           capacity: 2
//         }
//         zoneRedundant: enableRedundancy ? true : false
//       }
//     ]
//     location: secondaryLocation
//     managedIdentities: {
//       systemAssigned: true
//       userAssignedResourceIds: [
//         userAssignedIdentity.outputs.resourceId
//       ]
//     }
//     primaryUserAssignedIdentityResourceId: userAssignedIdentity.outputs.resourceId
//     privateEndpoints: enablePrivateNetworking
//       ? [
//           {
//             privateDnsZoneGroup: {
//               privateDnsZoneGroupConfigs: [
//                 {
//                   privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.sqlServer]!.outputs.resourceId
//                 }
//               ]
//             }
//             service: 'sqlServer'
//             subnetResourceId: network!.outputs.subnetPrivateEndpointsResourceId
//             //tags: tags
//           }
//         ]
//       : []
//     firewallRules: (!enablePrivateNetworking) ? [
//       {
//         endIpAddress: '255.255.255.255'
//         name: 'AllowSpecificRange'
//         startIpAddress: '0.0.0.0'
//       }
//       {
//         endIpAddress: '0.0.0.0'
//         name: 'AllowAllWindowsAzureIps'
//         startIpAddress: '0.0.0.0'
//       }
//     ] : []
//     //tags: tags
//   }
// }

// ========== Search Service ========== //
var searchServiceName = 'srch-${solutionPrefix}'
//var aiSearchIndexName = 'sample-dataset-index'
module searchService 'br/public:avm/res/search/search-service:0.11.1' = {
  name: take('avm.res.search.search-service.${solutionPrefix}', 64)
  params: {
    name: searchServiceName
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    disableLocalAuth: false
    hostingMode: 'default'
    managedIdentities: {
      systemAssigned: true
    }

    // Enabled the Public access because other services are not able to connect with search search AVM module when public access is disabled

    // publicNetworkAccess: enablePrivateNetworking  ? 'Disabled' : 'Enabled'
    publicNetworkAccess: 'Enabled'
    networkRuleSet: {
      bypass: 'AzureServices'
    }
    partitionCount: 1
    replicaCount: 1
    sku: enableScalability ? 'standard' : 'basic'
    //tags: tags
    roleAssignments: [
      {
        principalId: userAssignedIdentity.outputs.principalId
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'ServicePrincipal'
      }
      {
        principalId: deployingUserPrincipalId
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: deployerPrincipalType
      }
      // {
      //   principalId: aiFoundryAiProjectPrincipalId
      //   roleDefinitionIdOrName: 'Search Index Data Reader'
      //   principalType: 'ServicePrincipal'
      // }
      // {
      //   principalId: aiFoundryAiProjectPrincipalId
      //   roleDefinitionIdOrName: 'Search Service Contributor'
      //   principalType: 'ServicePrincipal'
      // }
    ]

    //Removing the Private endpoints as we are facing the issue with connecting to search service while comminicating with agents

    privateEndpoints:[]
    // privateEndpoints: enablePrivateNetworking 
    //   ? [
    //       {
    //         name: 'pep-search-${solutionSuffix}'
    //         customNetworkInterfaceName: 'nic-search-${solutionSuffix}'
    //         privateDnsZoneGroup: {
    //           privateDnsZoneGroupConfigs: [
    //             {
    //               privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.search]!.outputs.resourceId
    //             }
    //           ]
    //         }
    //         subnetResourceId: virtualNetwork!.outputs.subnetResourceIds[0]
    //         service: 'searchService'
    //       }
    //     ]
    //   : []
  }
}

// ========== User Assigned Identity ========== //
// WAF best practices for identity and access management: https://learn.microsoft.com/en-us/azure/well-architected/security/identity-access
var userAssignedIdentityResourceName = 'id-${solutionPrefix}'
module userAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: take('avm.res.managed-identity.user-assigned-identity.${userAssignedIdentityResourceName}', 64)
  params: {
    name: userAssignedIdentityResourceName
    location: solutionLocation
    //tags: tags
    enableTelemetry: enableTelemetry
  }
}
var deployerPrincipalType = contains(deployer(), 'userPrincipalName')? 'User' : 'ServicePrincipal'

var appFileStorageContainerName = 'files'
var referenceDataStorageContainerName = 'reference-data'

module storageAccount 'modules/storageAccount.bicep' = {
  name: take('storage-account-${solutionPrefix}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: take('${abbrs.storage.storageAccount}${solutionPrefix}', 24)
    location: solutionLocation
    //tags: allTags
    skuName: enableRedundancy ? 'Standard_GZRS' : 'Standard_LRS'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: network.outputs.vnetResourceId
          subnetResourceId: network.outputs.subnetPrivateEndpointsResourceId
        }
      : null
    containers: [
      {
        name: appFileStorageContainerName
        properties: {
          publicAccess: 'None'
        }
      }
            {
        name: referenceDataStorageContainerName
        properties: {
          publicAccess: 'None'
        }
      }
    ]
    roleAssignments: [
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
    ]
    enableTelemetry: enableTelemetry
  }
}

module containerAppBackend 'br/public:avm/res/app/container-app:0.17.0' = {
  name: take('container-app-backend-${solutionPrefix}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [] // Placeholder until applicationInsights is defined
  params: {
    name: take('${abbrs.containers.containerApp}backend-${solutionPrefix}', 32)
    location: solutionLocation
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      userAssignedResourceIds: [
        userAssignedIdentity.outputs.resourceId
      ]
    }
    containers: [
      {
        name: 'cmsabackend'
        image: 'ccbcontainerreg.azurecr.io/backend:latest'
        env: [
          {
            name: 'COSMOS_DB_ENDPOINT'
            value: 'https://${cosmosDbResourceName}.documents.azure.com:443/'
          }
          {
            name: 'ALLOWED_ORIGINS_STR'
            value: 'https://${containerAppFrontend.name}.azurewebsites.net'
          }
          {
            name: 'AZURE_CLIENT_ID'
            value: userAssignedIdentity.outputs.clientId
          }
          {
            name: 'AZURE_CLIENT_SECRET'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'AZURE_FOUNDRY_ENDPOINT'
            value: 'https://${aiServices.name}.services.ai.azure.com/api/projects/testModle-project'  
          }
          {
            name: 'AZURE_OPENAI_API_KEY'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'AZURE_OPENAI_API_KEY'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'AZURE_OPENAI_API_VERSION'
            value: gptModelVersion 
          }
          {
            name: 'AZURE_OPENAI_ENDPOINT'
            value: 'https://${aiServices.name}.openai.azure.com/' 
          }
          {
            name: 'AZURE_SEARCH_API_KEY'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'AZURE_SEARCH_ENDPOINT'
            value: 'https://${searchService.name}.search.windows.net/'
          }
          {
            name: 'AZURE_SEARCH_INDEX'
            value: 'policies' 
          }
          {
            name: 'AZURE_TENANT_ID'
            value: tenant().tenantId 
          }
          {
            name: 'COSMOS_DB_DATABASE_NAME'
            value: comsmosDbDatabaseName 
          }
          {
            name: 'COSMOS_DB_ENDPOINT'
            value: 'https://${cosmosDbResourceName}.documents.azure.com:443/' 
          }
          {
            name: 'DOCKER_REGISTRY_SERVER_PASSWORD'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'DOCKER_REGISTRY_SERVER_URL'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'DOCKER_REGISTRY_SERVER_USERNAME'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'FOUNDRY_KNOWLEDGE_AGENT_ID'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'FOUNDRY_ORCHESTRATOR_AGENT_ID'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'FOUNDRY_ORDER_AGENT_ID'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'FOUNDRY_PRODUCT_AGENT_ID'
            value: 'ReplaceWithAppropriateValue' // Replace with a valid value or remove this line if not needed
          }
          {
            name: 'USE_FOUNDRY_AGENTS'
            value: 'true'
          }
          {
            name: 'WEBSITES_CONTAINER_START_TIME_LIMIT'
            value: '1800'
          }
          {
            name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
            value: 'false'
          }
                    {
            name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
            value: '8000'
          }
        ]
        resources: {
          cpu: 1
          memory: '2.0Gi'
        }
        probes: enableMonitoring
          ? [
              {
                httpGet: {
                  path: '/health'
                  port: 8000
                }
                initialDelaySeconds: 3
                periodSeconds: 3
                type: 'Liveness'
              }
            ]
          : []
      }
    ]
    ingressTargetPort: 8000
    ingressExternal: true
    scaleSettings: {
      maxReplicas: enableScaling ? 3 : 1
      minReplicas: 1
      rules: enableScaling
        ? [
            {
              name: 'http-scaler'
              http: {
                metadata: {
                  concurrentRequests: 100
                }
              }
            }
          ]
        : []
    }
    //tags: allTags
    enableTelemetry: enableTelemetry
  }
}


module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.11.2' = {
  name: take('container-env-${solutionPrefix}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights, logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: containerAppsEnvironmentName
    infrastructureResourceGroupName: '${resourceGroup().name}-ME-${containerAppsEnvironmentName}'
    location: solutionLocation
    zoneRedundant: enableRedundancy && enablePrivateNetworking
    publicNetworkAccess: 'Enabled' // public access required for frontend
    infrastructureSubnetResourceId: enablePrivateNetworking ? network.outputs.subnetWebResourceId : null
    managedIdentities: {
      userAssignedResourceIds: [
        appIdentity.outputs.resourceId
      ]
    }
    appInsightsConnectionString: enableMonitoring ? applicationInsights.outputs.connectionString : null
    // appLogsConfiguration: enableMonitoring
    //   ? {
    //       destination: 'log-analytics'
    //       logAnalyticsConfiguration: {
    //         customerId: LogAnalyticsWorkspaceId
    //         sharedKey: LogAnalyticsPrimarySharedKey
    //       }
    //     }
    //   : {}
    // workloadProfiles: enablePrivateNetworking
    //   ? [
    //       // NOTE: workload profiles are required for private networking
    //       {
    //         name: 'Consumption'
    //         workloadProfileType: 'Consumption'
    //       }
    //     ]
    //   : []
    //tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module applicationInsights 'br/public:avm/res/insights/component:0.6.0' = if (enableMonitoring) {
  name: take('app-insights-${solutionPrefix}-deployment', 64)
  params: {
    name: '${abbrs.managementGovernance.applicationInsights}${solutionPrefix}'
    location: solutionLocation
    workspaceResourceId: logAnalyticsWorkspaceResourceId
    diagnosticSettings: [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }]
    //tags: allTags
    enableTelemetry: enableTelemetry
  }
}

var useExistingLogAnalytics = !empty(existingLogAnalyticsWorkspaceId)
var logAnalyticsWorkspaceResourceId = useExistingLogAnalytics ? existingLogAnalyticsWorkspaceId : logAnalyticsWorkspace.outputs.resourceId

// Deploy new Log Analytics workspace only if required and not using existing
module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = if ((enableMonitoring || enablePrivateNetworking) && !useExistingLogAnalytics) {
  name: take('log-analytics-${solutionPrefix}-deployment', 64)
  params: {
    name: '${abbrs.managementGovernance.logAnalyticsWorkspace}${solutionPrefix}'
    location: solutionLocation
    skuName: 'PerGB2018'
    dataRetention: 30
    diagnosticSettings: [{ useThisWorkspace: true }]
    //tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module network 'modules/network.bicep' = if (enablePrivateNetworking) {
  name: take('network-${solutionPrefix}-deployment', 64)
  params: {
    resourcesName: solutionPrefix
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkspaceResourceId
    vmAdminUsername: vmAdminUsername ?? 'JumpboxAdminUser'
    vmAdminPassword: vmAdminPassword ?? 'JumpboxAdminP@ssw0rd1234!'
    vmSize: vmSize ??  'Standard_DS2_v2' // Default VM size 
    location: solutionLocation
    //tags: allTags
    enableTelemetry: enableTelemetry
  }
}
module appIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: take('identity-app-${solutionPrefix}-deployment', 64)
  params: {
    name: '${abbrs.security.managedIdentity}${solutionPrefix}'
    location: solutionLocation
    //tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module containerAppFrontend 'br/public:avm/res/app/container-app:0.17.0' = {
  name: take('container-app-frontend-${solutionPrefix}-deployment', 64)
  params: {
    name: take('${abbrs.containers.containerApp}frontend-${solutionPrefix}', 32)
    location: solutionLocation
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      userAssignedResourceIds: [
        appIdentity.outputs.resourceId
      ]
    }
    containers: [
      {
        env: [
          {
            name: 'NODE_ENV'
            value: 'production'
          }
          {
            name: 'VITE_API_BASE_URL'
            value: 'https://${abbrs.containers.containerApp}backend-${solutionPrefix}.azurewebsites.net'
          }
                    {
            name: 'VITE_AZURE_AUTHORITY'
            value: 'https://login.microsoftonline.com/${tenant().tenantId}'
          }
                    {
            name: 'VITE_AZURE_CLIENT_ID'
            value: userAssignedIdentity.outputs.clientId
          }
                    {
            name: 'VITE_AZURE_TENANT_ID'
            value: tenant().tenantId
          }
                    {
            name: 'VITE_ENVIRONMENT'
            value: 'production'
          }
                    {
            name: 'VITE_REDIRECT_URI'
            value: 'https://${abbrs.containers.containerApp}frontend-${solutionPrefix}.azurewebsites.net/auth/callback'
          }
                    {
            name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
            value: 'false'
          }
                    {
            name: 'WEBSITES_PORT'
            value: '80'
          }
        ]
        image: 'ccbcontainerreg.azurecr.io/frontend:latest'
        name: 'ccbsfrontend'
        resources: {
          cpu: '1'
          memory: '2.0Gi'
        }
      }
    ]
    ingressTargetPort: 80
    ingressExternal: true
    scaleSettings: {
      maxReplicas: enableScaling ? 3 : 1
      minReplicas: 1
      rules: enableScaling
        ? [
            {
              name: 'http-scaler'
              http: {
                metadata: {
                  concurrentRequests: 100
                }
              }
            }
          ]
        : []
    }
    //tags: allTags
    enableTelemetry: enableTelemetry
  }
}

//Test appservice 
// module appService 'deploy_app_service.bicep' = {
//   name: '${solutionPrefix}-app-module'
//   params: {
//     solutionName: solutionPrefix
//     solutionLocation:solutionLocation
//     appServicePlanId: hostingplan.outputs.id
//     appImageName: 'DOCKER|ccbcontainerreg.azurecr.io/frontend:latest'
//     userassignedIdentityId: userAssignedIdentity.outputs.clientId
//     // appSettings: union(
//     //   appSettings,
//     //   {
//     //     APPINSIGHTS_INSTRUMENTATIONKEY: reference(applicationInsightsId, '2015-05-01').InstrumentationKey
//     //     REACT_APP_LAYOUT_CONFIG: reactAppLayoutConfig
//     //   }
//     // )
//   }
// }

//param userassignedIdentityId string
// param appServicePlanId string
// resource appService 'Microsoft.Web/sites@2020-06-01' = {
//   name: solutionPrefix
//   location: solutionLocation
//   identity: {
//     type: 'UserAssigned'
//     userAssignedIdentities: {
//       '${userAssignedIdentityResourceName}': {}
//     }
//   }
//   properties: {
//     serverFarmId: appServicePlanId
//     siteConfig: {
//       alwaysOn: true
//       ftpsState: 'Disabled'
//       linuxFxVersion: 'DOCKER|ccbcontainerreg.azurecr.io/frontend:latest'
//     }
//   }
//   resource basicPublishingCredentialsPoliciesFtp 'basicPublishingCredentialsPolicies' = {
//     name: 'ftp'
//     properties: {
//       allow: false
//     }
//   }
//   resource basicPublishingCredentialsPoliciesScm 'basicPublishingCredentialsPolicies' = {
//     name: 'scm'
//     properties: {
//       allow: false
//     }
//   }
// }


module hostingplan 'deploy_app_service_plan.bicep' = {
  name: 'deploy_app_service_plan'
  params: {
    solutionLocation: solutionLocation
    HostingPlanName: '${abbrs.compute.appServicePlan}${solutionPrefix}'
  }
}


//========== AVM WAF ========== //
//========== Cosmos DB module ========== //
var cosmosDbResourceName = 'cosmos-${solutionPrefix}'
//var cosmosDbDatabaseName = 'db_conversation_history'
var collectionName = 'conversations'
var productsContainerName = 'products'
var cartsContainerName = 'carts'
var chatSessionsContainerName = 'chat_sessions'
var transactionsContainerName = 'transactions'
var userProfilesContainerName = 'users'
var comsmosDbDatabaseName = 'ecommerce_db'
module cosmosDb 'br/public:avm/res/document-db/database-account:0.15.0' = {
  name: take('avm.res.document-db.database-account.${cosmosDbResourceName}', 64)
  params: {
    // Required parameters
    name: cosmosDbResourceName
    location: solutionLocation
    //tags: tags
    enableTelemetry: enableTelemetry
    sqlDatabases: [
      {
        name: comsmosDbDatabaseName
        containers: [
          {
            name: collectionName
            paths: [
              '/userId'
            ]
          }
          {
            name: productsContainerName
            paths: [
              '/user_id'
            ]
            kind: 'Hash'
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
            conflictResolutionPolicy: {
              mode: 'LastWriterWins'
              conflictResolutionPath: '/_ts'
            }
          }
          {
            name: cartsContainerName
            paths: [
              '/user_id'
            ]
            kind: 'Hash'
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
            conflictResolutionPolicy: {
              mode: 'LastWriterWins'
              conflictResolutionPath: '/_ts'
            }
          }
          {
            name: chatSessionsContainerName
            paths: [
              '/category'
            ]
            kind: 'Hash'
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
            conflictResolutionPolicy: {
              mode: 'LastWriterWins'
              conflictResolutionPath: '/_ts'
            }
          }
          {
            name: transactionsContainerName
            paths: [
              '/user_id'
            ]
            kind: 'Hash'
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
            conflictResolutionPolicy: {
              mode: 'LastWriterWins'
              conflictResolutionPath: '/_ts'
            }
          }
          {
            name: userProfilesContainerName
            paths: [
              '/email'
            ]
            kind: 'Hash'
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
            conflictResolutionPolicy: {
              mode: 'LastWriterWins'
              conflictResolutionPath: '/_ts'
            }
          }
        ]
      }
    ]
    dataPlaneRoleDefinitions: [
      {
        // Cosmos DB Built-in Data Contributor: https://docs.azure.cn/en-us/cosmos-db/nosql/security/reference-data-plane-roles#cosmos-db-built-in-data-contributor
        roleName: 'Cosmos DB SQL Data Contributor'
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
        ]
        assignments: [{ principalId: userAssignedIdentity.outputs.principalId }]
      }
    ]
    // WAF aligned configuration for Monitoring
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    // WAF aligned configuration for Private Networking
    networkRestrictions: {
      networkAclBypass: 'None'
      publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    }
    privateEndpoints: enablePrivateNetworking
      ? [
          {
            name: 'pep-${cosmosDbResourceName}'
            customNetworkInterfaceName: 'nic-${cosmosDbResourceName}'
            privateDnsZoneGroup: {
              privateDnsZoneGroupConfigs: [
                { privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.cosmosDB]!.outputs.resourceId }
              ]
            }
            service: 'Sql'
            subnetResourceId: network!.outputs.subnetPrivateEndpointsResourceId
          }
        ]
      : []
    // WAF aligned configuration for Redundancy
    zoneRedundant: enableRedundancy ? true : false
    capabilitiesToAdd: enableRedundancy ? null : ['EnableServerless']
    automaticFailover: enableRedundancy ? true : false
    failoverLocations: enableRedundancy
      ? [
          {
            failoverPriority: 0
            isZoneRedundant: true
            locationName: secondaryLocation
          }
          {
            failoverPriority: 1
            isZoneRedundant: true
            locationName: solutionLocation
          }
        ]
      : [
          {
            locationName: solutionLocation
            failoverPriority: 0
            isZoneRedundant: false
          }
        ]
  }
  dependsOn: [storageAccount]
}

// ===================================================
// DEPLOY PRIVATE DNS ZONES
// - Deploys all zones if no existing Foundry project is used
// - Excludes AI-related zones when using with an existing Foundry project
// ===================================================
@batchSize(5)
module avmPrivateDnsZones 'br/public:avm/res/network/private-dns-zone:0.7.1' = [
  for (zone, i) in privateDnsZones: if (enablePrivateNetworking) {
    name: 'avm.res.network.private-dns-zone.${split(zone, '.')[1]}'
    params: {
      name: zone
      //tags: tags
      enableTelemetry: enableTelemetry
      virtualNetworkLinks: [
        {
          name: take('vnetlink-${network!.outputs.vnetName}-${split(zone, '.')[1]}', 80)
          virtualNetworkResourceId: network!.outputs.vnetResourceId
        }
      ]
    }
  }
]

// ========== Private DNS Zones ========== //
var privateDnsZones = [
  'privatelink.cognitiveservices.azure.com'
  'privatelink.openai.azure.com'
  'privatelink.services.ai.azure.com'
  'privatelink.blob.${environment().suffixes.storage}'
  'privatelink.queue.${environment().suffixes.storage}'
  'privatelink.file.${environment().suffixes.storage}'
  'privatelink.dfs.${environment().suffixes.storage}'
  'privatelink.documents.azure.com'
  'privatelink.vaultcore.azure.net'
  'privatelink${environment().suffixes.sqlServerHostname}'
  'privatelink.search.windows.net'
]
// DNS Zone Index Constants
var dnsZoneIndex = {
  cognitiveServices: 0
  openAI: 1
  aiServices: 2
  storageBlob: 3
  storageQueue: 4
  storageFile: 5
  storageDfs: 6
  cosmosDB: 7
  keyVault: 8
  sqlServer: 9
  search: 10
}

var containerAppsEnvironmentName = '${abbrs.containers.containerAppsEnvironment}${solutionPrefix}'
//param vmAdminUsername string = take(newGuid(), 20)
param vmAdminUsername string?
//param vmAdminPassword string = newGuid()
param vmAdminPassword string?

var LogAnalyticsWorkspaceId = useExistingLogAnalytics ? existingLogAnalyticsWorkspaceId : logAnalyticsWorkspace.outputs.logAnalyticsWorkspaceId
//var LogAnalyticsPrimarySharedKey string = useExistingLogAnalytics ? listKeys(existingLogAnalyticsWorkspaceId, '2023-01-01').keys[0].value : logAnalyticsWorkspace.outputs.primarySharedKey
