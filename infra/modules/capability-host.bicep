@description('Name of the AI Foundry account (Cognitive Services)')
param aiFoundryName string

@description('Name of the AI Foundry project')
param aiFoundryProjectName string

@description('Name of the Cosmos DB connection for thread storage')
param threadStorageConnectionName string

@description('Name of the Storage connection for file storage')
param storageConnectionName string

@description('Name of the AI Search connection for vector store')
param vectorStoreConnectionName string

// Reference to the existing AI Foundry account
resource aiFoundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: aiFoundryName
}

// Account-level capability host - enables Agent Service on the account
resource accountCapabilityHost 'Microsoft.CognitiveServices/accounts/capabilityHosts@2025-06-01' = {
  parent: aiFoundryAccount
  name: 'default'
  properties: {
    capabilityHostKind: 'Agents'
  }
}

// Reference to the existing AI Foundry project
resource aiFoundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: aiFoundryAccount
  name: aiFoundryProjectName
}

// Project-level capability host - specifies BYO resources for agent data storage
resource projectCapabilityHost 'Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-06-01' = {
  parent: aiFoundryProject
  name: 'default'
  properties: {
    threadStorageConnections: [threadStorageConnectionName]
    vectorStoreConnections: [vectorStoreConnectionName]
    storageConnections: [storageConnectionName]
  }
  dependsOn: [
    accountCapabilityHost
  ]
}

@description('Name of the account capability host')
output accountCapabilityHostName string = accountCapabilityHost.name

@description('Name of the project capability host')
output projectCapabilityHostName string = projectCapabilityHost.name
