#!/usr/bin/env pwsh
<#
.SYNOPSIS
Deploy using WAF configuration (infra_avm/main.bicep with WAF parameters)

.DESCRIPTION
This script updates azure.yaml to use the AVM deployment configuration with
WAF parameters and runs azd up.
#>

Write-Host "=== WAF Deployment ===" -ForegroundColor Cyan
Write-Host "Configuring for WAF deployment (infra_avm/ with WAF parameters)...`n" -ForegroundColor Yellow

# Update azure.yaml to use infra_avm path
$azureYaml = Get-Content "azure.yaml" -Raw
$azureYaml = $azureYaml -replace 'path:\s*infra(?!_)', 'path: infra_avm'

# Ensure infra path exists in yaml
if ($azureYaml -notmatch 'infra:\s*\n\s*path:') {
    $azureYaml = $azureYaml -replace '(metadata:.*?\n)', "`$1`ninfra:`n  path: infra_avm`n"
}

Set-Content "azure.yaml" -Value $azureYaml -NoNewline

Write-Host "✓ Configured for WAF deployment" -ForegroundColor Green
Write-Host "`nSetting WAF parameters...`n" -ForegroundColor Yellow

azd config set infra.parameters main.waf.parameters.json

Write-Host "`nRunning: azd up`n" -ForegroundColor Yellow

azd up
