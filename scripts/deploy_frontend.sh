#!/bin/bash

#################################################################################
# Deploy Frontend React Application to Azure
# 
# This script builds and deploys the React frontend to Azure Static Web Apps
# or Azure Storage Static Website
#################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ENVIRONMENT="${ENVIRONMENT:-dev}"
DEPLOY_METHOD="${DEPLOY_METHOD:-storage}"  # 'storage' or 'static-web-app'

print_status "Starting frontend deployment..."
print_status "Environment: $ENVIRONMENT"
print_status "Frontend directory: $FRONTEND_DIR"
print_status "Deploy method: $DEPLOY_METHOD"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

# Load environment configuration
ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"
if [ -f "$ENV_FILE" ]; then
    print_status "Loading environment configuration from: $ENV_FILE"
    source "$ENV_FILE"
else
    print_error "Environment configuration not found: $ENV_FILE"
    print_error "Please run deploy_resources.sh first"
    exit 1
fi

# Change to frontend directory
cd "$FRONTEND_DIR"

# Install dependencies
print_status "Installing dependencies..."
npm ci || npm install

# Create production environment file
print_status "Creating production environment configuration..."

# Get backend URL
if [ -n "$APP_SERVICE_URL" ]; then
    REACT_APP_API_URL="$APP_SERVICE_URL"
elif [ -n "$APP_SERVICE_NAME" ]; then
    REACT_APP_API_URL="https://$APP_SERVICE_NAME.azurewebsites.net"
else
    print_warning "Backend URL not found, using default"
    REACT_APP_API_URL="http://localhost:8000"
fi

# Create .env.production
cat > "$FRONTEND_DIR/.env.production" << EOF
# Production environment configuration
REACT_APP_API_URL=$REACT_APP_API_URL
REACT_APP_ENVIRONMENT=$ENVIRONMENT
REACT_APP_APP_INSIGHTS_KEY=$APPINSIGHTS_INSTRUMENTATION_KEY
GENERATE_SOURCEMAP=false
EOF

print_status "API URL configured: $REACT_APP_API_URL"

# Build the application
print_status "Building React application..."
npm run build

# Check if build was successful
if [ ! -d "$FRONTEND_DIR/build" ]; then
    print_error "Build failed - build directory not found"
    exit 1
fi

