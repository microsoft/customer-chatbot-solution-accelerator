# Scenario-based deployment

Deploy one scenario per azd environment. The default scenario is **ecommerce** (Contoso Paints retail host + embedded chat widget).

## Quick start

```powershell
# Retail (default)
azd env new contoso-retail
azd up

# Healthcare
azd env new contoso-health
azd env set AZURE_ENV_SCENARIO healthcare
azd up

# Banking
azd env new contoso-bank
azd env set AZURE_ENV_SCENARIO banking
azd up
```

Set `AZURE_ENV_SCENARIO` **before the first `azd up`** on a new environment. It drives Bicep (`DEPLOYMENT_SCENARIO`, search indexes, welcome copy, Foundry tool names) and postprovision (data seed, agents, `VITE_SCENARIO` build arg).

Optional preflight:

```powershell
. .\infra_basic\scripts\sync_azd_hook_env.ps1
Sync-AzdHookEnv -ProjectRoot (Get-Location)
. .\infra_basic\scripts\preflight_scenario.ps1
```

## What changes per scenario

| Layer | Behavior |
|-------|----------|
| Host UI (`ecommerce-app/frontend`) | Product grid, hospital services, or banking products |
| Host API | `/api/products` (retail), `/api/services` + `/api/appointments` (healthcare), `/api/accounts` + `/api/banking/transactions` (banking) |
| Chat widget UI | Same layout; welcome text from `/api/chat/config` |
| Foundry agents | Scenario instructions + Search indexes from `scenarios/{scenario}/` |
| Cosmos / Search seed | Scenario catalog CSV + policy docs loaded on postprovision |

## Scenario packs

```
scenarios/
  ecommerce/   # default Contoso Paints
  healthcare/  # Contoso Health
  banking/     # Contoso Bank
```

Each pack contains:

- `manifest.json` — index names, branding, welcome copy
- `data/catalog.csv` — catalog seeded to Cosmos + Search
- `data/policies/` — RAG policy documents
- `agents/*.txt` — Foundry agent instructions

## Infrastructure

- `AZURE_ENV_SCENARIO` flows through [`infra_basic/main.parameters.json`](../infra_basic/main.parameters.json) → Bicep `deploymentScenario`
- App Settings: `DEPLOYMENT_SCENARIO`, `VITE_SCENARIO`, `CHAT_WELCOME_*`, Search index names, `FOUNDRY_CATALOG_TOOL_NAME`, `FOUNDRY_POLICY_TOOL_NAME`
- Foundry agents and chat runtime use matching tool names from `scenarios/{scenario}/manifest.json`
- Ecommerce frontend Docker build receives `VITE_SCENARIO` build arg via [`infra_basic/scripts/cloud_build_acr.ps1`](../infra_basic/scripts/cloud_build_acr.ps1)

## Switching scenarios

Use a **separate azd environment** per scenario. Reusing an environment requires:

1. `azd env set AZURE_ENV_SCENARIO <scenario>`
2. Re-run postprovision data/agent scripts or full `azd up`
3. Rebuild ecommerce frontend image so `VITE_SCENARIO` is baked in

## Sample chat prompts

**Ecommerce:** "What is your return policy?" / "Show me warm white paint colors"

**Healthcare:** "What are visiting hours?" / "Tell me about primary care services"

## CI

GitHub Actions workflows can set the scenario before deploy:

```yaml
- run: azd env set AZURE_ENV_SCENARIO healthcare
```

Use separate azd environment names per scenario in pipeline jobs to avoid cross-contamination of Cosmos and Search indexes.
