param imageTag string
param containerRegistryLoginServer string
param applicationInsightsId string

@description('Solution Location')
param solutionLocation string

param imageRepository string

@secure()
param appSettings object = {}
param appServicePlanId string

param azdServiceName string = ''

var imageName = 'DOCKER|${containerRegistryLoginServer}/${imageRepository}:${imageTag}'
param name string
var svcTags = empty(azdServiceName) ? {} : { 'azd-service-name': azdServiceName }
module appService 'deploy_app_service.bicep' = {
  name: '${name}-app-module'
  params: {
    solutionLocation:solutionLocation
    solutionName: name
    appServicePlanId: appServicePlanId
    appImageName: imageName
    resourceTags: svcTags
    appSettings: union(
      appSettings,
      {
        APPINSIGHTS_INSTRUMENTATIONKEY: reference(applicationInsightsId, '2015-05-01').InstrumentationKey
      }
    )
  }
}

output appUrl string = appService.outputs.appUrl
output identityPrincipalId string = appService.outputs.identityPrincipalId
