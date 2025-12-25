#!/bin/bash

#######################################
# Deploy Backend to Azure App Service
# Usage: ./deploy_backend.sh [dev|test|prod]
#######################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
RESOURCE_GROUP="ai-research-system-${ENVIRONMENT}-rg"
BACKEND_DIR="../backend"
TEMP_DIR="/tmp/ai-research-backend-${ENVIRONMENT}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI Research System - Backend Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to load deployment outputs
load_deployment_outputs() {
    echo -e "${YELLOW}Loading deployment outputs...${NC}"
    
    OUTPUT_FILE="../infra/deployment-outputs-${ENVIRONMENT}.json"
    if [ ! -f "$OUTPUT_FILE" ]; then
        echo -e "${RED}Deployment outputs not found. Run deploy_resources.sh first.${NC}"
        exit 1
    fi
    
    # Extract values from outputs
    WEB_APP_NAME=$(jq -r '.webAppName.value' "$OUTPUT_FILE")
    APP_INSIGHTS_KEY=$(jq -r '.appInsightsInstrumentationKey.value' "$OUTPUT_FILE")
    APP_INSIGHTS_CONNECTION=$(jq -r '.appInsightsConnectionString.value' "$OUTPUT_FILE")
    SEARCH_ENDPOINT=$(jq -r '.searchServiceEndpoint.value' "$OUTPUT_FILE")
    SEARCH_KEY=$(jq -r '.searchServiceApiKey.value' "$OUTPUT_FILE")
    OPENAI_ENDPOINT=$(jq -r '.openAiEndpoint.value' "$OUTPUT_FILE")
    OPENAI_KEY=$(jq -r '.openAiKey.value' "$OUTPUT_FILE")
    STORAGE_CONNECTION=$(jq -r '.storageConnectionString.value' "$OUTPUT_FILE")
    
    echo -e "${GREEN}Deployment outputs loaded!${NC}"
    echo "Web App Name: $WEB_APP_NAME"
}

# Function to prepare backend package
prepare_backend() {
    echo ""
    echo -e "${YELLOW}Preparing backend package...${NC}"
    
    # Create temp directory
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    
    # Copy backend files
    cp -r "$BACKEND_DIR"/* "$TEMP_DIR/"
    
    # Create startup script for Azure
    cat > "$TEMP_DIR/startup.sh" << 'EOF'
#!/bin/bash
cd /home/site/wwwroot
pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
EOF
    
    chmod +x "$TEMP_DIR/startup.sh"
    
    # Create .env file with Azure resources
    cat > "$TEMP_DIR/.env" << EOF
# Azure Configuration
API_ENV=$ENVIRONMENT
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure AI Search
AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT
AZURE_SEARCH_API_KEY=$SEARCH_KEY
AZURE_SEARCH_INDEX_NAME=research-index

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CONNECTION
APPINSIGHTS_INSTRUMENTATIONKEY=$APP_INSIGHTS_KEY

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION
AZURE_STORAGE_CONTAINER_NAME=research-data

# Enable dummy mode for testing
ENABLE_DUMMY_MODE=true
EOF
    
    echo -e "${GREEN}Backend package prepared!${NC}"
}

# Function to create deployment package
create_deployment_package() {
    echo ""
    echo -e "${YELLOW}Creating deployment package...${NC}"
    
    cd "$TEMP_DIR"
    zip -r backend-deployment.zip . -x "*.pyc" -x "__pycache__/*" -x ".git/*" -x "*.pytest_cache/*"
    
    echo -e "${GREEN}Deployment package created!${NC}"
}

# Function to deploy to App Service
deploy_to_app_service() {
    echo ""
    echo -e "${YELLOW}Deploying to Azure App Service...${NC}"
    
    # Configure App Service for Python
    az webapp config set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$WEB_APP_NAME" \
        --linux-fx-version "PYTHON|3.11" \
        --startup-file "startup.sh" \
        --only-show-errors
    
    # Set app settings
    echo "Configuring app settings..."
    az webapp config appsettings set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$WEB_APP_NAME" \
        --settings \
            SCM_DO_BUILD_DURING_DEPLOYMENT=true \
            WEBSITE_RUN_FROM_PACKAGE=0 \
            API_ENV="$ENVIRONMENT" \
            ENABLE_DUMMY_MODE=true \
        --only-show-errors
    
    # Deploy the package
    echo "Deploying application..."
    az webapp deployment source config-zip \
        --resource-group "$RESOURCE_GROUP" \
        --name "$WEB_APP_NAME" \
        --src "$TEMP_DIR/backend-deployment.zip" \
        --only-show-errors
    
    echo -e "${GREEN}Backend deployed successfully!${NC}"
}

# Function to verify deployment
verify_deployment() {
    echo ""
    echo -e "${YELLOW}Verifying deployment...${NC}"
    
    WEB_APP_URL="https://${WEB_APP_NAME}.azurewebsites.net"
    
    echo "Waiting for application to start..."
    sleep 30
    
    # Check health endpoint
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${WEB_APP_URL}/health" || echo "000")
    
    if [ "$HEALTH_RESPONSE" == "200" ]; then
        echo -e "${GREEN}Health check passed!${NC}"
        echo "Application is running at: $WEB_APP_URL"
        
        # Display health details
        echo ""
        echo "Health check response:"
        curl -s "${WEB_APP_URL}/health" | jq '.' || true
    else
        echo -e "${YELLOW}Health check returned: $HEALTH_RESPONSE${NC}"
        echo "The application may still be starting. Check the logs:"
        echo "az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
    fi
}

# Function to enable logging
enable_logging() {
    echo ""
    echo -e "${YELLOW}Enabling application logging...${NC}"
    
    az webapp log config \
        --resource-group "$RESOURCE_GROUP" \
        --name "$WEB_APP_NAME" \
        --application-logging filesystem \
        --detailed-error-messages true \
        --failed-request-tracing true \
        --level information \
        --only-show-errors
    
    echo -e "${GREEN}Logging enabled!${NC}"
}

# Function to display deployment info
display_deployment_info() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Backend Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Web App Name: $WEB_APP_NAME"
    echo "URL: https://${WEB_APP_NAME}.azurewebsites.net"
    echo ""
    echo -e "${YELLOW}Available Endpoints:${NC}"
    echo "- Health: https://${WEB_APP_NAME}.azurewebsites.net/health"
    echo "- API Docs: https://${WEB_APP_NAME}.azurewebsites.net/docs"
    echo "- Research: https://${WEB_APP_NAME}.azurewebsites.net/api/research"
    echo ""
    echo -e "${YELLOW}View Logs:${NC}"
    echo "az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
    echo ""
}

# Function to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_DIR"
    echo -e "${GREEN}Cleanup complete!${NC}"
}

# Main execution
main() {
    echo "Environment: $ENVIRONMENT"
    echo "Resource Group: $RESOURCE_GROUP"
    echo ""
    
    load_deployment_outputs
    prepare_backend
    create_deployment_package
    deploy_to_app_service
    enable_logging
    verify_deployment
    display_deployment_info
    cleanup
}

# Run main function
main