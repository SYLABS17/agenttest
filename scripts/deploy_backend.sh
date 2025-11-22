#!/bin/bash

#################################################################################
# Deploy Backend FastAPI Application to Azure App Service
# 
# This script builds and deploys the Python backend to Azure App Service
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
BACKEND_DIR="$PROJECT_ROOT/backend"
ENVIRONMENT="${ENVIRONMENT:-dev}"

print_status "Starting backend deployment..."
print_status "Environment: $ENVIRONMENT"
print_status "Backend directory: $BACKEND_DIR"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    print_error "Backend directory not found: $BACKEND_DIR"
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

# Check required variables
if [ -z "$APP_SERVICE_NAME" ] || [ -z "$AZURE_RESOURCE_GROUP" ]; then
    print_error "Required Azure configuration not found"
    print_error "APP_SERVICE_NAME: $APP_SERVICE_NAME"
    print_error "AZURE_RESOURCE_GROUP: $AZURE_RESOURCE_GROUP"
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Create deployment package
print_status "Creating deployment package..."

# Create temporary deployment directory
DEPLOY_DIR=$(mktemp -d)
print_status "Using temporary directory: $DEPLOY_DIR"

# Copy backend files
cp -r . "$DEPLOY_DIR/"

# Create startup command file for Azure
cat > "$DEPLOY_DIR/startup.txt" << EOF
python -m uvicorn main:app --host 0.0.0.0 --port 8000
EOF

# Create or update requirements.txt if using pyproject.toml
if [ -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then
    print_status "Generating requirements.txt from pyproject.toml..."
    if command -v poetry &> /dev/null; then
        poetry export -f requirements.txt --output "$DEPLOY_DIR/requirements.txt" --without-hashes
    else
        print_warning "Poetry not found, using existing requirements.txt"
        if [ ! -f "requirements.txt" ]; then
            print_error "No requirements.txt found and poetry not available"
            exit 1
        fi
    fi
fi

# Create App Service configuration
print_status "Configuring App Service settings..."

# Set Python version
az webapp config set \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --linux-fx-version "PYTHON|3.11" \
    --only-show-errors

# Configure app settings
print_status "Setting application configuration..."

# Read existing app settings to preserve them
EXISTING_SETTINGS=$(az webapp config appsettings list \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --query "[?name!='WEBSITE_NODE_DEFAULT_VERSION' && name!='WEBSITE_HTTPLOGGING_RETENTION_DAYS'].{name:name, value:value}" \
    -o json)

# Set new app settings
az webapp config appsettings set \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --settings \
        APP_ENV="$ENVIRONMENT" \
        APP_DEBUG="false" \
        APP_HOST="0.0.0.0" \
        APP_PORT="8000" \
        SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
        AZURE_RESOURCE_GROUP="$AZURE_RESOURCE_GROUP" \
        AZURE_LOCATION="$AZURE_LOCATION" \
    --only-show-errors

# Set connection strings if available
if [ -n "$AZURE_STORAGE_CONNECTION_STRING" ]; then
    az webapp config connection-string set \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --settings AZURE_STORAGE="$AZURE_STORAGE_CONNECTION_STRING" \
        --connection-string-type Custom \
        --only-show-errors
fi

# Enable logging
print_status "Configuring logging..."

az webapp log config \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --application-logging filesystem \
    --detailed-error-messages true \
    --failed-request-tracing true \
    --level information \
    --only-show-errors

# Deploy using ZIP deploy
print_status "Creating deployment package..."

# Create ZIP file
cd "$DEPLOY_DIR"
zip -r deploy.zip . -x "*.git*" "__pycache__/*" "*.pyc" ".env*" "tests/*" "*.pytest_cache*"

print_status "Deploying to Azure App Service..."

# Deploy the ZIP file
az webapp deployment source config-zip \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --src deploy.zip \
    --only-show-errors

# Clean up temporary directory
rm -rf "$DEPLOY_DIR"

# Wait for deployment to complete
print_status "Waiting for deployment to complete..."
sleep 30

# Check deployment status
DEPLOY_STATUS=$(az webapp show \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --query state \
    -o tsv)

if [ "$DEPLOY_STATUS" != "Running" ]; then
    print_warning "App Service is not in running state: $DEPLOY_STATUS"
    print_status "Attempting to start the app..."
    
    az webapp start \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --only-show-errors
    
    sleep 10
fi

# Test the deployment
print_status "Testing deployment..."

APP_URL=$(az webapp show \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --query defaultHostName \
    -o tsv)

HEALTH_URL="https://$APP_URL/healthz"
print_status "Testing health endpoint: $HEALTH_URL"

# Try to reach the health endpoint
MAX_ATTEMPTS=10
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    print_status "Attempt $ATTEMPT of $MAX_ATTEMPTS..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_status "Health check successful!"
        break
    elif [ "$HTTP_CODE" = "000" ]; then
        print_warning "Connection failed, waiting..."
    else
        print_warning "Received HTTP code: $HTTP_CODE"
    fi
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        print_error "Health check failed after $MAX_ATTEMPTS attempts"
        print_status "Checking application logs..."
        
        az webapp log tail \
            --resource-group "$AZURE_RESOURCE_GROUP" \
            --name "$APP_SERVICE_NAME" \
            --only-show-errors || true
        
        exit 1
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    sleep 10
done

# Display deployment information
print_status "Backend deployment completed successfully!"
echo ""
echo "===== Deployment Summary ====="
echo "Environment: $ENVIRONMENT"
echo "App Service: $APP_SERVICE_NAME"
echo "Resource Group: $AZURE_RESOURCE_GROUP"
echo "URL: https://$APP_URL"
echo "API Documentation: https://$APP_URL/docs"
echo "Health Check: https://$APP_URL/healthz"
echo ""

# Show recent logs
print_status "Recent application logs:"
az webapp log tail \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$APP_SERVICE_NAME" \
    --only-show-errors \
    --timeout 10 || true

print_status "Backend deployment completed!"
print_status "Next steps:"
echo "  1. Verify the API at: https://$APP_URL/docs"
echo "  2. Check application logs in Azure Portal"
echo "  3. Run ./deploy_frontend.sh to deploy the frontend"