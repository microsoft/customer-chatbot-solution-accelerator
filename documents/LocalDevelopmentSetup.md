# Local Development Setup Guide

This guide provides comprehensive instructions for setting up the Customer Chatbot Solution Accelerator for local development across Windows and Linux platforms.

## Important Setup Notes

### Multi-Service Architecture

This application consists of **two separate services** that run independently:

1. **Backend API** - FastAPI REST API server for the frontend
2. **Frontend** - React-based e-commerce user interface with integrated chat

> **⚠️ Critical: Each service must run in its own terminal/console window**
>
> - **Do NOT close terminals** while services are running
> - Open **2 separate terminal windows** for local development
> - Each service will occupy its terminal and show live logs

### Path Conventions

**All paths in this guide are relative to the repository root directory:**

```
customer-chatbot-solution-accelerator/       ← Repository root (start here)
├── src/
│   ├── api/                                 ← Backend FastAPI application
│   │   ├── app/                             ← Main application code
│   │   │   ├── routers/                     ← API endpoint routes
│   │   │   ├── services/                    ← Business logic services
│   │   │   ├── plugins/                     ← Agent plugins
│   │   │   └── utils/                       ← Utility functions
│   │   ├── .env                             ← Backend environment config
│   │   └── requirements.txt                 ← Python dependencies
│   ├── App/                                 ← Frontend React application
│   │   ├── src/                             ← React/TypeScript source
│   │   ├── package.json                     ← Frontend dependencies
│   │   └── env.example                      ← Frontend env template
│   ├── tests/                               ← Unit and integration tests
│   ├── start-local.bat                      ← Windows startup script
│   └── start-local.sh                       ← Linux/Mac startup script
├── infra/                                   ← Azure infrastructure (Bicep)
├── documents/                               ← Documentation (you are here)
├── .vscode/                                 ← VS Code configuration
└── azure.yaml                               ← Azure Developer CLI config
```

**Before starting any step, ensure you are in the repository root directory:**

```bash
# Verify you're in the correct location
pwd  # Linux/macOS - should show: .../customer-chatbot-solution-accelerator
Get-Location  # Windows PowerShell - should show: ...\customer-chatbot-solution-accelerator

# If not, navigate to repository root
cd path/to/customer-chatbot-solution-accelerator
```

---

## Step 1: Prerequisites - Install Required Tools

Install these tools before you start:

