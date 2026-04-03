#!/bin/bash
# Pre-provision script: Check if capability hosts already exist on the BYO Foundry project.
# If they do, set SKIP_CAPABILITY_HOST=true to avoid 409 Conflict during deployment.
# This script runs automatically via the azd preprovision hook.

set -e

echo "=== Pre-provision: Checking Capability Host status ==="

# Get the existing AI Foundry project resource ID from azd env
EXISTING_PROJECT_ID=$(azd env get-value EXISTING_AI_FOUNDRY_AI_PROJECT_RESOURCE_ID 2>/dev/null || echo "")
ENABLE_PRIVATE_NETWORKING=$(azd env get-value ENABLE_PRIVATE_NETWORKING 2>/dev/null || echo "false")

# If no existing project or private networking is disabled, skip the check
if [ -z "$EXISTING_PROJECT_ID" ] || [ "$ENABLE_PRIVATE_NETWORKING" != "true" ]; then
  echo "No BYO Foundry project with private networking — skipping capability host check."
  azd env set SKIP_CAPABILITY_HOST "false" 2>/dev/null || true
  exit 0
fi

echo "BYO Foundry project detected: $EXISTING_PROJECT_ID"
echo "Checking for existing capability hosts..."

# Parse resource ID components
# Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}
SUBSCRIPTION_ID=$(echo "$EXISTING_PROJECT_ID" | cut -d'/' -f3)
RESOURCE_GROUP=$(echo "$EXISTING_PROJECT_ID" | cut -d'/' -f5)
ACCOUNT_NAME=$(echo "$EXISTING_PROJECT_ID" | cut -d'/' -f9)
PROJECT_NAME=$(echo "$EXISTING_PROJECT_ID" | cut -d'/' -f11)

API_VERSION="2025-06-01"

# Get access token
ACCESS_TOKEN=$(az account get-access-token --query accessToken -o tsv 2>/dev/null)
if [ -z "$ACCESS_TOKEN" ]; then
  echo "WARNING: Could not get Azure access token. Skipping capability host check."
  azd env set SKIP_CAPABILITY_HOST "false"
  exit 0
fi

# Check Account-level capability host
ACCOUNT_CAPHOST_URL="https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${ACCOUNT_NAME}/capabilityHosts?api-version=${API_VERSION}"

ACCOUNT_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  "$ACCOUNT_CAPHOST_URL" 2>/dev/null)

ACCOUNT_HTTP_CODE=$(echo "$ACCOUNT_RESPONSE" | tail -1)
ACCOUNT_BODY=$(echo "$ACCOUNT_RESPONSE" | sed '$d')

# Check Project-level capability host
PROJECT_CAPHOST_URL="https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${ACCOUNT_NAME}/projects/${PROJECT_NAME}/capabilityHosts?api-version=${API_VERSION}"

PROJECT_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  "$PROJECT_CAPHOST_URL" 2>/dev/null)

PROJECT_HTTP_CODE=$(echo "$PROJECT_RESPONSE" | tail -1)
PROJECT_BODY=$(echo "$PROJECT_RESPONSE" | sed '$d')

# Determine if capability hosts already exist
ACCOUNT_HAS_CAPHOST=false
PROJECT_HAS_CAPHOST=false

if [ "$ACCOUNT_HTTP_CODE" = "200" ]; then
  # Check if the response contains any capability host entries
  ACCOUNT_COUNT=$(echo "$ACCOUNT_BODY" | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('value',[])))" 2>/dev/null || echo "0")
  if [ "$ACCOUNT_COUNT" -gt "0" ]; then
    ACCOUNT_HAS_CAPHOST=true
    echo "  ✓ Account capability host found on: ${ACCOUNT_NAME}"
  fi
fi

if [ "$PROJECT_HTTP_CODE" = "200" ]; then
  PROJECT_COUNT=$(echo "$PROJECT_BODY" | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('value',[])))" 2>/dev/null || echo "0")
  if [ "$PROJECT_COUNT" -gt "0" ]; then
    PROJECT_HAS_CAPHOST=true
    echo "  ✓ Project capability host found on: ${PROJECT_NAME}"
  fi
fi

# Set the skip flag based on findings
if [ "$ACCOUNT_HAS_CAPHOST" = "true" ] && [ "$PROJECT_HAS_CAPHOST" = "true" ]; then
  echo ""
  echo "Both account and project capability hosts already exist."
  echo "Setting SKIP_CAPABILITY_HOST=true to avoid 409 Conflict."
  azd env set SKIP_CAPABILITY_HOST "true"
elif [ "$ACCOUNT_HAS_CAPHOST" = "true" ] || [ "$PROJECT_HAS_CAPHOST" = "true" ]; then
  echo ""
  echo "WARNING: Partial capability host configuration detected."
  echo "  Account capability host: ${ACCOUNT_HAS_CAPHOST}"
  echo "  Project capability host: ${PROJECT_HAS_CAPHOST}"
  echo "Setting SKIP_CAPABILITY_HOST=true — manual configuration may be needed."
  echo "See: https://learn.microsoft.com/azure/foundry/agents/concepts/capability-hosts"
  azd env set SKIP_CAPABILITY_HOST "true"
else
  echo ""
  echo "No existing capability hosts found — deployment will auto-configure them."
  azd env set SKIP_CAPABILITY_HOST "false"
fi

echo "=== Pre-provision: Capability Host check complete ==="
