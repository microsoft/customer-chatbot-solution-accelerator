#!/usr/bin/env pwsh
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
#Requires -Version 7.0

<#
.SYNOPSIS
    Configures Microsoft Entra authentication after the App Services exist.

.DESCRIPTION
    Creates or reuses a single-tenant app registration, configures Easy Auth on
    both frontend App Services, and sets the tenant and audience used by both
    Python backends for JWT validation. The application client ID is persisted
    in the current Azure Developer CLI environment for idempotent reruns.

.PARAMETER ResourceGroup
    Resource group containing the four App Services.
.PARAMETER ChatBackendAppName
    Chat backend App Service name.
.PARAMETER ChatFrontendAppName
    Chat frontend App Service name.
.PARAMETER ScenarioBackendAppName
    Scenario backend App Service name.
.PARAMETER ScenarioFrontendAppName
    Scenario frontend App Service name.
.PARAMETER ClientId
    Existing app registration client ID. Defaults to AZURE_ENV_ENTRA_CLIENT_ID.
.PARAMETER AppDisplayName
    Display name used when creating an app registration.

.EXAMPLE
    ./infra/scripts/post-provision/configure_auth.ps1
#>

[CmdletBinding()]
param(
    [string]$ResourceGroup,
    [string]$ChatBackendAppName,
    [string]$ChatFrontendAppName,
    [string]$ScenarioBackendAppName,
    [string]$ScenarioFrontendAppName,
    [string]$ClientId,
    [string]$AppDisplayName
)

$ErrorActionPreference = 'Stop'
$secretSettingName = 'MICROSOFT_PROVIDER_AUTHENTICATION_SECRET'

# region Helpers
function Test-CommandAvailable {
    param([Parameter(Mandatory)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-AzdEnvValue {
    param([Parameter(Mandatory)][string]$Key)
    if (-not (Test-CommandAvailable 'azd')) { return $null }
    $value = azd env get-value $Key 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($value)) { return $null }
    if ($value -match 'ERROR:' -or $value -match 'not found in environment') { return $null }
    return $value.Trim()
}

function Resolve-Value {
    param([string]$Value, [Parameter(Mandatory)][string]$EnvironmentKey)
    if (-not [string]::IsNullOrWhiteSpace($Value)) { return $Value }
    $processValue = [Environment]::GetEnvironmentVariable($EnvironmentKey)
    if (-not [string]::IsNullOrWhiteSpace($processValue)) { return $processValue }
    return Get-AzdEnvValue $EnvironmentKey
}

function Invoke-Az {
    param([Parameter(Mandatory)][string[]]$Arguments)
    $output = az @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI command failed: az $($Arguments[0..([Math]::Min(2, $Arguments.Count - 1))] -join ' ')"
    }
    return $output
}

function Get-FrontendSecret {
    param(
        [Parameter(Mandatory)][string]$AppName,
        [Parameter(Mandatory)][string]$ExpectedClientId,
        [Parameter(Mandatory)][string]$SubscriptionId
    )
    $authUri = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$AppName/config/authsettingsV2?api-version=2022-09-01"
    $configuredClientId = az rest --method get --uri $authUri --query 'properties.identityProviders.azureActiveDirectory.registration.clientId' -o tsv 2>$null
    if ($LASTEXITCODE -ne 0 -or $configuredClientId -ne $ExpectedClientId) { return $null }
    $secret = az webapp config appsettings list --resource-group $ResourceGroup --name $AppName --query "[?name=='$secretSettingName'].value | [0]" -o tsv 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($secret)) { return $null }
    return $secret.Trim()
}

