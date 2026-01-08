#!/usr/bin/env pwsh
<#
.SYNOPSIS
Deploy using Standard configuration (infra/main.bicep)

.DESCRIPTION
This script updates azure.yaml to use the standard deployment configuration
and runs azd up.
#>

Write-Host "=== Standard Deployment ===" -ForegroundColor Cyan
Write-Host "Configuring for Standard deployment (infra/)...`n" -ForegroundColor Yellow

# Update azure.yaml to use infra path
$azureYaml = Get-Content "azure.yaml" -Raw
$azureYaml = $azureYaml -replace 'path:\s*infra_avm', 'path: infra'

# Ensure infra path exists in yaml
if ($azureYaml -notmatch 'infra:\s*\n\s*path:') {
    $azureYaml = $azureYaml -replace '(metadata:.*?\n)', "`$1`ninfra:`n  path: infra`n"
}

Set-Content "azure.yaml" -Value $azureYaml -NoNewline

Write-Host "✓ Configured for Standard deployment" -ForegroundColor Green
Write-Host "`nRunning: azd up`n" -ForegroundColor Yellow

azd up
