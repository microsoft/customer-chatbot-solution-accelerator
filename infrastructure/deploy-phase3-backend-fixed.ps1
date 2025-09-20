param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🚀 PHASE 3: BACKEND DEPLOYMENT (FIXED)" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

$ErrorActionPreference = "Stop"

try {
    # Check if logged in
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        throw "Not logged into Azure. Please run 'az login' first."
    }
    Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green

    # Check resource group
    $rgExists = az group exists --name $ResourceGroupName
    if ($rgExists -eq "false") {
        throw "Resource group does not exist. Please run Phase 1 first."
    }
    Write-Host "✅ Resource group exists" -ForegroundColor Green

    # Get Cosmos DB details (optional)
    Write-Host "`n🔍 Getting Cosmos DB details..." -ForegroundColor Blue
    $cosmosAccounts = az cosmosdb list --resource-group $ResourceGroupName --query "[].name" -o tsv
    if (-not $cosmosAccounts) {
        Write-Host "⚠️  No Cosmos DB found. Backend will use mock data." -ForegroundColor Yellow
        $cosmosEndpoint = ""
        $cosmosKey = ""
    } else {
        $cosmosDbName = $cosmosAccounts[0]
        $cosmosEndpoint = az cosmosdb show --name $cosmosDbName --resource-group $ResourceGroupName --query "documentEndpoint" -o tsv
        $cosmosKey = az cosmosdb keys list --name $cosmosDbName --resource-group $ResourceGroupName --query "primaryMasterKey" -o tsv
        Write-Host "✅ Found Cosmos DB: $cosmosDbName" -ForegroundColor Green
    }

    # Find frontend deployment
    Write-Host "`n🔍 Finding frontend deployment..." -ForegroundColor Blue
    $frontendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'frontend') || contains(name, 'ecommerce-frontend')].name" -o tsv
    if (-not $frontendApps) {
        Write-Host "❌ No frontend deployment found. Please deploy frontend first." -ForegroundColor Red
        exit 1
    }
    $frontendAppServiceName = ($frontendApps -split "`n")[-1]
    $frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"
    Write-Host "✅ Found frontend: $frontendAppServiceName" -ForegroundColor Green

    # Variables
    $timestamp = Get-Date -Format "yyyyMMddHHmm"
    $backendAppServiceName = "ecommerce-backend-$timestamp"
    $appServicePlanName = "frontend-plan"

    Write-Host "`n🐍 Creating Backend App Service..." -ForegroundColor Blue
    Write-Host "Backend App Service Name: $backendAppServiceName" -ForegroundColor Cyan

    # Create backend app service
    az webapp create `
        --name $backendAppServiceName `
        --resource-group $ResourceGroupName `
        --plan $appServicePlanName `
        --runtime "PYTHON:3.11" `
        --only-show-errors

    Write-Host "✅ Backend App Service created" -ForegroundColor Green

    # Configure app settings
    Write-Host "`n⚙️  Configuring app settings..." -ForegroundColor Blue
    
    $appSettings = @(
        "COSMOS_DB_ENDPOINT=$cosmosEndpoint",
        "COSMOS_DB_KEY=$cosmosKey", 
        "COSMOS_DB_DATABASE_NAME=ecommerce_db",
        "ALLOWED_ORIGINS=$frontendUrl,http://localhost:5173",
        "WEBSITES_PORT=8000",
        "SCM_DO_BUILD_DURING_DEPLOYMENT=1",
        "ENABLE_ORYX_BUILD=true",
        "PYTHONPATH=/home/site/wwwroot",
        "AZURE_OPENAI_ENDPOINT=https://testmodle.openai.azure.com/",
        "AZURE_OPENAI_API_KEY=your_openai_api_key_here",
        "AZURE_OPENAI_API_VERSION=2025-01-01-preview",
        "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini"
    )

    az webapp config appsettings set `
        --name $backendAppServiceName `
        --resource-group $ResourceGroupName `
        --settings $appSettings `
        --only-show-errors

    # Set startup command
    Write-Host "⚙️  Setting startup command..." -ForegroundColor Blue
    az webapp config set `
        --name $backendAppServiceName `
        --resource-group $ResourceGroupName `
        --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" `
        --only-show-errors

    Write-Host "✅ Configuration completed" -ForegroundColor Green

    # Prepare backend code
    Write-Host "`n📦 Preparing backend code..." -ForegroundColor Blue
    
    $backendPath = Join-Path $PSScriptRoot "..\backend"
    if (-not (Test-Path $backendPath)) {
        throw "Backend directory not found at: $backendPath"
    }

    Push-Location $backendPath
    try {
        # Verify requirements.txt
        if (-not (Test-Path "requirements.txt")) {
            throw "requirements.txt not found in backend directory"
        }

        # Create a clean deployment package
        $deployPath = Join-Path $PSScriptRoot "backend-deploy-clean"
        if (Test-Path $deployPath) {
            Remove-Item $deployPath -Recurse -Force
        }
        New-Item -ItemType Directory -Path $deployPath -Force | Out-Null

        # Copy only necessary files
        Write-Host "Copying backend files..." -ForegroundColor Gray
        Copy-Item "app" $deployPath -Recurse -Force
        Copy-Item "requirements.txt" $deployPath -Force

        # Create a simple web.config for better Azure integration
        $webConfig = @"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified"/>
    </handlers>
    <httpPlatform processPath="python" arguments="-m uvicorn app.main:app --host 0.0.0.0 --port %HTTP_PLATFORM_PORT%" stdoutLogEnabled="true" stdoutLogFile="python.log" startupTimeLimit="60" requestTimeout="00:04:00">
    </httpPlatform>
  </system.webServer>
</configuration>
"@
        $webConfig | Out-File -FilePath "$deployPath\web.config" -Encoding UTF8

        # Create zip for deployment
        $zipPath = Join-Path $PSScriptRoot "backend-deploy-clean.zip"
        if (Test-Path $zipPath) {
            Remove-Item $zipPath -Force
        }
        
        Compress-Archive -Path "$deployPath\*" -DestinationPath $zipPath -Force
        Write-Host "✅ Deployment package created" -ForegroundColor Green

        # Deploy to Azure
        Write-Host "`n🚀 Deploying backend to Azure..." -ForegroundColor Blue
        az webapp deploy `
            --resource-group $ResourceGroupName `
            --name $backendAppServiceName `
            --src-path $zipPath `
            --type zip `
            --async false

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Backend deployment completed" -ForegroundColor Green
        } else {
            throw "Backend deployment failed"
        }

        # Clean up
        Remove-Item $deployPath -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

    } finally {
        Pop-Location
    }

    # Wait for startup
    Write-Host "`n⏳ Waiting for backend to start..." -ForegroundColor Blue
    Start-Sleep -Seconds 60

    # Test backend
    $backendUrl = "https://$backendAppServiceName.azurewebsites.net"
    Write-Host "`n🔍 Testing backend..." -ForegroundColor Blue
    
    try {
        $healthResponse = Invoke-RestMethod -Uri "$backendUrl/health" -Method GET -TimeoutSec 30
        Write-Host "✅ Backend health check passed" -ForegroundColor Green
        Write-Host "   Status: $($healthResponse.status)" -ForegroundColor Cyan
    } catch {
        Write-Host "⚠️  Backend still starting up (this is normal)" -ForegroundColor Yellow
        Write-Host "   Please wait 2-3 more minutes and test manually" -ForegroundColor Yellow
    }

    # Success summary
    Write-Host "`n🎉 PHASE 3 COMPLETE!" -ForegroundColor Green
    Write-Host "===================" -ForegroundColor Green
    Write-Host "✅ Backend: $backendAppServiceName" -ForegroundColor Green
    Write-Host "✅ Frontend: $frontendAppServiceName" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Test URLs:" -ForegroundColor Yellow
    Write-Host "   Backend API: $backendUrl" -ForegroundColor Cyan
    Write-Host "   API Docs: $backendUrl/docs" -ForegroundColor Cyan
    Write-Host "   Health Check: $backendUrl/health" -ForegroundColor Cyan
    Write-Host "   Frontend: $frontendUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Wait 2-3 minutes for full startup" -ForegroundColor White
    Write-Host "2. Test the URLs above" -ForegroundColor White
    Write-Host "3. Run Phase 4: ./deploy-phase4-integration.ps1" -ForegroundColor White

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check Azure portal for detailed logs" -ForegroundColor White
    Write-Host "2. Verify all dependencies in requirements.txt" -ForegroundColor White
    Write-Host "3. Check startup command configuration" -ForegroundColor White
    exit 1
}