- [Visual Studio Code](https://code.visualstudio.com/) with the following extensions:
  - [Azure Tools](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-node-azure-pack)
  - [Bicep](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-bicep)
  - [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
  - [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- [Python 3.11+](https://www.python.org/downloads/). **Important:** Check "Add Python to PATH" during installation.
- [PowerShell 7.0+](https://github.com/PowerShell/PowerShell#get-powershell) (Windows)
- [Node.js (LTS)](https://nodejs.org/en) - Required for frontend development
- [Git](https://git-scm.com/downloads)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)

### Windows Development

#### Option 1: Native Windows (PowerShell)

```powershell
# Install Python 3.11+ and Git
winget install Python.Python.3.11
winget install Git.Git

# Install Node.js for frontend
winget install OpenJS.NodeJS.LTS

# Install Azure CLI
winget install Microsoft.AzureCLI

# Install Azure Developer CLI
winget install Microsoft.Azd
```

#### Option 2: Windows with WSL2 (Recommended for Linux-like experience)

```bash
# Install WSL2 first (run in PowerShell as Administrator):
# wsl --install -d Ubuntu

# Then in WSL2 Ubuntu terminal:
sudo apt update && sudo apt install python3.11 python3.11-venv git curl nodejs npm -y
```

### Linux Development

#### Ubuntu/Debian

```bash
# Install prerequisites
sudo apt update && sudo apt install python3.11 python3.11-venv git curl nodejs npm -y
```

#### RHEL/CentOS/Fedora

```bash
# Install prerequisites
sudo dnf install python3.11 python3.11-devel git curl gcc nodejs npm -y
```

---

## Step 2: Clone the Repository

Choose a location on your local machine where you want to store the project files.

### Using Command Line/Terminal

1. **Open your terminal or command prompt. Navigate to your desired directory and clone the repository:**

   ```bash
   git clone https://github.com/microsoft/customer-chatbot-solution-accelerator.git
   ```

2. **Navigate to the project directory:**

   ```bash
   cd customer-chatbot-solution-accelerator
   ```

3. **Open the project in Visual Studio Code:**

   ```bash
   code .
   ```

---

## Step 3: Development Tools Setup

### Visual Studio Code (Recommended)

The repository includes pre-configured VS Code settings in `.vscode/` directory:

- **launch.json** - Debug configurations for Python FastAPI backend
- **settings.json** - Python, linting, and testing configurations

#### Recommended Extensions

VS Code should automatically prompt you to install recommended extensions. If not, install these manually:

- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Python language server
- `ms-python.black-formatter` - Code formatting
- `ms-python.isort` - Import sorting
- `ms-python.flake8` - Linting
- `ms-azuretools.vscode-bicep` - Bicep support
- `ms-vscode.azure-account` - Azure account management

---

## Step 4: Azure Authentication Setup

Before running the application locally, authenticate with Azure:

```bash
# Login to Azure CLI
az login

# Set your subscription (replace with your subscription ID)
az account set --subscription "your-subscription-id"

# Verify authentication
az account show
```

---

## Step 5: Local Setup/Deployment

Follow these steps to set up and run the application locally:

### 5.1. Deploy Azure Resources First

Before running locally, you need Azure resources deployed. If you haven't already:

```bash
# Initialize Azure Developer CLI
azd init

# Deploy to Azure (this creates all required resources)
azd up
```

📖 **Detailed Deployment:** Follow the [Deployment Guide](./DeploymentGuide.md) for complete instructions.

### 5.2. Configure Environment Variables

#### Backend Environment (.env)

1. Navigate to `src/api/` directory
2. If resources were provisioned using `azd provision` or `azd up`, environment variables are automatically configured in `.azure/<env-name>/.env`
3. Copy or create a `.env` file in `src/api/` with the required values:

```env
# App Configuration
APP_ENV="dev"
ALLOWED_ORIGINS_STR="*"

# Azure AI Foundry
AZURE_AI_AGENT_ENDPOINT="https://your-ai-services.services.ai.azure.com/api/projects/your-project"
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
AZURE_FOUNDRY_ENDPOINT="https://your-ai-services.services.ai.azure.com/api/projects/your-project"

# Azure OpenAI
AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"
AZURE_OPENAI_API_VERSION="2025-01-01-preview"

# Azure AI Search
AZURE_AI_SEARCH_ENDPOINT="https://your-search.search.windows.net"
AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
AZURE_SEARCH_INDEX="policies"
AZURE_SEARCH_PRODUCT_INDEX="products"

# Azure Cosmos DB
COSMOS_DB_ENDPOINT="https://your-cosmos.documents.azure.com:443/"
COSMOS_DB_DATABASE_NAME="ecommerce_db"
AZURE_COSMOSDB_DATABASE="ecommerce_db"
AZURE_COSMOSDB_CONVERSATIONS_CONTAINER="chat_sessions"

# Foundry Agents
FOUNDRY_CHAT_AGENT="chat-agent-name"
FOUNDRY_PRODUCT_AGENT="product-agent-name"
FOUNDRY_POLICY_AGENT="policy-agent-name"
USE_FOUNDRY_AGENTS="True"
USE_AI_PROJECT_CLIENT="True"
```

> **Note**: Set `APP_ENV="dev"` for local development. This enables DefaultAzureCredential for authentication.

#### Frontend Environment

1. Navigate to `src/App/` directory
2. Copy `env.example` to `.env`:

```bash
cp src/App/env.example src/App/.env
```

3. Update the `.env` file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/
VITE_ENVIRONMENT=development
```

### 5.3. Required Azure RBAC Permissions

To run the application locally, your Azure account needs the following role assignments on the deployed resources:

#### Cosmos DB Access

```bash
# Get your principal ID
PRINCIPAL_ID=$(az ad signed-in-user show --query id -o tsv)

# Assign Cosmos DB Built-in Data Contributor role
az cosmosdb sql role assignment create \
  --account-name <cosmos-account-name> \
  --resource-group <resource-group> \
  --role-definition-name "Cosmos DB Built-in Data Contributor" \
  --principal-id $PRINCIPAL_ID \
  --scope "/"
```

#### Azure AI Search Access

```bash
# Assign Search Index Data Contributor role
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Search Index Data Contributor" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Search/searchServices/<search-name>"
```

> **Note**: After Azure deployment is complete, the post-deployment script assigns these roles automatically. You may only need to do this manually if permissions are missing.

---

## Step 6: Running the Application

### 6.1. Create Virtual Environment

Open your terminal and navigate to the repository root folder:

```bash
# Navigate to the project root folder
cd customer-chatbot-solution-accelerator

# Create virtual environment in the root folder
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate virtual environment (Windows Command Prompt)
.venv\Scripts\activate.bat

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate
```

> **Note**: After activation, you should see `(.venv)` in your terminal prompt indicating the virtual environment is active.

### 6.2. Install Dependencies

```bash
# Navigate to the API folder (while virtual environment is activated)
cd src/api

# Upgrade pip
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

### 6.3. Running with Automated Script

For convenience, use the provided startup scripts that handle starting both services:

**Windows:**

```cmd
cd src
.\start-local.bat
```

**macOS/Linux:**

```bash
cd src
chmod +x start-local.sh
./start-local.sh
```

### 6.4. Running Backend and Frontend Separately

> **📋 Terminal Reminder**: This section requires **two separate terminal windows** - one for the Backend API and one for the Frontend. Keep both terminals open while running.

#### Terminal 1: Backend API

```bash
# Navigate to the API folder (with virtual environment activated)
cd src/api

# Run the backend API
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2: Frontend

```bash
# Navigate to the frontend folder
cd src/App

# Install frontend dependencies (first time only)
npm install

# Run the frontend development server
npm run dev
```

### 6.5. Using VS Code Debug Configuration

Alternatively, run the backend in debug mode:

1. Open VS Code
2. Go to **Run and Debug** (Ctrl+Shift+D)
3. Select **"Python: Backend"** from the dropdown
4. Click the green play button or press F5

---

## Step 7: Verify All Services Are Running

Before using the application, confirm all services are running correctly:

### 7.1. Terminal Status Checklist

| Terminal | Service | Command | Expected Output | URL |
|----------|---------|---------|-----------------|-----|
| **Terminal 1** | Backend API | `python -m uvicorn app.main:app --port 8000 --reload` | `INFO: Application startup complete` | http://127.0.0.1:8000 |
| **Terminal 2** | Frontend (Dev) | `npm run dev` | `Local: http://localhost:5173/` | http://localhost:5173 |

### 7.2. Quick Verification

**1. Check Backend API:**

```bash
# In a new terminal
curl http://127.0.0.1:8000/health
# Expected: {"status":"healthy"} or similar JSON response
```

**2. Check Frontend:**

- Open browser to http://localhost:5173
- Should see the Customer Chatbot e-commerce UI
- If authentication is configured, you may be redirected to Azure AD login

### 7.3. Common Issues

**Service not starting?**

- Ensure you're in the correct directory (`src/api` for backend, `src/App` for frontend)
- Verify virtual environment is activated (you should see `(.venv)` in prompt)
- Check that port is not already in use (8000 for API, 5173 for frontend dev)
- Review error messages in the terminal

**Can't access services?**

- Verify firewall isn't blocking ports 8000 or 5173
- Try `http://localhost:port` instead of `http://127.0.0.1:port`
- Ensure services show "startup complete" messages

**Azure authentication errors?**

- Ensure you're logged in with `az login`
- Verify `APP_ENV="dev"` is set in `.env`
- Check that your account has the required RBAC roles on Azure resources

---

## Step 8: Running Tests

The project includes unit tests and code quality tools:

```bash
# Navigate to the API directory
cd src/api

# Run tests with pytest
pytest tests/ -v

# Run tests with coverage report
pytest tests/ -v --cov=app --cov-report=html
```

---

## Step 9: Next Steps

Once all services are running (as confirmed in Step 7), you can:

1. **Access the Application**: Open `http://localhost:5173` in your browser to explore the Customer Chatbot UI
2. **Browse Products**: Navigate the e-commerce interface and browse the product catalog
3. **Test Chat**: Use the integrated chat assistant to ask questions about products or policies
4. **Explore the Code**: Review the codebase starting with `src/api/app/` directory

---

## Troubleshooting

### Common Issues

#### Python Version Issues

```bash
# Check available Python versions
python3 --version
python3.11 --version

# If python3.11 not found, install it:
# Ubuntu: sudo apt install python3.11
# macOS: brew install python@3.11
# Windows: winget install Python.Python.3.11
```

#### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf .venv  # Linux/macOS
# or Remove-Item -Recurse .venv  # Windows PowerShell

python -m venv .venv

# Activate and reinstall
source .venv/bin/activate  # Linux/macOS
# or .\.venv\Scripts\Activate.ps1  # Windows

pip install -r src/api/requirements.txt
```

#### Permission Issues (Linux/macOS)

```bash
# Fix ownership of files
sudo chown -R $USER:$USER .
```

#### Windows-Specific Issues

```powershell
# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Long path support (Windows 10 1607+, run as Administrator)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Azure Authentication Issues

```bash
# Login to Azure CLI
az login

# Set subscription
az account set --subscription "your-subscription-id"

# Test authentication
az account show
```

### Environment Variable Issues

```bash
# Check environment variables are loaded
env | grep AZURE  # Linux/macOS
Get-ChildItem Env:AZURE*  # Windows PowerShell

# Validate .env file format
cat src/api/.env | grep -v '^#' | grep '='  # Should show key=value pairs
```

---

## Related Documentation

- [Deployment Guide](./DeploymentGuide.md) - Instructions for Azure deployment
- [Technical Architecture](./TechnicalArchitecture.md) - Solution architecture details
- [App Authentication Setup](./AppAuthentication.md) - Configure application authentication
- [Delete Resource Group](./DeleteResourceGroup.md) - Steps to safely delete Azure resources
- [Quota Check](./QuotaCheck.md) - Verify Azure quotas before deployment