function Set-FrontendAuth {
    param(
        [Parameter(Mandatory)][string]$AppName,
        [Parameter(Mandatory)][string]$ApplicationClientId,
        [Parameter(Mandatory)][string]$TenantId,
        [Parameter(Mandatory)][string]$SubscriptionId,
        [Parameter(Mandatory)][string]$ClientSecret
    )
    Invoke-Az @('webapp', 'config', 'appsettings', 'set', '--resource-group', $ResourceGroup, '--name', $AppName, '--settings', "$secretSettingName=$ClientSecret", '--output', 'none') | Out-Null

    $body = @{
        properties = @{
            platform = @{ enabled = $true; runtimeVersion = '~1' }
            globalValidation = @{ requireAuthentication = $false; unauthenticatedClientAction = 'AllowAnonymous' }
            httpSettings = @{ requireHttps = $true }
            identityProviders = @{
                azureActiveDirectory = @{
                    enabled = $true
                    registration = @{
                        clientId = $ApplicationClientId
                        clientSecretSettingName = $secretSettingName
                        openIdIssuer = "https://login.microsoftonline.com/$TenantId/v2.0"
                    }
                    login = @{ loginParameters = @("scope=openid profile email offline_access api://$ApplicationClientId/user_impersonation") }
                    validation = @{ allowedAudiences = @($ApplicationClientId) }
                }
            }
            login = @{ tokenStore = @{ enabled = $true } }
        }
    } | ConvertTo-Json -Depth 10 -Compress

    $tempFile = New-TemporaryFile
    try {
        Set-Content -LiteralPath $tempFile.FullName -Value $body -NoNewline
        $authUri = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$AppName/config/authsettingsV2?api-version=2022-09-01"
        Invoke-Az @('rest', '--method', 'put', '--uri', $authUri, '--body', "@$($tempFile.FullName)", '--output', 'none') | Out-Null
    }
    finally {
        Remove-Item -LiteralPath $tempFile.FullName -Force -ErrorAction SilentlyContinue
    }
}
# endregion Helpers

