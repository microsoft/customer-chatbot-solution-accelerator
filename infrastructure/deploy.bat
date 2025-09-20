@echo off
REM Azure Infrastructure Deployment Script for Windows
REM This script deploys the e-commerce chat application infrastructure to Azure

setlocal enabledelayedexpansion

REM Default values
set "RESOURCE_GROUP_NAME=ecommerce-chat-rg"
set "LOCATION=East US"
set "ENVIRONMENT=dev"
set "APP_NAME_PREFIX=ecommerce-chat"
set "SUBSCRIPTION_ID="

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :check_required
if "%~1"=="--subscription-id" (
    set "SUBSCRIPTION_ID=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--resource-group" (
    set "RESOURCE_GROUP_NAME=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--location" (
    set "LOCATION=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--environment" (
    set "ENVIRONMENT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--app-name-prefix" (
    set "APP_NAME_PREFIX=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
echo Unknown option %~1
exit /b 1

:show_help
echo Usage: %0 --subscription-id ^<subscription-id^> [options]
echo Options:
echo   --subscription-id    Azure subscription ID (required)
echo   --resource-group     Resource group name (default: ecommerce-chat-rg)
echo   --location          Azure location (default: East US)
echo   --environment       Environment name (default: dev)
echo   --app-name-prefix   Application name prefix (default: ecommerce-chat)
echo   -h, --help          Show this help message
exit /b 0

:check_required
if "%SUBSCRIPTION_ID%"=="" (
    echo Error: --subscription-id is required
    exit /b 1
)

echo 🚀 Starting Azure Infrastructure Deployment...
echo Subscription ID: %SUBSCRIPTION_ID%
echo Resource Group: %RESOURCE_GROUP_NAME%
echo Location: %LOCATION%
echo Environment: %ENVIRONMENT%

REM Check if Azure CLI is installed
az --version >nul 2>&1
if errorlevel 1 (
    echo Error: Azure CLI is not installed. Please install it first.
    echo Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
    exit /b 1
)

REM Login to Azure (if not already logged in)
echo 🔐 Checking Azure login status...
az account show >nul 2>&1
if errorlevel 1 (
    echo Not logged in. Please log in to Azure...
    az login
    if errorlevel 1 (
        echo Error: Failed to login to Azure
        exit /b 1
    )
)
echo ✅ Successfully logged in to Azure

REM Set subscription
echo 📋 Setting subscription...
az account set --subscription "%SUBSCRIPTION_ID%"
if errorlevel 1 (
    echo Error: Failed to set subscription
    exit /b 1
)
echo ✅ Subscription set to: %SUBSCRIPTION_ID%

REM Create resource group if it doesn't exist
echo 📦 Creating resource group...
az group show --name "%RESOURCE_GROUP_NAME%" >nul 2>&1
if errorlevel 1 (
    az group create --name "%RESOURCE_GROUP_NAME%" --location "%LOCATION%"
    if errorlevel 1 (
        echo Error: Failed to create resource group
        exit /b 1
    )
    echo ✅ Resource group created: %RESOURCE_GROUP_NAME%
) else (
    echo ✅ Resource group already exists: %RESOURCE_GROUP_NAME%
)

REM Deploy Bicep template
echo 🏗️ Deploying Bicep template...
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "DEPLOYMENT_NAME=ecommerce-chat-deployment-%YYYY%%MM%%DD%-%HH%%Min%%Sec%"

az deployment group create ^
    --resource-group "%RESOURCE_GROUP_NAME%" ^
    --template-file "main.bicep" ^
    --parameters "parameters.json" ^
    --name "%DEPLOYMENT_NAME%" ^
    --verbose

if errorlevel 1 (
    echo Error: Failed to deploy Bicep template
    exit /b 1
)

echo ✅ Bicep template deployed successfully!
echo Deployment Name: %DEPLOYMENT_NAME%

REM Display outputs
echo 📊 Deployment Outputs:
az deployment group show ^
    --resource-group "%RESOURCE_GROUP_NAME%" ^
    --name "%DEPLOYMENT_NAME%" ^
    --query "properties.outputs" ^
    --output table

REM Configure Key Vault access policies
echo 🔑 Configuring Key Vault access policies...
set "KEY_VAULT_NAME=%APP_NAME_PREFIX%-%ENVIRONMENT%-kv"

REM Get current user
for /f "tokens=*" %%i in ('az account show --query user.name --output tsv') do set "CURRENT_USER=%%i"

REM Get the current user's object ID
for /f "tokens=*" %%i in ('az ad user show --id "%CURRENT_USER%" --query id --output tsv') do set "USER_OBJECT_ID=%%i"

REM Set Key Vault access policy
az keyvault set-policy ^
    --name "%KEY_VAULT_NAME%" ^
    --object-id "%USER_OBJECT_ID%" ^
    --secret-permissions get set list delete ^
    --key-permissions get list create delete update import backup restore recover purge

if errorlevel 1 (
    echo Warning: Failed to configure Key Vault access policies
    echo You may need to configure access policies manually
) else (
    echo ✅ Key Vault access policies configured
)

REM Display next steps
echo.
echo 🎉 Infrastructure deployment completed successfully!
echo.
echo 📋 Next Steps:
echo 1. Configure Azure OpenAI Service:
echo    - Go to Azure Portal ^> Create Resource ^> Azure OpenAI
echo    - Create a new Azure OpenAI resource
echo    - Deploy GPT-4o model
echo    - Add secrets to Key Vault
echo.
echo 2. Configure Microsoft Entra ID:
echo    - Go to Azure Portal ^> Azure Active Directory ^> App registrations
echo    - Create new app registration
echo    - Add secrets to Key Vault
echo.
echo 3. Deploy Application Code:
echo    - Use Azure CLI or Azure DevOps to deploy frontend and backend
echo    - Configure app settings with Key Vault references
echo.
echo 4. Test the Application:
echo    - Frontend: https://%APP_NAME_PREFIX%-%ENVIRONMENT%-frontend.azurewebsites.net
echo    - Backend: https://%APP_NAME_PREFIX%-%ENVIRONMENT%-backend.azurewebsites.net
echo    - API Docs: https://%APP_NAME_PREFIX%-%ENVIRONMENT%-backend.azurewebsites.net/docs
echo.
echo 🔗 Useful Links:
echo Azure Portal: https://portal.azure.com
echo Resource Group: https://portal.azure.com/#@/resource/subscriptions/%SUBSCRIPTION_ID%/resourceGroups/%RESOURCE_GROUP_NAME%
echo.
echo ✨ Happy coding!

endlocal
