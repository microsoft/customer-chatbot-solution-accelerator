# Test Frontend Deployment
# This script tests the frontend deployment locally before deploying to Azure

param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat"
)

Write-Host "🧪 TESTING FRONTEND DEPLOYMENT" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

# Variables
$resourceNamePrefix = "$AppNamePrefix-$Environment"
$frontendAppServiceName = "$resourceNamePrefix-frontend"

# Check if frontend app service exists
Write-Host "`n🔍 Checking if frontend app service exists..." -ForegroundColor Blue
$appExists = az webapp show --name $frontendAppServiceName --resource-group $ResourceGroupName --query "name" -o tsv 2>$null

if ($appExists) {
    Write-Host "✅ Frontend app service exists: $frontendAppServiceName" -ForegroundColor Green
    
    # Get the app URL
    $frontendUrl = "https://$frontendAppServiceName.azurewebsites.net"
    Write-Host "🌐 Frontend URL: $frontendUrl" -ForegroundColor Cyan
    
    # Test the URL
    Write-Host "`n🔍 Testing frontend URL..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri $frontendUrl -Method GET -TimeoutSec 30
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Frontend is responding (Status: $($response.StatusCode))" -ForegroundColor Green
            
            # Check if it's serving the React app or the placeholder
            if ($response.Content -like "*Your web app is running and waiting for your content*") {
                Write-Host "⚠️  Frontend is showing placeholder content - deployment may not have completed" -ForegroundColor Yellow
            } elseif ($response.Content -like "*ShopChat*" -or $response.Content -like "*Shopping Assistant*") {
                Write-Host "✅ Frontend is serving the React application!" -ForegroundColor Green
            } else {
                Write-Host "❓ Frontend response is unexpected" -ForegroundColor Yellow
                Write-Host "Response preview: $($response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)))" -ForegroundColor Gray
            }
        } else {
            Write-Host "❌ Frontend returned status code: $($response.StatusCode)" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Failed to connect to frontend: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Frontend app service does not exist: $frontendAppServiceName" -ForegroundColor Red
    Write-Host "Please run the deployment script first." -ForegroundColor Yellow
}

Write-Host "`n✨ Test completed!" -ForegroundColor Green