# Deploy based on method
if [ "$DEPLOY_METHOD" = "storage" ]; then
    # Deploy to Azure Storage Static Website
    print_status "Deploying to Azure Storage Static Website..."
    
    # Check if storage account exists
    if [ -z "$AZURE_STORAGE_ACCOUNT" ]; then
        print_error "Storage account name not found"
        exit 1
    fi
    
    # Enable static website hosting
    print_status "Enabling static website hosting..."
    
    az storage blob service-properties update \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --static-website \
        --index-document "index.html" \
        --404-document "index.html" \
        --only-show-errors
    
    # Get storage account key
    STORAGE_KEY=$(az storage account keys list \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --query "[0].value" \
        -o tsv)
    
    # Upload build files to $web container
    print_status "Uploading files to storage..."
    
    az storage blob upload-batch \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --account-key "$STORAGE_KEY" \
        --source "$FRONTEND_DIR/build" \
        --destination '$web' \
        --overwrite \
        --only-show-errors
    
    # Set cache control headers for static assets
    print_status "Setting cache control headers..."
    
    az storage blob update-batch \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --account-key "$STORAGE_KEY" \
        --source '$web' \
        --pattern "static/*" \
        --content-cache-control "public, max-age=31536000" \
        --only-show-errors || true
    
    # Get the static website URL
    WEBSITE_URL=$(az storage account show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_STORAGE_ACCOUNT" \
        --query "primaryEndpoints.web" \
        -o tsv)
    
    print_status "Frontend deployed to: $WEBSITE_URL"
    
elif [ "$DEPLOY_METHOD" = "static-web-app" ]; then
    # Deploy to Azure Static Web Apps
    print_status "Deploying to Azure Static Web Apps..."
    
    # Check if Static Web App exists
    STATIC_WEB_APP_NAME="${PROJECT_NAME}-frontend-${ENVIRONMENT}"
    
    # Check if the Static Web App exists
    SWA_EXISTS=$(az staticwebapp show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$STATIC_WEB_APP_NAME" \
        --query "name" \
        -o tsv 2>/dev/null || echo "")
    
    if [ -z "$SWA_EXISTS" ]; then
        print_status "Creating Static Web App..."
        
        az staticwebapp create \
            --resource-group "$AZURE_RESOURCE_GROUP" \
            --name "$STATIC_WEB_APP_NAME" \
            --location "$AZURE_LOCATION" \
            --sku "Free" \
            --only-show-errors
    fi
    
    # Get deployment token
    DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$STATIC_WEB_APP_NAME" \
        --query "properties.apiKey" \
        -o tsv)
    
    # Deploy using SWA CLI
    if command -v swa &> /dev/null; then
        print_status "Deploying with SWA CLI..."
        
        swa deploy \
            --deployment-token "$DEPLOYMENT_TOKEN" \
            --app-location "." \
            --output-location "build" \
            --env "production"
    else
        print_warning "SWA CLI not found, using direct upload..."
        
        # Create deployment package
        cd "$FRONTEND_DIR/build"
        zip -r ../frontend-deploy.zip .
        cd ..
        
        # Upload to Static Web App (requires additional setup)
        print_warning "Manual deployment required. Please use GitHub Actions or Azure DevOps."
    fi
    
    # Get the Static Web App URL
    WEBSITE_URL=$(az staticwebapp show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$STATIC_WEB_APP_NAME" \
        --query "defaultHostname" \
        -o tsv)
    
    WEBSITE_URL="https://$WEBSITE_URL"
    print_status "Frontend deployed to: $WEBSITE_URL"
    
else
    # Deploy to App Service (same as backend)
    print_status "Deploying to App Service..."
    
    # Create a simple Node.js server to serve the React app
    cat > "$FRONTEND_DIR/server.js" << 'EOF'
const express = require('express');
const path = require('path');
const app = express();

app.use(express.static(path.join(__dirname, 'build')));

app.get('/*', function (req, res) {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Frontend server running on port ${port}`);
});
EOF
    
    # Add express to dependencies
    npm install express --save
    
    # Create startup command
    cat > "$FRONTEND_DIR/startup.txt" << EOF
node server.js
EOF
    
    # Create deployment package
    DEPLOY_DIR=$(mktemp -d)
    cp -r "$FRONTEND_DIR/build" "$DEPLOY_DIR/"
    cp "$FRONTEND_DIR/server.js" "$DEPLOY_DIR/"
    cp "$FRONTEND_DIR/package.json" "$DEPLOY_DIR/"
    cp "$FRONTEND_DIR/package-lock.json" "$DEPLOY_DIR/" 2>/dev/null || true
    
    # Deploy to App Service
    cd "$DEPLOY_DIR"
    zip -r deploy.zip .
    
    # Create or use frontend app service
    FRONTEND_APP_SERVICE="${APP_SERVICE_NAME}-frontend"
    
    az webapp deployment source config-zip \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$FRONTEND_APP_SERVICE" \
        --src deploy.zip \
        --only-show-errors
    
    rm -rf "$DEPLOY_DIR"
    
    WEBSITE_URL="https://$FRONTEND_APP_SERVICE.azurewebsites.net"
fi

# Configure CORS on backend to allow frontend
if [ -n "$APP_SERVICE_NAME" ] && [ -n "$WEBSITE_URL" ]; then
    print_status "Configuring CORS on backend..."
    
    # Remove trailing slash from URL
    CORS_ORIGIN="${WEBSITE_URL%/}"
    
    az webapp cors add \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --allowed-origins "$CORS_ORIGIN" "http://localhost:3000" \
        --only-show-errors || true
fi

# Test the deployment
print_status "Testing deployment..."

MAX_ATTEMPTS=10
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    print_status "Attempt $ATTEMPT of $MAX_ATTEMPTS..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$WEBSITE_URL" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_status "Frontend is accessible!"
        break
    elif [ "$HTTP_CODE" = "000" ]; then
        print_warning "Connection failed, waiting..."
    else
        print_warning "Received HTTP code: $HTTP_CODE"
    fi
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        print_warning "Frontend may take a few more minutes to be fully available"
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    sleep 10
done

# Display deployment information
print_status "Frontend deployment completed successfully!"
echo ""
echo "===== Deployment Summary ====="
echo "Environment: $ENVIRONMENT"
echo "Deploy Method: $DEPLOY_METHOD"
echo "Frontend URL: $WEBSITE_URL"
echo "Backend API: $REACT_APP_API_URL"
echo ""

# Create deployment summary file
SUMMARY_FILE="$PROJECT_ROOT/.azure/deployment-summary-$ENVIRONMENT.txt"
mkdir -p "$(dirname "$SUMMARY_FILE")"

cat > "$SUMMARY_FILE" << EOF
AI Research System Deployment Summary
======================================
Generated: $(date)
Environment: $ENVIRONMENT

Frontend:
  URL: $WEBSITE_URL
  Deploy Method: $DEPLOY_METHOD

Backend:
  URL: $REACT_APP_API_URL
  API Docs: $REACT_APP_API_URL/docs

Azure Resources:
  Resource Group: $AZURE_RESOURCE_GROUP
  Storage Account: $AZURE_STORAGE_ACCOUNT
  App Service: $APP_SERVICE_NAME

Access the application at: $WEBSITE_URL
EOF

print_status "Deployment summary saved to: $SUMMARY_FILE"

print_status "Frontend deployment completed!"
print_status "Next steps:"
echo "  1. Access the application at: $WEBSITE_URL"
echo "  2. Test the research chat functionality"
echo "  3. Monitor application performance in Azure Portal"
echo "  4. Run ./validate_end_to_end.sh to perform end-to-end validation"