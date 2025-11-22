#!/bin/bash

#######################################
# End-to-End Validation Script
# Usage: ./validate_end_to_end.sh [dev|test|prod]
#######################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
RESOURCE_GROUP="ai-research-system-${ENVIRONMENT}-rg"
VALIDATION_RESULTS=()
FAILED_TESTS=0
PASSED_TESTS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Research System - End-to-End Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to load deployment outputs
load_deployment_outputs() {
    echo -e "${YELLOW}Loading deployment configuration...${NC}"
    
    OUTPUT_FILE="../infra/deployment-outputs-${ENVIRONMENT}.json"
    if [ ! -f "$OUTPUT_FILE" ]; then
        echo -e "${RED}Deployment outputs not found. Run deploy_resources.sh first.${NC}"
        exit 1
    fi
    
    # Extract values from outputs
    WEB_APP_NAME=$(jq -r '.webAppName.value' "$OUTPUT_FILE")
    WEB_APP_URL=$(jq -r '.webAppUrl.value' "$OUTPUT_FILE")
    STORAGE_ACCOUNT_NAME=$(jq -r '.storageAccountName.value' "$OUTPUT_FILE")
    
    # Get static website URL
    STATIC_WEBSITE_URL=$(az storage account show \
        --name "$STORAGE_ACCOUNT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "primaryEndpoints.web" \
        --output tsv 2>/dev/null || echo "")
    
    BACKEND_URL="${WEB_APP_URL}"
    FRONTEND_URL="${STATIC_WEBSITE_URL:-$WEB_APP_URL}"
    
    echo -e "${GREEN}Configuration loaded!${NC}"
    echo "Backend URL: $BACKEND_URL"
    echo "Frontend URL: $FRONTEND_URL"
    echo ""
}

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    local check_json=${4:-false}
    
    echo -n "Testing $name... "
    
    RESPONSE=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    STATUS_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$STATUS_CODE" == "$expected_status" ]; then
        if [ "$check_json" == "true" ] && ! echo "$BODY" | jq . >/dev/null 2>&1; then
            echo -e "${RED}✗ Invalid JSON response${NC}"
            ((FAILED_TESTS++))
            VALIDATION_RESULTS+=("$name: FAILED (Invalid JSON)")
        else
            echo -e "${GREEN}✓ Passed (Status: $STATUS_CODE)${NC}"
            ((PASSED_TESTS++))
            VALIDATION_RESULTS+=("$name: PASSED")
        fi
    else
        echo -e "${RED}✗ Failed (Expected: $expected_status, Got: $STATUS_CODE)${NC}"
        ((FAILED_TESTS++))
        VALIDATION_RESULTS+=("$name: FAILED (Status: $STATUS_CODE)")
    fi
}

# Function to test API functionality
test_api_functionality() {
    local endpoint=$1
    local method=$2
    local data=$3
    local name=$4
    
    echo -n "Testing $name... "
    
    if [ "$method" == "POST" ]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$endpoint" 2>/dev/null || echo "000")
    else
        RESPONSE=$(curl -s -w "\n%{http_code}" "$endpoint" 2>/dev/null || echo "000")
    fi
    
    STATUS_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$STATUS_CODE" == "200" ] || [ "$STATUS_CODE" == "201" ]; then
        if echo "$BODY" | jq . >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Passed${NC}"
            ((PASSED_TESTS++))
            VALIDATION_RESULTS+=("$name: PASSED")
            
            # Display partial response
            echo "  Response preview: $(echo "$BODY" | jq -c '. | {success: .success, status: .status}' 2>/dev/null || echo "Valid response")"
        else
            echo -e "${RED}✗ Invalid response${NC}"
            ((FAILED_TESTS++))
            VALIDATION_RESULTS+=("$name: FAILED (Invalid response)")
        fi
    else
        echo -e "${RED}✗ Failed (Status: $STATUS_CODE)${NC}"
        ((FAILED_TESTS++))
        VALIDATION_RESULTS+=("$name: FAILED (Status: $STATUS_CODE)")
    fi
}

