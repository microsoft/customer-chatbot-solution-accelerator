@description('Principal ID of the managed identity or service principal to assign the role to')
param principalId string

@description('Role definition ID (GUID) of the Azure RBAC role to assign')
param roleDefinitionId string

@description('Resource ID of the target resource to scope the role assignment to (leave empty for resource group scope)')
param targetResourceId string = ''

@description('Description for the role assignment')
param roleDescription string = 'Role assignment created by Bicep'

// Determine if we're scoping to an AI Project or resource group
var isProjectScoped = targetResourceId != ''

// Parse AI project resource ID when needed: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}
var resourceParts = split(isProjectScoped ? targetResourceId : '///////////', '/')
var parentAccountName = resourceParts[8]
var projectName = resourceParts[10]

// Generate a unique name for the role assignment
var uniqueName = isProjectScoped 
  ? guid(targetResourceId, principalId, roleDefinitionId)
  : guid(subscription().subscriptionId, resourceGroup().id, principalId, roleDefinitionId)

// Reference existing AI project resources
resource cognitiveServicesAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = if (isProjectScoped) {
  name: parentAccountName
}

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = if (isProjectScoped) {
  parent: cognitiveServicesAccount
  name: projectName
}

// Role assignment resource (resource group scoped)
resource roleAssignmentRG 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!isProjectScoped) {
  name: uniqueName
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalType: 'ServicePrincipal'
    description: roleDescription
  }
}

// Role assignment resource (AI project scoped)
resource roleAssignmentProject 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (isProjectScoped) {
  scope: aiProject
  name: uniqueName
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalType: 'ServicePrincipal'
    description: roleDescription
  }
}

// Outputs
@description('Resource ID of the created role assignment')
output roleAssignmentId string = isProjectScoped ? roleAssignmentProject.id : roleAssignmentRG.id

@description('Name (GUID) of the created role assignment')
output roleAssignmentName string = isProjectScoped ? roleAssignmentProject.name : roleAssignmentRG.name

