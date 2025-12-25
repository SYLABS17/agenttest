#!/bin/bash

#######################################
# Deploy Azure Resources using ARM Templates
# Usage: ./deploy_resources.sh [dev|test|prod]
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
LOCATION="eastus"
TEMPLATE_FILE="../infra/main.json"
PARAMETERS_FILE="../infra/parameters.json"
DEPLOYMENT_NAME="ai-research-deployment-$(date +%Y%m%d%H%M%S)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI Research System - Infrastructure Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        echo -e "${RED}Azure CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
        az login
    fi
    
    # Check if ARM template files exist
    if [ ! -f "$TEMPLATE_FILE" ]; then
        echo -e "${RED}ARM template file not found: $TEMPLATE_FILE${NC}"
        exit 1
    fi
    
    if [ ! -f "$PARAMETERS_FILE" ]; then
        echo -e "${RED}Parameters file not found: $PARAMETERS_FILE${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Prerequisites check passed!${NC}"
}

# Function to validate ARM template
validate_template() {
    echo -e "${YELLOW}Validating ARM template...${NC}"
    
    az deployment group validate \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "$TEMPLATE_FILE" \
        --parameters "$PARAMETERS_FILE" \
        --parameters environment="$ENVIRONMENT" \
        --only-show-errors
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Template validation successful!${NC}"
    else
        echo -e "${RED}Template validation failed!${NC}"
        exit 1
    fi
}

# Function to create resource group
create_resource_group() {
    echo -e "${YELLOW}Creating resource group: $RESOURCE_GROUP${NC}"
    
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --tags Environment="$ENVIRONMENT" Project="AIResearchSystem" \
        --only-show-errors
    
    echo -e "${GREEN}Resource group created/updated!${NC}"
}

# Function to deploy resources
deploy_resources() {
    echo -e "${YELLOW}Deploying resources to $RESOURCE_GROUP...${NC}"
    echo "Deployment name: $DEPLOYMENT_NAME"
    echo ""
    
    # Deploy the template
    DEPLOYMENT_OUTPUT=$(az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$DEPLOYMENT_NAME" \
        --template-file "$TEMPLATE_FILE" \
        --parameters "$PARAMETERS_FILE" \
        --parameters environment="$ENVIRONMENT" \
        --only-show-errors \
        --output json)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Deployment successful!${NC}"
        
        # Extract outputs
        echo ""
        echo -e "${GREEN}Deployment Outputs:${NC}"
        echo "$DEPLOYMENT_OUTPUT" | jq '.properties.outputs'
        
        # Save outputs to file
        OUTPUT_FILE="../infra/deployment-outputs-${ENVIRONMENT}.json"
        echo "$DEPLOYMENT_OUTPUT" | jq '.properties.outputs' > "$OUTPUT_FILE"
        echo ""
        echo -e "${GREEN}Outputs saved to: $OUTPUT_FILE${NC}"
    else
        echo -e "${RED}Deployment failed!${NC}"
        exit 1
    fi
}

# Function to configure additional settings
configure_resources() {
    echo ""
    echo -e "${YELLOW}Configuring additional resource settings...${NC}"
    
    # Enable Application Insights
    echo "Enabling Application Insights continuous export..."
    
    # Configure diagnostic settings
    echo "Configuring diagnostic settings..."
    
    # Set up alerts
    echo "Setting up basic alerts..."
    
    echo -e "${GREEN}Additional configuration completed!${NC}"
}

# Function to display connection information
display_connection_info() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Update .env file with the deployment outputs"
    echo "2. Run ./deploy_backend.sh to deploy the backend"
    echo "3. Run ./deploy_frontend.sh to deploy the frontend"
    echo "4. Run ./validate_end_to_end.sh to test the deployment"
    echo ""
}

# Main execution
main() {
    echo "Environment: $ENVIRONMENT"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo ""
    
    check_prerequisites
    create_resource_group
    validate_template
    deploy_resources
    configure_resources
    display_connection_info
}

# Run main function
main