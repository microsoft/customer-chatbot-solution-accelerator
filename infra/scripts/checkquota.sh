#!/bin/bash

# Function to trim leading and trailing whitespace
trim() {
    local var="$*"
    var="${var#"${var%%[![:space:]]*}"}"
    var="${var%"${var##*[![:space:]]}"}"
    printf '%s' "$var"
}

# Valid Azure AI regions for this accelerator.
ALLOWED_REGIONS=(
    "australiaeast"
    "centralus"
    "eastasia"
    "eastus2"
    "japaneast"
    "northeurope"
    "southeastasia"
    "uksouth"
)

# Get requested regions from the environment variable and keep only supported regions.
REGIONS=()
if [[ -n "${AZURE_REGIONS:-}" ]]; then
    IFS=',' read -ra REQUESTED_REGIONS <<< "$AZURE_REGIONS"
    for req_region in "${REQUESTED_REGIONS[@]}"; do
        req_region=$(trim "$req_region")
        for allowed in "${ALLOWED_REGIONS[@]}"; do
            if [[ "$req_region" == "$allowed" ]]; then
                REGIONS+=("$req_region")
                break
            fi
        done
    done
fi
if [[ ${#REGIONS[@]} -eq 0 ]]; then
    echo "⚠️ WARNING: No valid regions found in AZURE_REGIONS. Using built-in supported regions list."
    REGIONS=("${ALLOWED_REGIONS[@]}")
fi

SUBSCRIPTION_ID=$(trim "${AZURE_SUBSCRIPTION_ID}")
GPT_MIN_CAPACITY="${GPT_MIN_CAPACITY:-10}"
EMBEDDING_MIN_CAPACITY="${EMBEDDING_MIN_CAPACITY:-10}"
GPT_REALTIME_MIN_CAPACITY="${GPT_REALTIME_MIN_CAPACITY:-1}"

# Verify Azure CLI is already authenticated (login is handled by the workflow via OIDC)
echo "Verifying Azure CLI authentication..."
if ! az account show > /dev/null 2>&1; then
   echo "❌ Error: Not logged in to Azure CLI. Please run 'az login' and try again."
   exit 1
fi
echo "✅ Azure CLI is authenticated."

echo "🔄 Validating required environment variables..."
if [[ -z "$SUBSCRIPTION_ID" ]]; then
    echo "❌ ERROR: Missing required environment variable AZURE_SUBSCRIPTION_ID."
    exit 1
fi

echo "🔄 Setting Azure subscription..."
if ! az account set --subscription "$SUBSCRIPTION_ID"; then
    echo "❌ ERROR: Invalid subscription ID or insufficient permissions."
    exit 1
fi
echo "✅ Azure subscription set successfully."

declare -A MIN_CAPACITY=(
    ["OpenAI.GlobalStandard.gpt4.1-mini"]="${GPT_MIN_CAPACITY}"
    ["OpenAI.GlobalStandard.text-embedding-3-small"]="${EMBEDDING_MIN_CAPACITY}"
    ["OpenAI.GlobalStandard.gpt-realtime-mini"]="${GPT_REALTIME_MIN_CAPACITY}"
)

VALID_REGION=""
VALID_REGION_AVAILABLE_CAPACITY=""
for REGION in "${REGIONS[@]}"; do
    echo "----------------------------------------"
    echo "🔍 Checking region: $REGION"

    USAGE_COUNT=$(az cognitiveservices usage list --location "$REGION" --query 'length(@)' -o tsv 2>/dev/null || echo "0")
    if [[ -z "$USAGE_COUNT" || "$USAGE_COUNT" == "0" ]]; then
        echo "⚠️ WARNING: Failed to retrieve quota for region $REGION. Skipping."
        continue
    fi

    INSUFFICIENT_QUOTA=false
    REGION_GPT_AVAILABLE=""
    for MODEL in "${!MIN_CAPACITY[@]}"; do
        CURRENT_VALUE=$(az cognitiveservices usage list --location "$REGION" --query "[?name.value=='$MODEL'].currentValue | [0]" -o tsv 2>/dev/null)
        LIMIT=$(az cognitiveservices usage list --location "$REGION" --query "[?name.value=='$MODEL'].limit | [0]" -o tsv 2>/dev/null)

        if [[ -z "$CURRENT_VALUE" || -z "$LIMIT" || "$CURRENT_VALUE" == "None" || "$LIMIT" == "None" ]]; then
            echo "⚠️ WARNING: No quota information found for model: $MODEL in $REGION."
            INSUFFICIENT_QUOTA=true
            break
        fi

        CURRENT_VALUE=${CURRENT_VALUE%.*}
        LIMIT=${LIMIT%.*}
        AVAILABLE=$((LIMIT - CURRENT_VALUE))

        echo "✅ Model: $MODEL | Used: $CURRENT_VALUE | Limit: $LIMIT | Available: $AVAILABLE"

        if [[ "$MODEL" == "OpenAI.GlobalStandard.gpt4.1-mini" ]]; then
            REGION_GPT_AVAILABLE="$AVAILABLE"
        fi

        if [ "$AVAILABLE" -lt "${MIN_CAPACITY[$MODEL]}" ]; then
            echo "❌ ERROR: $MODEL in $REGION has insufficient quota."
            echo "   Required: ${MIN_CAPACITY[$MODEL]}, Available: $AVAILABLE"
            INSUFFICIENT_QUOTA=true
            break
        fi
    done

    if [ "$INSUFFICIENT_QUOTA" = false ]; then
        VALID_REGION="$REGION"
        VALID_REGION_AVAILABLE_CAPACITY="$REGION_GPT_AVAILABLE"
        break
    fi
done

if [ -z "$VALID_REGION" ]; then
    echo "❌ No region with sufficient quota found. Blocking deployment."
    echo "Required models and capacities:"
    for MODEL in "${!MIN_CAPACITY[@]}"; do
        echo "  - $MODEL: ${MIN_CAPACITY[$MODEL]}"
    done
    echo "QUOTA_FAILED=true" >> "$GITHUB_ENV"
    exit 0
else
    echo "✅ Final Region: $VALID_REGION"
    echo "✅ Available GPT Capacity: $VALID_REGION_AVAILABLE_CAPACITY"
    echo "All required models have sufficient quota:"
    for MODEL in "${!MIN_CAPACITY[@]}"; do
        echo "  ✅ $MODEL: ${MIN_CAPACITY[$MODEL]} capacity available"
    done
    echo "VALID_REGION=$VALID_REGION" >> "$GITHUB_ENV"
    echo "AVAILABLE_CAPACITY=$VALID_REGION_AVAILABLE_CAPACITY" >> "$GITHUB_ENV"
    exit 0
fi
