#!/bin/bash

#################################################################################
# Deploy Azure Resources using ARM Templates/Bicep
# 
# This script deploys all required Azure resources for the AI Research System
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

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$PROJECT_ROOT/infra"
ENVIRONMENT="${ENVIRONMENT:-dev}"
LOCATION="${LOCATION:-eastus}"
PROJECT_NAME="${PROJECT_NAME:-airesearch}"
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID}"

print_status "Starting Azure resource deployment..."
print_status "Environment: $ENVIRONMENT"
print_status "Location: $LOCATION"
print_status "Project: $PROJECT_NAME"

# Login to Azure if not already logged in
if ! az account show &> /dev/null; then
    print_status "Please login to Azure..."
    az login
fi

# Set subscription if provided
if [ -n "$SUBSCRIPTION_ID" ]; then
    print_status "Setting subscription to: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Show current subscription
CURRENT_SUB=$(az account show --query name -o tsv)
print_status "Using subscription: $CURRENT_SUB"

# Validate Bicep templates
print_status "Validating Bicep templates..."
if [ -f "$INFRA_DIR/main.bicep" ]; then
    az bicep build --file "$INFRA_DIR/main.bicep" --only-show-errors
    print_status "Bicep validation successful"
else
    print_warning "Bicep templates not found, checking for ARM templates..."
fi

# Create deployment name
DEPLOYMENT_NAME="ai-research-$ENVIRONMENT-$(date +%Y%m%d%H%M%S)"

# Deploy resources
print_status "Deploying resources with name: $DEPLOYMENT_NAME"

# Check if using Bicep or ARM templates
if [ -f "$INFRA_DIR/main.bicep" ]; then
    # Deploy using Bicep
    print_status "Deploying using Bicep templates..."
    
    DEPLOYMENT_OUTPUT=$(az deployment sub create \
        --name "$DEPLOYMENT_NAME" \
        --location "$LOCATION" \
        --template-file "$INFRA_DIR/main.bicep" \
        --parameters \
            environment="$ENVIRONMENT" \
            location="$LOCATION" \
            projectName="$PROJECT_NAME" \
            owner="${OWNER:-research-team}" \
            costCenter="${COST_CENTER:-RSCH-001}" \
            appServicePlanSku="${APP_SERVICE_SKU:-P1V2}" \
            searchServiceSku="${SEARCH_SKU:-standard}" \
            storageAccountSku="${STORAGE_SKU:-Standard_LRS}" \
            enablePrivateEndpoints="${ENABLE_PRIVATE_ENDPOINTS:-false}" \
            enableDiagnosticSettings="${ENABLE_DIAGNOSTICS:-true}" \
            logRetentionDays="${LOG_RETENTION_DAYS:-30}" \
        --only-show-errors \
        --query properties.outputs \
        -o json)
        
elif [ -f "$INFRA_DIR/azuredeploy.json" ]; then
    # Deploy using ARM templates
    print_status "Deploying using ARM templates..."
    
    PARAMETERS_FILE="$INFRA_DIR/parameters.json"
    if [ ! -f "$PARAMETERS_FILE" ]; then
        PARAMETERS_FILE="$INFRA_DIR/azuredeploy.parameters.json"
    fi
    
    DEPLOYMENT_OUTPUT=$(az deployment sub create \
        --name "$DEPLOYMENT_NAME" \
        --location "$LOCATION" \
        --template-file "$INFRA_DIR/azuredeploy.json" \
        --parameters "$PARAMETERS_FILE" \
        --only-show-errors \
        --query properties.outputs \
        -o json)
else
    print_error "No deployment templates found in $INFRA_DIR"
    exit 1
fi

# Check deployment status
DEPLOYMENT_STATE=$(az deployment sub show \
    --name "$DEPLOYMENT_NAME" \
    --query properties.provisioningState \
    -o tsv)

if [ "$DEPLOYMENT_STATE" != "Succeeded" ]; then
    print_error "Deployment failed with state: $DEPLOYMENT_STATE"
    print_error "Check the Azure portal for detailed error information"
    exit 1
fi

print_status "Deployment completed successfully!"

