#!/bin/bash

#######################################
# Deploy Frontend to Azure Storage Static Website
# Usage: ./deploy_frontend.sh [dev|test|prod]
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
FRONTEND_DIR="../frontend"
TEMP_BUILD_DIR="/tmp/ai-research-frontend-build-${ENVIRONMENT}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI Research System - Frontend Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to check Node.js and npm
check_nodejs() {
    echo -e "${YELLOW}Checking Node.js and npm...${NC}"
    
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Node.js is not installed. Please install Node.js first.${NC}"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}npm is not installed. Please install npm first.${NC}"
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    
    echo "Node.js version: $NODE_VERSION"
    echo "npm version: $NPM_VERSION"
    echo -e "${GREEN}Node.js and npm check passed!${NC}"
}

# Function to load deployment outputs
load_deployment_outputs() {
    echo ""
    echo -e "${YELLOW}Loading deployment outputs...${NC}"
    
    OUTPUT_FILE="../infra/deployment-outputs-${ENVIRONMENT}.json"
    if [ ! -f "$OUTPUT_FILE" ]; then
        echo -e "${RED}Deployment outputs not found. Run deploy_resources.sh first.${NC}"
        exit 1
    fi
    
    # Extract values from outputs
    WEB_APP_NAME=$(jq -r '.webAppName.value' "$OUTPUT_FILE")
    WEB_APP_URL=$(jq -r '.webAppUrl.value' "$OUTPUT_FILE")
    STORAGE_ACCOUNT_NAME=$(jq -r '.storageAccountName.value' "$OUTPUT_FILE")
    STORAGE_CONNECTION=$(jq -r '.storageConnectionString.value' "$OUTPUT_FILE")
    
    # Backend API URL
    BACKEND_URL="${WEB_APP_URL}"
    
    echo -e "${GREEN}Deployment outputs loaded!${NC}"
    echo "Storage Account: $STORAGE_ACCOUNT_NAME"
    echo "Backend URL: $BACKEND_URL"
}

# Function to build frontend
build_frontend() {
    echo ""
    echo -e "${YELLOW}Building frontend application...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies
    echo "Installing dependencies..."
    npm ci --prefer-offline --no-audit
    
    # Create production .env
    cat > .env.production << EOF
VITE_API_URL=$BACKEND_URL
VITE_ENVIRONMENT=$ENVIRONMENT
EOF
    
    # Build for production
    echo "Building for production..."
    npm run build
    
    # Copy build to temp directory
    rm -rf "$TEMP_BUILD_DIR"
    cp -r dist "$TEMP_BUILD_DIR"
    
    echo -e "${GREEN}Frontend build complete!${NC}"
}

