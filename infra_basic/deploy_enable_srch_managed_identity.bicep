@description('Required. Name of Azure Search Service.')
param searchServiceName string
@description('Required. Location for the Azure Search Service.')
param location string

resource aiSearchWithManagedIdentity 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchServiceName
  location: location
  sku: {
    name: 'basic'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    networkRuleSet: {
      ipRules: []
    }
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    disableLocalAuth: true
    semanticSearch: 'free'
  }
}

@description('The principal ID of the managed identity assigned to the Azure Search Service.')
output principalId string = aiSearchWithManagedIdentity.identity.principalId
