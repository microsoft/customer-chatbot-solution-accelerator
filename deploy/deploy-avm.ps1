#!/usr/bin/env pwsh
<#
.SYNOPSIS
Deploy using AVM configuration (infra_avm/main.bicep)

.DESCRIPTION
This script temporarily switches to azure.avm.yaml configuration and deploys.
#>

Write-Host "=== AVM Deployment ===" -ForegroundColor Cyan
Write-Host "Deploying with infra_avm configuration...`n" -ForegroundColor Yellow

# Check if azure.avm.yaml exists
if (-not (Test-Path "azure.avm.yaml")) {
    Write-Host "✗ Error: azure.avm.yaml not found!" -ForegroundColor Red
    exit 1
}

# Backup current azure.yaml
$backupExists = $false
if (Test-Path "azure.yaml") {
    Copy-Item "azure.yaml" "azure.yaml.backup" -Force
    $backupExists = $true
    Write-Host "✓ Backed up azure.yaml" -ForegroundColor Green
}

# Switch to AVM configuration
Copy-Item "azure.avm.yaml" "azure.yaml" -Force
Write-Host "✓ Switched to azure.avm.yaml configuration (uses infra_avm/)" -ForegroundColor Green
Write-Host "`nRunning: azd up`n" -ForegroundColor Yellow

try {
    azd up
}
finally {
    # Restore original azure.yaml
    if ($backupExists -and (Test-Path "azure.yaml.backup")) {
        Copy-Item "azure.yaml.backup" "azure.yaml" -Force
        Remove-Item "azure.yaml.backup" -Force
        Write-Host "`n✓ Restored original azure.yaml" -ForegroundColor Green
    }
}