function Invoke-Main {
    if (-not (Test-CommandAvailable 'az')) { throw "Azure CLI ('az') is required." }
    if (-not (Test-CommandAvailable 'azd')) { throw "Azure Developer CLI ('azd') is required." }

    $account = Invoke-Az @('account', 'show', '--output', 'json') | ConvertFrom-Json
    $tenantId = $account.tenantId
    $subscriptionId = $account.id

    $script:ResourceGroup = Resolve-Value $ResourceGroup 'AZURE_RESOURCE_GROUP'
    $script:ChatBackendAppName = Resolve-Value $ChatBackendAppName 'CHAT_API_APP_NAME'
    $script:ChatFrontendAppName = Resolve-Value $ChatFrontendAppName 'CHAT_WEB_APP_NAME'
    $script:ScenarioBackendAppName = Resolve-Value $ScenarioBackendAppName 'SCENARIO_API_APP_NAME'
    $script:ScenarioFrontendAppName = Resolve-Value $ScenarioFrontendAppName 'SCENARIO_WEB_APP_NAME'
    $script:ClientId = Resolve-Value $ClientId 'AZURE_ENV_ENTRA_CLIENT_ID'

    foreach ($requiredValue in @{
        ResourceGroup = $script:ResourceGroup
        ChatBackendAppName = $script:ChatBackendAppName
        ChatFrontendAppName = $script:ChatFrontendAppName
        ScenarioBackendAppName = $script:ScenarioBackendAppName
        ScenarioFrontendAppName = $script:ScenarioFrontendAppName
    }.GetEnumerator()) {
        if ([string]::IsNullOrWhiteSpace($requiredValue.Value)) { throw "Missing $($requiredValue.Key)." }
    }

    $environmentName = Get-AzdEnvValue 'AZURE_ENV_NAME'
    if ([string]::IsNullOrWhiteSpace($AppDisplayName)) {
        $AppDisplayName = if ($environmentName) { "$environmentName-customer-chatbot-auth" } else { "$ChatFrontendAppName-auth" }
    }

    $redirectUris = @(
        "https://$ChatFrontendAppName.azurewebsites.net/.auth/login/aad/callback"
        "https://$ScenarioFrontendAppName.azurewebsites.net/.auth/login/aad/callback"
    )

    $application = $null
    if ($ClientId) {
        $applicationJson = Invoke-Az @('ad', 'app', 'show', '--id', $ClientId, '--output', 'json')
        $application = $applicationJson | ConvertFrom-Json
        Write-Host "Reusing Microsoft Entra app registration '$($application.displayName)'."
    }
    else {
        Write-Host "Creating Microsoft Entra app registration '$AppDisplayName'."
        $createArguments = @('ad', 'app', 'create', '--display-name', $AppDisplayName, '--sign-in-audience', 'AzureADMyOrg', '--enable-id-token-issuance', 'true', '--web-redirect-uris') + $redirectUris + @('--output', 'json')
        $applicationJson = Invoke-Az $createArguments
        $application = $applicationJson | ConvertFrom-Json
        $ClientId = $application.appId
    }

    $existingRedirectUris = @($application.web.redirectUris)
    $mergedRedirectUris = @($existingRedirectUris + $redirectUris | Sort-Object -Unique)
    Invoke-Az (@('ad', 'app', 'update', '--id', $ClientId, '--enable-id-token-issuance', 'true', '--web-redirect-uris') + $mergedRedirectUris + @('--output', 'none')) | Out-Null

    $apiIdentifierUri = "api://$ClientId"
    $identifierUris = @(@($application.identifierUris) + $apiIdentifierUri | Sort-Object -Unique)
    $scope = @($application.api.oauth2PermissionScopes) | Where-Object { $_.value -eq 'user_impersonation' } | Select-Object -First 1
    Invoke-Az (@('ad', 'app', 'update', '--id', $ClientId, '--identifier-uris') + $identifierUris + @('--output', 'none')) | Out-Null
    $scopes = @($application.api.oauth2PermissionScopes)
    if (-not $scope) {
        $scopes += @{
            adminConsentDescription = 'Access the customer chatbot API on behalf of the signed-in user.'
            adminConsentDisplayName = 'Access the customer chatbot API'
            id = [guid]::NewGuid().ToString()
            isEnabled = $true
            type = 'User'
            userConsentDescription = 'Allow this application to access the customer chatbot API on your behalf.'
            userConsentDisplayName = 'Access the customer chatbot API'
            value = 'user_impersonation'
        }
    }

    $apiBody = @{
        api = @{
            acceptMappedClaims = $application.api.acceptMappedClaims
            knownClientApplications = @($application.api.knownClientApplications)
            oauth2PermissionScopes = $scopes
            preAuthorizedApplications = @($application.api.preAuthorizedApplications)
            requestedAccessTokenVersion = 2
        }
    } | ConvertTo-Json -Depth 10 -Compress
    $apiBodyFile = New-TemporaryFile
    try {
        Set-Content -LiteralPath $apiBodyFile.FullName -Value $apiBody -NoNewline
        Invoke-Az @('rest', '--method', 'patch', '--uri', "https://graph.microsoft.com/v1.0/applications/$($application.id)", '--body', "@$($apiBodyFile.FullName)", '--output', 'none') | Out-Null
    }
    finally {
        Remove-Item -LiteralPath $apiBodyFile.FullName -Force -ErrorAction SilentlyContinue
    }

    $clientSecret = Get-FrontendSecret -AppName $ChatFrontendAppName -ExpectedClientId $ClientId -SubscriptionId $subscriptionId
    if (-not $clientSecret) {
        $clientSecret = Get-FrontendSecret -AppName $ScenarioFrontendAppName -ExpectedClientId $ClientId -SubscriptionId $subscriptionId
    }
    if (-not $clientSecret) {
        Write-Host 'Creating an App Service authentication credential.'
        $clientSecret = Invoke-Az @('ad', 'app', 'credential', 'reset', '--id', $ClientId, '--append', '--display-name', 'App Service Easy Auth', '--years', '2', '--query', 'password', '--output', 'tsv')
        $clientSecret = ($clientSecret | Out-String).Trim()
    }

    foreach ($frontendApp in @($ChatFrontendAppName, $ScenarioFrontendAppName)) {
        Write-Host "Configuring Easy Auth on '$frontendApp'."
        Set-FrontendAuth -AppName $frontendApp -ApplicationClientId $ClientId -TenantId $tenantId -SubscriptionId $subscriptionId -ClientSecret $clientSecret
    }

    foreach ($backendApp in @($ChatBackendAppName, $ScenarioBackendAppName)) {
        Write-Host "Configuring JWT validation on '$backendApp'."
        Invoke-Az @('webapp', 'config', 'appsettings', 'set', '--resource-group', $ResourceGroup, '--name', $backendApp, '--settings', "ENTRA_AUTH_CLIENT_ID=$ClientId", "ENTRA_AUTH_TENANT_ID=$tenantId", '--output', 'none') | Out-Null
    }

    azd env set AZURE_ENV_ENTRA_CLIENT_ID $ClientId | Out-Null
    azd env set AZURE_ENV_ENTRA_APP_OBJECT_ID $application.id | Out-Null
    Write-Host "Authentication configured. Client ID: $ClientId" -ForegroundColor Green
}

if ($MyInvocation.InvocationName -ne '.') {
    Invoke-Main
}