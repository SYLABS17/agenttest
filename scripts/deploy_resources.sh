#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <resource-group> <location> <name-prefix> <owner-email> [environment] [cost-center]" >&2
  exit 1
fi

RESOURCE_GROUP="$1"
LOCATION="$2"
NAME_PREFIX="$3"
OWNER="$4"
ENVIRONMENT="${5:-dev}"
COST_CENTER="${6:-AI-Research}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v jq >/dev/null; then
  echo "jq is required for parsing deployment outputs. Install jq and retry." >&2
  exit 1
fi

function deploy_template() {
  local template="$1"
  local params="$2"
  local deployment_name
  deployment_name=$(basename "$template" .json)
  echo "Validating ${template}..."
  az deployment group what-if \
    --only-show-errors \
    --resource-group "$RESOURCE_GROUP" \
    --name "$deployment_name" \
    --template-file "$template" \
    --parameters $params >/tmp/whatif.log
  echo "Deploying ${template}..."
  az deployment group create \
    --only-show-errors \
    --resource-group "$RESOURCE_GROUP" \
    --name "$deployment_name" \
    --template-file "$template" \
    --parameters $params >/tmp/deploy.log
}

COMMON_PARAMS="namePrefix=${NAME_PREFIX} location=${LOCATION} environment=${ENVIRONMENT} owner=${OWNER} costCenter=${COST_CENTER}"

# 1. Monitoring foundation
deploy_template "${ROOT_DIR}/infra/monitor.json" "${COMMON_PARAMS}"

MONITOR_OUTPUT=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name monitor --query "properties.outputs" -o json || echo "{}")
LOG_ANALYTICS_ID=$(echo "$MONITOR_OUTPUT" | jq -r '.logAnalyticsWorkspaceId.value // empty')
APP_INSIGHTS_CONNECTION=$(echo "$MONITOR_OUTPUT" | jq -r '.appInsightsConnectionString.value // empty')

# 2. App Service + storage
APP_SERVICE_PARAMS="${COMMON_PARAMS} logAnalyticsWorkspaceId=${LOG_ANALYTICS_ID} appInsightsConnectionString='${APP_INSIGHTS_CONNECTION}' webAppName=${NAME_PREFIX}-web storageAccountName=${NAME_PREFIX//-}store"
deploy_template "${ROOT_DIR}/infra/app_service.json" "${APP_SERVICE_PARAMS}"

# 3. Cognitive + Azure OpenAI
VNET_ID=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name app_service --query "properties.outputs.virtualNetworkId.value" -o tsv)
PE_SUBNET_ID="${VNET_ID}/subnets/pe-subnet"
COGNITIVE_PARAMS="${COMMON_PARAMS} logAnalyticsWorkspaceId=${LOG_ANALYTICS_ID} virtualNetworkId=${VNET_ID} privateEndpointSubnetId=${PE_SUBNET_ID}"
deploy_template "${ROOT_DIR}/infra/cognitive_search.json" "${COGNITIVE_PARAMS}"

echo "Resource deployment completed."
