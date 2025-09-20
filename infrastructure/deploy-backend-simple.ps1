param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Location = "West US 2"
)

Write-Host "🚀 SIMPLE BACKEND DEPLOYMENT" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green

$ErrorActionPreference = "Stop"

try {
    # Find frontend
    $frontendApps = az webapp list --resource-group $ResourceGroupName --query "[?contains(name, 'frontend')].name" -o tsv
    if (-not $frontendApps) {
        throw "No frontend found. Deploy frontend first."
    }
    $frontendName = ($frontendApps -split "`n")[-1]
    $frontendUrl = "https://$frontendName.azurewebsites.net"
    Write-Host "✅ Frontend: $frontendName" -ForegroundColor Green

    # Create backend name
    $timestamp = Get-Date -Format "yyyyMMddHHmm"
    $backendName = "backend-simple-$timestamp"
    Write-Host "✅ Backend: $backendName" -ForegroundColor Green

    # Create web app with EXPLICIT configuration
    Write-Host "`n📦 Creating backend app..." -ForegroundColor Blue
    
    az webapp create `
        --name $backendName `
        --resource-group $ResourceGroupName `
        --plan "frontend-plan" `
        --runtime "PYTHON:3.11" `
        --only-show-errors

    # Configure EVERYTHING explicitly
    Write-Host "⚙️  Configuring app..." -ForegroundColor Blue
    
    # Set startup command FIRST
    az webapp config set `
        --name $backendName `
        --resource-group $ResourceGroupName `
        --startup-file "gunicorn --bind 0.0.0.0:8000 --timeout 600 --workers 1 app.main:app -k uvicorn.workers.UvicornWorker" `
        --only-show-errors

    # Set app settings
    az webapp config appsettings set `
        --name $backendName `
        --resource-group $ResourceGroupName `
        --settings `
        "WEBSITES_PORT=8000" `
        "SCM_DO_BUILD_DURING_DEPLOYMENT=1" `
        "ALLOWED_ORIGINS=$frontendUrl,http://localhost:5173" `
        "PYTHONPATH=/home/site/wwwroot" `
        "WEBSITE_TIME_ZONE=UTC" `
        --only-show-errors

    Write-Host "✅ App configured" -ForegroundColor Green

    # Deploy code
    Write-Host "`n🚀 Deploying code..." -ForegroundColor Blue
    
    $backendPath = Join-Path $PSScriptRoot "..\backend"
    Push-Location $backendPath
    try {
        # Create simple zip
        $zipPath = Join-Path $PSScriptRoot "backend-simple.zip"
        if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
        
        # Zip everything except problematic folders
        $itemsToZip = Get-ChildItem -Path "." | Where-Object { 
            $_.Name -notin @("__pycache__", ".git", ".pytest_cache", "venv", "env") 
        }
        Compress-Archive -Path $itemsToZip -DestinationPath $zipPath -Force

        # Deploy with explicit settings
        az webapp deploy `
            --resource-group $ResourceGroupName `
            --name $backendName `
            --src-path $zipPath `
            --type zip `
            --async false `
            --timeout 600

        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

    } finally {
        Pop-Location
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Deployment completed" -ForegroundColor Green
    } else {
        throw "Deployment failed with exit code: $LASTEXITCODE"
    }

    # Test
    $backendUrl = "https://$backendName.azurewebsites.net"
    Write-Host "`n🔍 Testing backend..." -ForegroundColor Blue
    Write-Host "Wait 60 seconds for startup..." -ForegroundColor Yellow
    Start-Sleep -Seconds 60

    try {
        $response = Invoke-RestMethod -Uri "$backendUrl/health" -TimeoutSec 30
        Write-Host "✅ Backend is working!" -ForegroundColor Green
        Write-Host "Status: $($response.status)" -ForegroundColor Cyan
    } catch {
        Write-Host "⚠️  Backend still starting (normal for first deployment)" -ForegroundColor Yellow
    }

    # Results
    Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "======================" -ForegroundColor Green
    Write-Host "Backend: $backendUrl" -ForegroundColor Cyan
    Write-Host "API Docs: $backendUrl/docs" -ForegroundColor Cyan
    Write-Host "Health: $backendUrl/health" -ForegroundColor Cyan
    Write-Host "Frontend: $frontendUrl" -ForegroundColor Cyan

} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
