#!/usr/bin/env pwsh
#Requires -Version 7.0

$ErrorActionPreference = 'Stop'

function Get-AzdValue([string]$Key) {
    $v = azd env get-value $Key 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return $v
}

$rg = Get-AzdValue 'RESOURCE_GROUP_NAME'
if (-not $rg) { $rg = Get-AzdValue 'AZURE_RESOURCE_GROUP' }
if (-not $rg) { Write-Error 'RESOURCE_GROUP_NAME or AZURE_RESOURCE_GROUP not in azd env.' }

$suffix = Get-AzdValue 'SOLUTION_NAME'
if (-not $suffix) { Write-Error 'SOLUTION_NAME not in azd env.' }

$frontendName = "app-$suffix"
$apiName = Get-AzdValue 'API_APP_NAME'
if (-not $apiName) { $apiName = "api-$suffix" }

$fe = az webapp config show -g $rg -n $frontendName --query linuxFxVersion -o tsv 2>$null
$be = az webapp config show -g $rg -n $apiName --query linuxFxVersion -o tsv 2>$null

Write-Host "Frontend ($frontendName) linuxFxVersion: $fe"
Write-Host "Backend  ($apiName) linuxFxVersion: $be"

$url = Get-AzdValue 'WEB_APP_URL'
if ($url) { Write-Host "WEB_APP_URL: $url" }
