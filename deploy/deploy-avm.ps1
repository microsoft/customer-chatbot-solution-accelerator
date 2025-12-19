#!/usr/bin/env pwsh
<#
.SYNOPSIS
Deploy using AVM configuration (infra_avm/main.bicep)

.DESCRIPTION
This script updates azure.yaml to use the AVM deployment configuration
and runs azd up.
#>

Write-Host "=== AVM Deployment ===" -ForegroundColor Cyan
Write-Host "Configuring for AVM deployment (infra_avm/)...`n" -ForegroundColor Yellow

# Update azure.yaml to use infra_avm path
$azureYaml = Get-Content "azure.yaml" -Raw
$azureYaml = $azureYaml -replace 'path:\s*infra(?!_)', 'path: infra_avm'

# Ensure infra path exists in yaml
if ($azureYaml -notmatch 'infra:\s*\n\s*path:') {
    $azureYaml = $azureYaml -replace '(metadata:.*?\n)', "`$1`ninfra:`n  path: infra_avm`n"
}

Set-Content "azure.yaml" -Value $azureYaml -NoNewline

Write-Host "✓ Configured for AVM deployment" -ForegroundColor Green
Write-Host "`nRunning: azd up`n" -ForegroundColor Yellow

azd up
