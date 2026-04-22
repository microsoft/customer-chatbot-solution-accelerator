param solutionLocation string
// param keyVaultName string
param accountName string 
// var accountName = '${ solutionName }-cosmos'
var databaseName = 'ecommerce_db'
var collectionName = 'chat_sessions'

var containers = [
  {
    name: 'carts'
    id: 'carts'
    partitionKey: '/user_id'
  } 
  {
    name: 'chat_sessions'
    id: 'chat_sessions'
    partitionKey: '/user_id'
  }
    {
    name: 'products'
    id: 'products'
    partitionKey: '/productId'
  }
    {
    name: 'transactions'
    id: 'transactions'
    partitionKey: '/user_id'
  }
    {
    name: 'users'
    id: 'users'
    partitionKey: '/email'
  }
]

@allowed([ 'GlobalDocumentDB', 'MongoDB', 'Parse' ])
param kind string = 'GlobalDocumentDB'

param tags object = {}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2025-11-01-preview' = {
  name: accountName
  kind: kind
  location: solutionLocation
  tags: tags
  properties: {
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    locations: [
      {
        locationName: solutionLocation
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    disableLocalAuth: true
    capacityMode: 'Serverless'
    apiProperties: (kind == 'MongoDB') ? { serverVersion: '4.0' } : {}
  }
}


resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-11-01-preview' = {
  name: '${accountName}/${databaseName}'
  properties: {
    resource: { id: databaseName }
  }

  resource list 'containers' = [for container in containers: {
    name: container.name
    properties: {
      resource: {
        id: container.id
        partitionKey: { paths: [ container.partitionKey ] }
      }
      options: {}
    }
  }]

  dependsOn: [
    cosmos
  ]
}

// resource keyVault 'Microsoft.KeyVault/vaults@2025-05-01' existing = {
//   name: keyVaultName
// }

// resource AZURE_COSMOSDB_ACCOUNT 'Microsoft.KeyVault/vaults/secrets@2025-05-01' = {
//   parent: keyVault
//   name: 'AZURE-COSMOSDB-ACCOUNT'
//   properties: {
//     value: cosmos.name
//   }
// }

// resource AZURE_COSMOSDB_ACCOUNT_KEY 'Microsoft.KeyVault/vaults/secrets@2025-05-01' = {
//   parent: keyVault
//   name: 'AZURE-COSMOSDB-ACCOUNT-KEY'
//   properties: {
//     value: cosmos.listKeys().primaryMasterKey
//   }
// }

// resource AZURE_COSMOSDB_DATABASE 'Microsoft.KeyVault/vaults/secrets@2025-05-01' = {
//   parent: keyVault
//   name: 'AZURE-COSMOSDB-DATABASE'
//   properties: {
//     value: databaseName
//   }
// }

// resource AZURE_COSMOSDB_CONVERSATIONS_CONTAINER 'Microsoft.KeyVault/vaults/secrets@2025-05-01' = {
//   parent: keyVault
//   name: 'AZURE-COSMOSDB-CONVERSATIONS-CONTAINER'
//   properties: {
//     value: collectionName
//   }
// }

// resource AZURE_COSMOSDB_ENABLE_FEEDBACK 'Microsoft.KeyVault/vaults/secrets@2025-05-01' = {
//   parent: keyVault
//   name: 'AZURE-COSMOSDB-ENABLE-FEEDBACK'
//   properties: {
//     value: 'True'
//   }
// }

output cosmosAccountName string = cosmos.name
output cosmosDatabaseName string = databaseName
output cosmosContainerName string = collectionName