# Extract outputs
if [ -n "$DEPLOYMENT_OUTPUT" ]; then
    print_status "Deployment outputs:"
    echo "$DEPLOYMENT_OUTPUT" | jq '.'
    
    # Save outputs to file
    OUTPUT_FILE="$PROJECT_ROOT/.azure/deployment-outputs-$ENVIRONMENT.json"
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    echo "$DEPLOYMENT_OUTPUT" > "$OUTPUT_FILE"
    print_status "Outputs saved to: $OUTPUT_FILE"
    
    # Extract key values for environment configuration
    RESOURCE_GROUP=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.resourceGroupName.value')
    APP_SERVICE_NAME=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.appServiceName.value')
    APP_SERVICE_URL=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.appServiceUrl.value')
    SEARCH_SERVICE_NAME=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.searchServiceName.value')
    STORAGE_ACCOUNT_NAME=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.storageAccountName.value')
    APP_INSIGHTS_KEY=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.applicationInsightsInstrumentationKey.value')
    
    # Create environment file
    ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"
    cat > "$ENV_FILE" << EOF
# Auto-generated Azure configuration for $ENVIRONMENT environment
# Generated on $(date)

AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP=$RESOURCE_GROUP
AZURE_LOCATION=$LOCATION

# App Service
APP_SERVICE_NAME=$APP_SERVICE_NAME
APP_SERVICE_URL=$APP_SERVICE_URL

# Azure Cognitive Search
AZURE_SEARCH_SERVICE=$SEARCH_SERVICE_NAME
AZURE_SEARCH_ENDPOINT=https://$SEARCH_SERVICE_NAME.search.windows.net

# Storage
AZURE_STORAGE_ACCOUNT=$STORAGE_ACCOUNT_NAME

# Application Insights
APPINSIGHTS_INSTRUMENTATION_KEY=$APP_INSIGHTS_KEY

# Environment
APP_ENV=$ENVIRONMENT
EOF
    
    print_status "Environment configuration saved to: $ENV_FILE"
fi

# Verify resources
print_status "Verifying deployed resources..."

if [ -n "$RESOURCE_GROUP" ]; then
    RESOURCE_COUNT=$(az resource list \
        --resource-group "$RESOURCE_GROUP" \
        --query 'length(@)' \
        -o tsv)
    
    print_status "Resources deployed in resource group $RESOURCE_GROUP: $RESOURCE_COUNT"
    
    # List resources
    print_status "Deployed resources:"
    az resource list \
        --resource-group "$RESOURCE_GROUP" \
        --query '[].{Name:name, Type:type, Location:location}' \
        -o table
fi

# Set up resource locks (optional)
if [ "${ENABLE_RESOURCE_LOCKS:-false}" == "true" ]; then
    print_status "Setting up resource locks..."
    
    # Lock the resource group
    az lock create \
        --name "rg-lock-$PROJECT_NAME-$ENVIRONMENT" \
        --resource-group "$RESOURCE_GROUP" \
        --lock-type CanNotDelete \
        --notes "Prevent accidental deletion of production resources" \
        --only-show-errors
    
    print_status "Resource locks configured"
fi

# Configure Azure Key Vault (if exists)
KEY_VAULT_NAME=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.keyVaultName.value // empty')
if [ -n "$KEY_VAULT_NAME" ]; then
    print_status "Configuring Key Vault access policies..."
    
    # Get current user's object ID
    USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)
    
    # Set Key Vault access policy for current user
    az keyvault set-policy \
        --name "$KEY_VAULT_NAME" \
        --object-id "$USER_OBJECT_ID" \
        --secret-permissions get list set delete \
        --key-permissions get list create delete \
        --certificate-permissions get list create delete \
        --only-show-errors
    
    print_status "Key Vault access configured"
fi

print_status "Azure resource deployment completed successfully!"
print_status "Next steps:"
echo "  1. Review the deployed resources in Azure Portal"
echo "  2. Configure application settings in App Service"
echo "  3. Run ./deploy_backend.sh to deploy the backend application"
echo "  4. Run ./deploy_frontend.sh to deploy the frontend application"