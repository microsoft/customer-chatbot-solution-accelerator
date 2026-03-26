## [Optional]: Customizing resource names 

By default this template will use the environment name as the prefix to prevent naming collisions within Azure. The parameters below show the default values. You only need to run the statements below if you need to change the values. 


> To override any of the parameters, run `azd env set <PARAMETER_NAME> <VALUE>` before running `azd up`. On the first azd command, it will prompt you for the environment name. Be sure to choose 3-16 characters alphanumeric unique name. 

## Parameters

| Name                                   | Type    | Example Value                | Purpose                                                                       |
| -------------------------------------- | ------- | ---------------------------- | ----------------------------------------------------------------------------- |
| `AZURE_LOCATION`                       | string  | `<User selects during deployment>` | Sets the Azure region for resource deployment.                                |
| `AZURE_ENV_NAME`                       | string  | `docgen`                   | Sets the environment name prefix for all Azure resources.                     |                                      |
| `AZURE_ENV_AI_SERVICE_LOCATION`                       | string  | `<User selects during deployment>` | Sets the Azure region for AI service resource deployment.  |
| `AZURE_ENV_MODEL_DEPLOYMENT_TYPE`      | string  | `Standard`                 | Defines the model deployment type (allowed: `Standard`, `GlobalStandard`).    |
| `AZURE_ENV_GPT_MODEL_NAME`                 | string  | `gpt-4o-mini`                   | Specifies the GPT model name (allowed: `gpt-4o-mini`).                    |
| `AZURE_ENV_GPT_MODEL_VERSION`                 | string  | `2024-07-18`                   | Set the Azure model version.                    |
| `AZURE_ENV_GPT_MODEL_CAPACITY`             | integer | `10`                         | Sets the GPT model capacity (based on what's available in your subscription). |
| `AZURE_ENV_EMBEDDING_DEPLOYMENT_CAPACITY` | integer | `10`                      | Sets the embedding model deployment capacity (minimum: 10).                   |
| `AZURE_ENV_CONTAINER_REGISTRY_ENDPOINT`    | string  | `ccbcontainerreg.azurecr.io` | Sets the Azure Container Registry login server/endpoint (for example: `ccbcontainerreg.azurecr.io`). |
| `AZURE_ENV_IMAGETAG`       | string  | `latest_waf`   | Set the Image tag (allowed values: latest_waf, dev, hotfix).                                   |
| `AZURE_ENV_LOG_ANALYTICS_WORKSPACE_RID` | string  | Guide to get your [Existing Workspace ID](./ReuseLogAnalytics.md)  | Reuses an existing Log Analytics Workspace instead of creating a new one.     |
| `AZURE_ENV_FOUNDRY_PROJECT_RID`    | string  | Guid to get your existing AI Foundry Project resource ID           | Reuses an existing AIFoundry and AIFoundryProject instead of creating a new one.  |
| `AZURE_ENV_VM_ADMIN_USERNAME`          | string  | `adminuser`                | The admin username for the virtual machine (used when WAF private networking is enabled). |
| `AZURE_ENV_VM_ADMIN_PASSWORD`          | string  | *(secure)*                 | The admin password for the virtual machine (used when WAF private networking is enabled). |

## How to Set a Parameter

To customize any of the above values, run the following command **before** `azd up`:

```bash
azd env set <PARAMETER_NAME> <VALUE>
```

**Example:**

```bash
azd env set AZURE_LOCATION westus2
```
