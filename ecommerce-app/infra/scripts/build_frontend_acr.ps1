#!/usr/bin/env pwsh
#Requires -Version 7.0

param(
    [string]$Registry = $env:AZURE_ENV_ACR_NAME,
    [string]$ImageTag = $env:AZURE_ENV_IMAGETAG,
    [string]$Repository = $(if ($env:AZURE_ENV_FRONTEND_IMAGE_REPO) { $env:AZURE_ENV_FRONTEND_IMAGE_REPO } else { 'ccsa-ecom-frontend' })
)

$ErrorActionPreference = 'Stop'

if (-not $ImageTag) {
    $ImageTag = 'latest_v2'
}

if (-not $Registry -and $env:AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT) {
    $Registry = ($env:AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT -replace '\.azurecr\.io\s*$', '')
}

if (-not $Registry) {
    Write-Error 'Set -Registry, or AZURE_ENV_ACR_NAME, or AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT (login server).'
}

$appRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$ctx = Join-Path $appRoot 'frontend'

$imageRef = "${Repository}:${ImageTag}"
Write-Host "az acr build --registry $Registry --image $imageRef --file Dockerfile --platform linux $ctx"

az acr build --registry $Registry --image $imageRef --file Dockerfile --platform linux $ctx
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Set AZURE_ENV_IMAGETAG=$ImageTag (and AZURE_ENV_FRONTEND_IMAGE_REPO=$Repository if non-default) then azd provision or update the web app."
