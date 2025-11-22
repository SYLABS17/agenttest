#!/bin/bash
set -e

# Usage: ./deploy_backend.sh <resource_group> <webapp_name>

RESOURCE_GROUP=$1
WEBAPP_NAME=$2

if [ -z "$RESOURCE_GROUP" ] || [ -z "$WEBAPP_NAME" ]; then
    if [ -f infra/outputs.json ]; then
        RESOURCE_GROUP=$(jq -r .resourceGroup infra/outputs.json)
        WEBAPP_NAME=$(jq -r .webAppName infra/outputs.json)
    else
        echo "Usage: $0 <resource_group> <webapp_name>"
        exit 1
    fi
fi

echo "Deploying Backend to $WEBAPP_NAME in $RESOURCE_GROUP..."

# Create a deployment zip of the CONTENTS of backend/
cd backend
zip -r ../backend.zip .
cd ..

# Deploy
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --src backend.zip

# Configure startup command
# Since we zipped contents, main.py is at root. 
# But wait, imports in main.py use "backend.agents..."
# If main.py is at root, "backend" package is not found unless the folder is named backend.
# This is a common issue. 
# Option 1: Zip `backend` folder (as I did originally) and use `backend.main:app`.
# Option 2: Change imports in `main.py` to relative or no "backend." prefix.

# Let's stick to Option 1 (Original Plan) as it preserves package structure.
# I will revert the logic to zip the folder, but ensure startup command is correct.

# Re-zipping folder
rm -f backend.zip
zip -r backend.zip backend/

# Deploy
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --src backend.zip

# Startup command: python -m uvicorn backend.main:app --host 0.0.0.0
az webapp config set --resource-group $RESOURCE_GROUP --name $WEBAPP_NAME --startup-file "python -m uvicorn backend.main:app --host 0.0.0.0"

echo "Backend Deployed!"
rm backend.zip