# Function to enable static website hosting
enable_static_website() {
    echo ""
    echo -e "${YELLOW}Enabling static website hosting...${NC}"
    
    # Enable static website on storage account
    az storage blob service-properties update \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --static-website \
        --index-document "index.html" \
        --404-document "index.html" \
        --only-show-errors
    
    # Get the static website URL
    STATIC_WEBSITE_URL=$(az storage account show \
        --name "$STORAGE_ACCOUNT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "primaryEndpoints.web" \
        --output tsv)
    
    echo -e "${GREEN}Static website hosting enabled!${NC}"
    echo "Static Website URL: $STATIC_WEBSITE_URL"
}

# Function to deploy to Azure Storage
deploy_to_storage() {
    echo ""
    echo -e "${YELLOW}Deploying frontend to Azure Storage...${NC}"
    
    # Upload files to $web container
    az storage blob upload-batch \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --source "$TEMP_BUILD_DIR" \
        --destination '$web' \
        --overwrite \
        --only-show-errors
    
    # Set cache control for static assets
    echo "Setting cache control headers..."
    
    # Set long cache for assets with hash in filename
    az storage blob list \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --container-name '$web' \
        --prefix "assets/" \
        --query "[].name" \
        --output tsv | while read -r blob; do
        az storage blob update \
            --account-name "$STORAGE_ACCOUNT_NAME" \
            --container-name '$web' \
            --name "$blob" \
            --content-cache-control "public, max-age=31536000, immutable" \
            --only-show-errors
    done
    
    # Set short cache for index.html
    az storage blob update \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --container-name '$web' \
        --name "index.html" \
        --content-cache-control "no-cache, no-store, must-revalidate" \
        --only-show-errors
    
    echo -e "${GREEN}Frontend deployed successfully!${NC}"
}

# Function to configure CDN (optional)
configure_cdn() {
    echo ""
    echo -e "${YELLOW}Configuring CDN (optional)...${NC}"
    
    read -p "Do you want to configure Azure CDN? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        CDN_PROFILE_NAME="ai-research-cdn-${ENVIRONMENT}"
        CDN_ENDPOINT_NAME="ai-research-endpoint-${ENVIRONMENT}"
        
        # Create CDN profile
        az cdn profile create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$CDN_PROFILE_NAME" \
            --sku "Standard_Microsoft" \
            --only-show-errors
        
        # Create CDN endpoint
        az cdn endpoint create \
            --resource-group "$RESOURCE_GROUP" \
            --profile-name "$CDN_PROFILE_NAME" \
            --name "$CDN_ENDPOINT_NAME" \
            --origin "${STORAGE_ACCOUNT_NAME}.blob.core.windows.net" \
            --origin-host-header "${STORAGE_ACCOUNT_NAME}.blob.core.windows.net" \
            --enable-compression \
            --only-show-errors
        
        CDN_URL="https://${CDN_ENDPOINT_NAME}.azureedge.net"
        echo -e "${GREEN}CDN configured!${NC}"
        echo "CDN URL: $CDN_URL"
    else
        echo "Skipping CDN configuration."
    fi
}

# Function to deploy to App Service (alternative)
deploy_to_app_service_static() {
    echo ""
    echo -e "${YELLOW}Alternative: Deploy to App Service static hosting...${NC}"
    
    # This function deploys the frontend to the same App Service as the backend
    # under the /static path
    
    cd "$TEMP_BUILD_DIR"
    
    # Create deployment package
    zip -r frontend-static.zip . -x "*.map"
    
    # Deploy to App Service wwwroot/static
    az webapp deployment source config-zip \
        --resource-group "$RESOURCE_GROUP" \
        --name "$WEB_APP_NAME" \
        --src "frontend-static.zip" \
        --target-path "/home/site/wwwroot/static" \
        --only-show-errors || true
    
    echo "Frontend also available at: ${WEB_APP_URL}/static"
}

# Function to verify deployment
verify_deployment() {
    echo ""
    echo -e "${YELLOW}Verifying frontend deployment...${NC}"
    
    # Check if index.html is accessible
    RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$STATIC_WEBSITE_URL" || echo "000")
    
    if [ "$RESPONSE_CODE" == "200" ]; then
        echo -e "${GREEN}Frontend is accessible!${NC}"
        echo "URL: $STATIC_WEBSITE_URL"
    else
        echo -e "${YELLOW}Frontend returned status code: $RESPONSE_CODE${NC}"
        echo "It may take a few minutes for the changes to propagate."
    fi
}

# Function to display deployment info
display_deployment_info() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Frontend Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Storage Account: $STORAGE_ACCOUNT_NAME"
    echo "Frontend URL: $STATIC_WEBSITE_URL"
    echo "Backend API: $BACKEND_URL"
    echo ""
    echo -e "${YELLOW}Access the application:${NC}"
    echo "$STATIC_WEBSITE_URL"
    echo ""
    echo -e "${YELLOW}Test the integration:${NC}"
    echo "1. Open the application in your browser"
    echo "2. Try a sample research query"
    echo "3. Check the metrics page"
    echo "4. View the logs (dev mode only)"
    echo ""
}

# Function to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_BUILD_DIR"
    rm -f "$FRONTEND_DIR/.env.production"
    echo -e "${GREEN}Cleanup complete!${NC}"
}

# Main execution
main() {
    echo "Environment: $ENVIRONMENT"
    echo "Resource Group: $RESOURCE_GROUP"
    echo ""
    
    check_nodejs
    load_deployment_outputs
    build_frontend
    enable_static_website
    deploy_to_storage
    # configure_cdn  # Optional
    # deploy_to_app_service_static  # Alternative deployment
    verify_deployment
    display_deployment_info
    cleanup
}

# Run main function
main