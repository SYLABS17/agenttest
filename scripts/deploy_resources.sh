#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="${ROOT_DIR}/infra"

RESOURCE_GROUP="${RESOURCE_GROUP:?Set RESOURCE_GROUP to the target RG}"
LOCATION="${LOCATION:?Set LOCATION to the Azure region (e.g. eastus2)}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
OWNER="${OWNER:-ai-foundry}"
COST_CENTER="${COST_CENTER:-RND}"
BASE_NAME="${BASE_NAME:-aiaresearch}"
ALERT_EMAIL="${ALERT_EMAIL:-}"
SUBSCRIPTION_ID="${SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}"
SUBNET_RESOURCE_ID="${SUBNET_RESOURCE_ID:?Set SUBNET_RESOURCE_ID for private endpoints}"
PRIVATE_DNS_ZONE_ID="${PRIVATE_DNS_ZONE_ID:?Set PRIVATE_DNS_ZONE_ID for private endpoint DNS}"

log() {
  printf "\n[%s] %s\n" "$(date '+%H:%M:%S')" "$*"
}

extract_output() {
  local payload="$1"
  local key="$2"
  printf '%s' "$payload" | python3 - "$key" <<'PY'
import json, sys
key = sys.argv[1]
data = json.loads(sys.stdin.read() or "{}")
value = data.get("properties", {}).get("outputs", {}).get(key, {}).get("value")
if value is None:
    sys.exit(1)
print(value)
PY
}

log "Ensuring resource group ${RESOURCE_GROUP} exists..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --only-show-errors >/dev/null

log "Deploying monitoring foundation..."
monitor_result=$(az deployment group create \
  --only-show-errors \
  --name "${BASE_NAME}-monitor" \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "${TEMPLATE_DIR}/monitor.json" \
  --parameters baseName="$BASE_NAME" environment="$ENVIRONMENT" owner="$OWNER" costCenter="$COST_CENTER" location="$LOCATION" alertEmail="$ALERT_EMAIL" \
  --output json)

LOG_ANALYTICS_ID=$(extract_output "$monitor_result" "logAnalyticsWorkspaceId")
APP_INSIGHTS_CONNECTION=$(extract_output "$monitor_result" "appInsightsConnectionString")

log "Deploying App Service plan, web apps, storage, and networking..."
appsvc_result=$(az deployment group create \
  --only-show-errors \
  --name "${BASE_NAME}-appsvc" \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "${TEMPLATE_DIR}/app_service.json" \
  --parameters baseName="$BASE_NAME" \
               environment="$ENVIRONMENT" \
               owner="$OWNER" \
               costCenter="$COST_CENTER" \
               location="$LOCATION" \
               logAnalyticsWorkspaceId="$LOG_ANALYTICS_ID" \
               appInsightsConnectionString="$APP_INSIGHTS_CONNECTION" \
               subnetResourceId="$SUBNET_RESOURCE_ID" \
               privateDnsZoneId="$PRIVATE_DNS_ZONE_ID" \
  --output json)

STORAGE_ACCOUNT_NAME=$(extract_output "$appsvc_result" "storageAccountName")
BACKEND_APP_NAME=$(extract_output "$appsvc_result" "backendAppName")
FRONTEND_APP_NAME=$(extract_output "$appsvc_result" "frontendAppName")

STORAGE_ACCOUNT_ID="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT_NAME}"

log "Deploying Cognitive Search, Azure OpenAI, and Language resources..."
az deployment group create \
  --only-show-errors \
  --name "${BASE_NAME}-cog" \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "${TEMPLATE_DIR}/cognitive_search.json" \
  --parameters baseName="$BASE_NAME" \
               environment="$ENVIRONMENT" \
               owner="$OWNER" \
               costCenter="$COST_CENTER" \
               location="$LOCATION" \
               logAnalyticsWorkspaceId="$LOG_ANALYTICS_ID" \
               subnetResourceId="$SUBNET_RESOURCE_ID" \
               privateDnsZoneId="$PRIVATE_DNS_ZONE_ID" \
               archiveStorageAccountId="$STORAGE_ACCOUNT_ID" \
  >/dev/null

log "Resource deployment complete."
printf "\nBackend URL: https://%s.azurewebsites.net\nFrontend URL: https://%s.azurewebsites.net\n" "$BACKEND_APP_NAME" "$FRONTEND_APP_NAME"
