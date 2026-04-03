@description('Name of the AI Foundry account')
param aiFoundryName string

@description('Name of the AI Foundry project')
param aiFoundryProjectName string

@description('Name of the Cosmos DB connection')
param cosmosDbConnectionName string

@description('Resource ID of the Cosmos DB account')
param cosmosDbResourceId string

@description('Cosmos DB endpoint')
param cosmosDbEndpoint string

@description('Location of the Cosmos DB account')
param cosmosDbLocation string

@description('Name of the Storage connection')
param storageConnectionName string

@description('Resource ID of the Storage account')
param storageResourceId string

@description('Storage blob endpoint')
param storageBlobEndpoint string

@description('Location of the Storage account')
param storageLocation string

@description('Name of the AI Search connection')
param aiSearchConnectionName string

@description('Resource ID of the AI Search service')
param aiSearchResourceId string

@description('AI Search endpoint')
param aiSearchEndpoint string

@description('Location of the AI Search service')
param aiSearchLocation string

// Cosmos DB connection for thread storage
resource cosmosDbConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  name: '${aiFoundryName}/${aiFoundryProjectName}/${cosmosDbConnectionName}'
  properties: {
    category: 'CosmosDB'
    target: cosmosDbEndpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: cosmosDbResourceId
      location: cosmosDbLocation
    }
  }
}

// Storage connection for file storage
resource storageConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  name: '${aiFoundryName}/${aiFoundryProjectName}/${storageConnectionName}'
  properties: {
    category: 'AzureBlob'
    target: storageBlobEndpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: storageResourceId
      location: storageLocation
    }
  }
}

// AI Search connection for vector store (this supplements the existing CognitiveSearch connection)
resource aiSearchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  name: '${aiFoundryName}/${aiFoundryProjectName}/${aiSearchConnectionName}'
  properties: {
    category: 'CognitiveSearch'
    target: aiSearchEndpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: aiSearchResourceId
      location: aiSearchLocation
    }
  }
}

@description('Name of the Cosmos DB connection')
output cosmosDbConnectionOutputName string = cosmosDbConnectionName

@description('Name of the Storage connection')
output storageConnectionOutputName string = storageConnectionName

@description('Name of the AI Search connection')
output aiSearchConnectionOutputName string = aiSearchConnectionName
