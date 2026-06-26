function Sync-AzdHookEnv {
    param([Parameter(Mandatory)][string]$ProjectRoot)
    $ErrorActionPreference = 'Stop'
    Push-Location $ProjectRoot
    try {
        $jsonText = azd env get-values -o json
        if ([string]::IsNullOrWhiteSpace($jsonText)) {
            return
        }
        $obj = $jsonText | ConvertFrom-Json
        foreach ($prop in $obj.PSObject.Properties) {
            if ($null -eq $prop.Value) {
                continue
            }
            Set-Item -LiteralPath ('Env:{0}' -f $prop.Name) -Value ([string]$prop.Value)
        }
        if (-not [string]::IsNullOrWhiteSpace($env:RESOURCE_GROUP_NAME) -and [string]::IsNullOrWhiteSpace($env:AZURE_RESOURCE_GROUP)) {
            Set-Item Env:AZURE_RESOURCE_GROUP -Value $env:RESOURCE_GROUP_NAME
        }
        if (-not [string]::IsNullOrWhiteSpace($env:AZURE_RESOURCE_GROUP) -and [string]::IsNullOrWhiteSpace($env:RESOURCE_GROUP_NAME)) {
            Set-Item Env:RESOURCE_GROUP_NAME -Value $env:AZURE_RESOURCE_GROUP
        }
    }
    finally {
        Pop-Location
    }
}
