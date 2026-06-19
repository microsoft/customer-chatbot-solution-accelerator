## [Optional]: Customizing resource names 

By default this template will use the environment name as the prefix to prevent naming collisions within Azure. The parameters below show the default values. You only need to run the statements below if you need to change the values.

> To override any of the parameters, run `azd env set <PARAMETER_NAME> <VALUE>` before running `azd up`. On the first azd command, it will prompt you for the environment name. Be sure to choose 3-16 characters alphanumeric unique name.

## Parameters

| Name                                   | Type    | Example Value                | Purpose                                                                       |
| -------------------------------------- | ------- | ---------------------------- | ----------------------------------------------------------------------------- |
| `DEPLOYMENT_FLAVOR`                    | string  | `bicep`                      | **Deployment mode** - Controls which infrastructure modules are used:<br/>• `bicep` (default): Vanilla Bicep for dev/test<br/>• `avm`: AVM production without private networking<br/>• `avm-waf`: AVM with WAF features and private networking<br/>|
| `AZURE_LOCATION`                       | string  | `<User selects during deployment>` | Sets the Azure region for resource deployment.                                |
| `AZURE_ENV_NAME`                       | string  | `docgen`                   | Sets the environment name prefix for all Azure resources.                     |                                      |
| `AZURE_ENV_AI_SERVICE_LOCATION`                       | string  | `<User selects during deployment>` | Sets the Azure region for AI service resource deployment.  |
| `AZURE_ENV_MODEL_DEPLOYMENT_TYPE`      | string  | `Standard`                 | Defines the model deployment type (allowed: `Standard`, `GlobalStandard`).    |
| `AZURE_ENV_GPT_MODEL_NAME`                 | string  | `gpt-4.1-mini`                   | Specifies the GPT model name (allowed: `gpt-4.1-mini`).                    |
| `AZURE_ENV_GPT_MODEL_VERSION`                 | string  | `2025-04-14`                   | Set the Azure model version.                    |
| `AZURE_ENV_GPT_MODEL_CAPACITY`             | integer | `10`                         | Sets the GPT model capacity (based on what's available in your subscription). |
| `AZURE_ENV_EMBEDDING_DEPLOYMENT_CAPACITY` | integer | `10`                      | Sets the embedding model deployment capacity (minimum: 10).                   |
| `AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT`    | string  | `ccbcontainerreg.azurecr.io` | Sets the Azure Container Registry login server/endpoint (for example: `ccbcontainerreg.azurecr.io`). |
| `AZURE_ENV_ACR_NAME`       | string  | *(derived)*   | Short ACR name passed to **`az acr build --registry`** in **`infra/scripts/build_*_acr`** scripts; optional if the endpoint is set (name is parsed from **`AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT`**). |
| `AZURE_ENV_IMAGETAG`       | string  | `latest_v2`   | Tag used for both App Service container pins and **`az acr build`** scripts (`latest`, `dev`, `demo`, `latest_v2`, or a SHA/time stamp). |
| `AZURE_ENV_SCENARIO`       | string  | `ecommerce`   | Deployment scenario: `ecommerce` (default), `healthcare`, or `banking`. See [scenario-deployment-guide.md](./scenario-deployment-guide.md). |
| `AZURE_ENV_FRONTEND_IMAGE_REPO` | string | *(per app)* | Overrides Bicep **`frontendImageRepository`**: chat default **`ccsa-chat-frontend`**, ecommerce default **`ccsa-ecom-frontend`**. |
| `AZURE_ENV_BACKEND_IMAGE_REPO` | string | *(per app)* | Overrides Bicep **`backendImageRepository`**: chat default **`ccsa-chat-backend`**, ecommerce default **`ccsa-ecom-backend`**. |
| `AZURE_ENV_EXISTING_LOG_ANALYTICS_WORKSPACE_RID` | string  | Guide to get your [Existing Workspace Resource ID](./ReuseLogAnalytics.md)  | Reuses an existing Log Analytics Workspace instead of creating a new one.     |
| `AZURE_EXISTING_AIPROJECT_RESOURCE_ID`    | string  | Guide to get your existing [Existing Foundry Project Resource ID](./ReuseFoundryProject.md)           | Reuses an existing AIFoundry and AIFoundryProject instead of creating a new one.  |
| `AZURE_ENV_VM_ADMIN_USERNAME`          | string  | `testvmuser`               | **Optional (Entra ID Auth is default):** The admin username for the VM. Only set if using traditional username/password auth instead of Microsoft Entra ID authentication (not recommended). |
| `AZURE_ENV_VM_ADMIN_PASSWORD`          | string  | *(secure)*                 | **Optional (Entra ID Auth is default):** The admin password for the VM. Only set if using traditional username/password auth instead of Microsoft Entra ID authentication (not recommended). |
| `AZURE_ENV_VM_SIZE`  | string | `Standard_D2s_v5`               | The size/SKU of the Jumpbox Virtual Machine for WAF/private-networking deployments (e.g., `Standard_D2s_v5`, `Standard_DS2_v2`).         |

## How to Set a Parameter

To customize any of the above values, run the following command **before** `azd up`:

```bash
azd env set <PARAMETER_NAME> <VALUE>
```

**Examples:**

```bash
# Set deployment region
azd env set AZURE_LOCATION westus2

## Deployment Flavor Examples
# Default: Vanilla Bicep
azd env set DEPLOYMENT_FLAVOR bicep

# AVM non-WAF (enterprise-grade without private networking)
azd env set DEPLOYMENT_FLAVOR avm

# AVM WAF-aligned (production with private networking)
azd env set DEPLOYMENT_FLAVOR avm-waf
```