# Function to run infrastructure tests
test_infrastructure() {
    echo -e "${BLUE}1. Infrastructure Tests${NC}"
    echo "------------------------"
    
    # Test Resource Group
    echo -n "Checking Resource Group... "
    if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
        echo -e "${GREEN}✓ Exists${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗ Not found${NC}"
        ((FAILED_TESTS++))
    fi
    
    # Test App Service
    echo -n "Checking App Service... "
    if az webapp show --name "$WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        echo -e "${GREEN}✓ Exists${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗ Not found${NC}"
        ((FAILED_TESTS++))
    fi
    
    # Test Storage Account
    echo -n "Checking Storage Account... "
    if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        echo -e "${GREEN}✓ Exists${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗ Not found${NC}"
        ((FAILED_TESTS++))
    fi
    
    echo ""
}

# Function to run backend tests
test_backend() {
    echo -e "${BLUE}2. Backend API Tests${NC}"
    echo "---------------------"
    
    # Test root endpoint
    test_endpoint "Root endpoint" "$BACKEND_URL/" 200 true
    
    # Test health endpoint
    test_endpoint "Health endpoint" "$BACKEND_URL/health" 200 true
    
    # Test API documentation
    test_endpoint "API Documentation" "$BACKEND_URL/docs" 200 false
    
    # Test metrics endpoint
    test_endpoint "Metrics endpoint" "$BACKEND_URL/api/metrics" 200 true
    
    # Test agents status
    test_endpoint "Agents status" "$BACKEND_URL/api/agents/status" 200 true
    
    # Test research endpoint with dummy query
    test_api_functionality \
        "$BACKEND_URL/api/test/dummy-query" \
        "POST" \
        "" \
        "Dummy query test"
    
    # Test research endpoint with custom query
    RESEARCH_DATA='{"query":"Test validation query","include_evaluation":false}'
    test_api_functionality \
        "$BACKEND_URL/api/research" \
        "POST" \
        "$RESEARCH_DATA" \
        "Research endpoint"
    
    echo ""
}

# Function to run frontend tests
test_frontend() {
    echo -e "${BLUE}3. Frontend Tests${NC}"
    echo "------------------"
    
    if [ -z "$STATIC_WEBSITE_URL" ]; then
        echo -e "${YELLOW}Static website URL not available, skipping frontend tests${NC}"
        return
    fi
    
    # Test frontend homepage
    test_endpoint "Frontend homepage" "$FRONTEND_URL" 200 false
    
    # Test static assets
    echo -n "Checking static assets... "
    # Try to find a CSS or JS file
    ASSET_CHECK=$(curl -s "$FRONTEND_URL" | grep -E "(\.css|\.js)" | head -n 1)
    if [ -n "$ASSET_CHECK" ]; then
        echo -e "${GREEN}✓ Assets loading${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${YELLOW}⚠ Could not verify assets${NC}"
    fi
    
    echo ""
}

# Function to run integration tests
test_integration() {
    echo -e "${BLUE}4. Integration Tests${NC}"
    echo "---------------------"
    
    # Test complete research flow
    echo -n "Testing complete research flow... "
    
    RESEARCH_REQUEST='{
        "query": "Integration test: AI in healthcare",
        "include_evaluation": true
    }'
    
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$RESEARCH_REQUEST" \
        "$BACKEND_URL/api/research" 2>/dev/null)
    
    if echo "$RESPONSE" | jq -e '.success == true and .report != null and .chat_history != null' >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Research flow working${NC}"
        ((PASSED_TESTS++))
        
        # Extract metrics
        PROCESSING_TIME=$(echo "$RESPONSE" | jq '.processing_time_ms' 2>/dev/null)
        CHAT_COUNT=$(echo "$RESPONSE" | jq '.chat_history | length' 2>/dev/null)
        
        echo "  Processing time: ${PROCESSING_TIME}ms"
        echo "  Chat messages: ${CHAT_COUNT}"
    else
        echo -e "${RED}✗ Research flow failed${NC}"
        ((FAILED_TESTS++))
    fi
    
    echo ""
}

