#!/usr/bin/env pwsh
<#
.SYNOPSIS
Deploy using WAF configuration (infra_avm/main.bicep with WAF parameters)

.DESCRIPTION
This script temporarily switches to azure.avm.yaml configuration and swaps parameter files to use main.waf.parameters.json.
#>

Write-Host "=== WAF Deployment ===" -ForegroundColor Cyan
Write-Host "Deploying with infra_avm configuration (WAF parameters)...`n" -ForegroundColor Yellow

# Check if azure.avm.yaml exists
if (-not (Test-Path "azure.avm.yaml")) {
    Write-Host "✗ Error: azure.avm.yaml not found!" -ForegroundColor Red
    exit 1
}

# Check if WAF parameters file exists
if (-not (Test-Path "infra_avm\main.waf.parameters.json")) {
    Write-Host "✗ Error: infra_avm\main.waf.parameters.json not found!" -ForegroundColor Red
    exit 1
}

# Backup current azure.yaml
$backupYamlExists = $false
if (Test-Path "azure.yaml") {
    Copy-Item "azure.yaml" "azure.yaml.backup" -Force
    $backupYamlExists = $true
    Write-Host "✓ Backed up azure.yaml" -ForegroundColor Green
}

# Backup current parameters file
$backupParamsExists = $false
if (Test-Path "infra_avm\main.parameters.json") {
    Copy-Item "infra_avm\main.parameters.json" "infra_avm\main.parameters.json.backup" -Force
    $backupParamsExists = $true
    Write-Host "✓ Backed up main.parameters.json" -ForegroundColor Green
}

# Switch to WAF configuration
Copy-Item "azure.avm.yaml" "azure.yaml" -Force
Write-Host "✓ Switched to azure.avm.yaml configuration" -ForegroundColor Green

# Switch to WAF parameters
Copy-Item "infra_avm\main.waf.parameters.json" "infra_avm\main.parameters.json" -Force
Write-Host "✓ Switched to main.waf.parameters.json" -ForegroundColor Green
Write-Host "✓ Using infra_avm/main.bicep with WAF parameters" -ForegroundColor Green
Write-Host "`nRunning: azd up`n" -ForegroundColor Yellow

try {
    azd up
}
finally {
    # Restore original azure.yaml
    if ($backupYamlExists -and (Test-Path "azure.yaml.backup")) {
        Copy-Item "azure.yaml.backup" "azure.yaml" -Force
        Remove-Item "azure.yaml.backup" -Force
        Write-Host "`n✓ Restored original azure.yaml" -ForegroundColor Green
    }
    
    # Restore original parameters file
    if ($backupParamsExists -and (Test-Path "infra_avm\main.parameters.json.backup")) {
        Copy-Item "infra_avm\main.parameters.json.backup" "infra_avm\main.parameters.json" -Force
        Remove-Item "infra_avm\main.parameters.json.backup" -Force
        Write-Host "✓ Restored original main.parameters.json" -ForegroundColor Green
    }
}