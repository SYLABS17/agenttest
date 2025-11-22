#!/bin/bash
set -e

# Config
RESOURCE_GROUP="rg-ai-research-001"
LOCATION="eastus"
BASE_NAME="airesearch${RANDOM}"

echo "Deploying to Resource Group: $RESOURCE_GROUP"
echo "Base Name: $BASE_NAME"

# Create Resource Group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy Monitor (Log Analytics + App Insights)
echo "Deploying Monitor..."
az deployment group create \
  --name "monitor-deploy" \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/monitor.json \
  --parameters baseName=$BASE_NAME location=$LOCATION \
  --query properties.outputs > monitor_outputs.json

AI_CONN_STRING=$(jq -r .appInsightsConnectionString.value monitor_outputs.json)
echo "App Insights Connection String retrieved."

# Deploy Storage
echo "Deploying Storage..."
az deployment group create \
  --name "storage-deploy" \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/storage.json \
  --parameters baseName=$BASE_NAME location=$LOCATION

# Deploy Cognitive Search
echo "Deploying Search..."
az deployment group create \
  --name "search-deploy" \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/cognitive_search.json \
  --parameters baseName=$BASE_NAME location=$LOCATION

# Deploy AI Services
echo "Deploying AI Services..."
az deployment group create \
  --name "ai-deploy" \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/ai_services.json \
  --parameters baseName=$BASE_NAME location=$LOCATION

# Deploy App Service
echo "Deploying App Service..."
az deployment group create \
  --name "app-deploy" \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/app_service.json \
  --parameters baseName=$BASE_NAME location=$LOCATION appInsightsConnectionString="$AI_CONN_STRING" \
  --query properties.outputs > app_outputs.json

WEB_APP_NAME=$(jq -r .webAppName.value app_outputs.json)
echo "Deployment Complete!"
echo "Web App Name: $WEB_APP_NAME"

# Generate outputs.json
echo "{ \"webAppName\": \"$WEB_APP_NAME\", \"resourceGroup\": \"$RESOURCE_GROUP\" }" > infra/outputs.json
rm monitor_outputs.json app_outputs.json