# Function to run performance tests
test_performance() {
    echo -e "${BLUE}5. Performance Tests${NC}"
    echo "---------------------"
    
    # Test response times
    echo "Testing response times..."
    
    endpoints=(
        "$BACKEND_URL/health"
        "$BACKEND_URL/api/metrics"
        "$BACKEND_URL/api/agents/status"
    )
    
    for endpoint in "${endpoints[@]}"; do
        echo -n "  $(basename "$endpoint"): "
        
        TIME=$(curl -s -o /dev/null -w "%{time_total}" "$endpoint" 2>/dev/null)
        TIME_MS=$(echo "$TIME * 1000" | bc 2>/dev/null || echo "0")
        
        if (( $(echo "$TIME_MS < 1000" | bc -l) )); then
            echo -e "${GREEN}${TIME_MS}ms ✓${NC}"
            ((PASSED_TESTS++))
        elif (( $(echo "$TIME_MS < 2000" | bc -l) )); then
            echo -e "${YELLOW}${TIME_MS}ms ⚠${NC}"
            ((PASSED_TESTS++))
        else
            echo -e "${RED}${TIME_MS}ms ✗${NC}"
            ((FAILED_TESTS++))
        fi
    done
    
    echo ""
}

# Function to run security tests
test_security() {
    echo -e "${BLUE}6. Security Tests${NC}"
    echo "------------------"
    
    # Test HTTPS enforcement
    echo -n "Testing HTTPS enforcement... "
    if [[ "$BACKEND_URL" == https://* ]] && [[ "$FRONTEND_URL" == https://* ]]; then
        echo -e "${GREEN}✓ HTTPS enabled${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗ HTTPS not enforced${NC}"
        ((FAILED_TESTS++))
    fi
    
    # Test CORS headers
    echo -n "Testing CORS configuration... "
    CORS_HEADER=$(curl -s -I "$BACKEND_URL/api/health" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
    if [ -n "$CORS_HEADER" ]; then
        echo -e "${GREEN}✓ CORS configured${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${YELLOW}⚠ CORS headers not found${NC}"
    fi
    
    # Test authentication endpoints (should fail without auth)
    echo -n "Testing unauthorized access protection... "
    # This is a placeholder - implement based on your auth strategy
    echo -e "${YELLOW}⚠ Auth tests not implemented${NC}"
    
    echo ""
}

# Function to display results summary
display_summary() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Validation Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))
    
    echo "Environment: $ENVIRONMENT"
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ All tests passed! The deployment is working correctly.${NC}"
    else
        echo ""
        echo -e "${RED}❌ Some tests failed. Please review the results above.${NC}"
        echo ""
        echo "Failed tests:"
        for result in "${VALIDATION_RESULTS[@]}"; do
            if [[ $result == *"FAILED"* ]]; then
                echo "  - $result"
            fi
        done
    fi
    
    echo ""
    echo -e "${BLUE}Access Points:${NC}"
    echo "Backend API: $BACKEND_URL"
    echo "API Documentation: $BACKEND_URL/docs"
    if [ -n "$FRONTEND_URL" ]; then
        echo "Frontend Application: $FRONTEND_URL"
    fi
    
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    if [ $FAILED_TESTS -eq 0 ]; then
        echo "1. Access the frontend application"
        echo "2. Try some research queries"
        echo "3. Monitor the metrics dashboard"
        echo "4. Review application logs"
    else
        echo "1. Review failed tests above"
        echo "2. Check application logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
        echo "3. Verify deployment status in Azure Portal"
        echo "4. Re-run failed deployments if necessary"
    fi
}

# Main execution
main() {
    echo "Environment: $ENVIRONMENT"
    echo "Starting validation tests..."
    echo ""
    
    load_deployment_outputs
    
    test_infrastructure
    test_backend
    test_frontend
    test_integration
    test_performance
    test_security
    
    display_summary
    
    # Exit with error code if tests failed
    if [ $FAILED_TESTS -gt 0 ]; then
        exit 1
    fi
}

# Run main function
main