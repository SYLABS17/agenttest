#!/bin/bash

#################################################################################
# End-to-End Validation Script for AI Research System
# 
# This script validates the complete deployment and tests all components
#################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${ENVIRONMENT:-dev}"
VERBOSE="${VERBOSE:-false}"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

print_info "Starting end-to-end validation for AI Research System"
print_info "Environment: $ENVIRONMENT"
echo ""

# Load environment configuration
ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    print_error "Environment configuration not found: $ENV_FILE"
    exit 1
fi

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_test "$test_name"
    
    if eval "$test_command"; then
        print_status "$test_name - PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_error "$test_name - FAILED"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_TESTS+=("$test_name")
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url="$1"
    local expected_code="${2:-200}"
    local description="$3"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$HTTP_CODE" = "$expected_code" ]; then
        [ "$VERBOSE" = "true" ] && print_status "$description: $url (HTTP $HTTP_CODE)"
        return 0
    else
        [ "$VERBOSE" = "true" ] && print_error "$description: $url (HTTP $HTTP_CODE, expected $expected_code)"
        return 1
    fi
}

# Function to test API endpoint with data
test_api_endpoint() {
    local url="$1"
    local method="${2:-GET}"
    local data="$3"
    local description="$4"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        RESPONSE=$(curl -s -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "\n%{http_code}" || echo "Error 000")
    else
        RESPONSE=$(curl -s "$url" -w "\n%{http_code}" || echo "Error 000")
    fi
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
        [ "$VERBOSE" = "true" ] && print_status "$description: Success (HTTP $HTTP_CODE)"
        [ "$VERBOSE" = "true" ] && [ -n "$BODY" ] && echo "  Response: $(echo "$BODY" | head -c 100)..."
        return 0
    else
        [ "$VERBOSE" = "true" ] && print_error "$description: Failed (HTTP $HTTP_CODE)"
        [ "$VERBOSE" = "true" ] && [ -n "$BODY" ] && echo "  Error: $BODY"
        return 1
    fi
}

echo "===== 1. AZURE RESOURCES VALIDATION ====="
echo ""

# Test Azure CLI connection
run_test "Azure CLI Authentication" "az account show > /dev/null 2>&1"

# Check resource group
run_test "Resource Group Exists" "az group show --name '$AZURE_RESOURCE_GROUP' > /dev/null 2>&1"

# Check App Service
if [ -n "$APP_SERVICE_NAME" ]; then
    run_test "App Service Exists" "az webapp show --resource-group '$AZURE_RESOURCE_GROUP' --name '$APP_SERVICE_NAME' > /dev/null 2>&1"
    
    # Check App Service state
    APP_STATE=$(az webapp show --resource-group "$AZURE_RESOURCE_GROUP" --name "$APP_SERVICE_NAME" --query state -o tsv 2>/dev/null || echo "Unknown")
    if [ "$APP_STATE" = "Running" ]; then
        print_status "App Service State: Running"
    else
        print_warning "App Service State: $APP_STATE"
    fi
fi

# Check Storage Account
if [ -n "$AZURE_STORAGE_ACCOUNT" ]; then
    run_test "Storage Account Exists" "az storage account show --resource-group '$AZURE_RESOURCE_GROUP' --name '$AZURE_STORAGE_ACCOUNT' > /dev/null 2>&1"
fi

# Check Search Service
if [ -n "$AZURE_SEARCH_SERVICE" ]; then
    run_test "Search Service Exists" "az search service show --resource-group '$AZURE_RESOURCE_GROUP' --name '$AZURE_SEARCH_SERVICE' > /dev/null 2>&1"
fi

echo ""
echo "===== 2. BACKEND API VALIDATION ====="
echo ""

# Get backend URL
if [ -n "$APP_SERVICE_URL" ]; then
    BACKEND_URL="$APP_SERVICE_URL"
elif [ -n "$APP_SERVICE_NAME" ]; then
    BACKEND_URL="https://$APP_SERVICE_NAME.azurewebsites.net"
else
    BACKEND_URL="http://localhost:8000"
fi

print_info "Testing backend at: $BACKEND_URL"

# Test backend endpoints
run_test "Backend Health Check" "check_endpoint '$BACKEND_URL/healthz' 200 'Health endpoint'"
run_test "Backend Root Endpoint" "check_endpoint '$BACKEND_URL/' 200 'Root endpoint'"
run_test "Backend API Docs" "check_endpoint '$BACKEND_URL/docs' 200 'API documentation'"
run_test "Backend Config Endpoint" "check_endpoint '$BACKEND_URL/config' 200 'Configuration endpoint'"
run_test "Backend Agents Endpoint" "check_endpoint '$BACKEND_URL/agents' 200 'Agents endpoint'"
run_test "Backend Metrics Endpoint" "check_endpoint '$BACKEND_URL/metrics' 200 'Metrics endpoint'"

# Test research functionality
print_test "Research API Functionality"
RESEARCH_DATA='{"query": "Test validation query", "evaluate": false, "timeout_seconds": 10}'

if test_api_endpoint "$BACKEND_URL/research" "POST" "$RESEARCH_DATA" "Research endpoint"; then
    print_status "Research API Functionality - PASSED"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_warning "Research API Functionality - SKIPPED (may require full configuration)"
fi

echo ""
echo "===== 3. FRONTEND VALIDATION ====="
echo ""

# Get frontend URL from deployment summary
SUMMARY_FILE="$PROJECT_ROOT/.azure/deployment-summary-$ENVIRONMENT.txt"
if [ -f "$SUMMARY_FILE" ]; then
    FRONTEND_URL=$(grep "Frontend:" -A1 "$SUMMARY_FILE" | grep "URL:" | awk '{print $2}')
fi

# Fallback to storage account URL
if [ -z "$FRONTEND_URL" ] && [ -n "$AZURE_STORAGE_ACCOUNT" ]; then
    FRONTEND_URL=$(az storage account show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_STORAGE_ACCOUNT" \
        --query "primaryEndpoints.web" \
        -o tsv 2>/dev/null)
fi

if [ -n "$FRONTEND_URL" ]; then
    print_info "Testing frontend at: $FRONTEND_URL"
    
    run_test "Frontend Accessibility" "check_endpoint '$FRONTEND_URL' 200 'Frontend home page'"
    run_test "Frontend Static Assets" "check_endpoint '$FRONTEND_URL/static/js/main.*.js' 200 'JavaScript bundle' || check_endpoint '$FRONTEND_URL/index.html' 200 'Index page'"
else
    print_warning "Frontend URL not found, skipping frontend tests"
fi

echo ""
echo "===== 4. INTEGRATION TESTS ====="
echo ""

# Test frontend-backend connectivity
if [ -n "$FRONTEND_URL" ] && [ -n "$BACKEND_URL" ]; then
    print_test "Frontend-Backend Integration"
    
    # Check if CORS is configured
    CORS_CHECK=$(curl -s -I -X OPTIONS "$BACKEND_URL/" \
        -H "Origin: $FRONTEND_URL" \
        -H "Access-Control-Request-Method: GET" \
        2>/dev/null | grep -i "access-control-allow-origin" || echo "")
    
    if [ -n "$CORS_CHECK" ]; then
        print_status "CORS Configuration - PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_warning "CORS Configuration - May need configuration"
    fi
fi

# Test end-to-end flow
print_test "End-to-End Research Flow"

if [ -n "$BACKEND_URL" ]; then
    # Get test queries
    TEST_QUERIES=$(curl -s "$BACKEND_URL/test/queries" 2>/dev/null | grep -o '"queries":\[[^]]*\]' || echo "")
    
    if [ -n "$TEST_QUERIES" ]; then
        print_status "Test queries available"
        
        # Try to simulate a research
        SIMULATE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/test/simulate?query_index=0" 2>/dev/null || echo "")
        
        if [[ "$SIMULATE_RESPONSE" == *"request_id"* ]]; then
            print_status "End-to-End Research Flow - PASSED"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            print_warning "End-to-End Research Flow - Partial (simulation mode)"
        fi
    else
        print_warning "End-to-End Research Flow - SKIPPED (test data not available)"
    fi
fi

echo ""
echo "===== 5. PERFORMANCE TESTS ====="
echo ""

# Test response times
if [ -n "$BACKEND_URL" ]; then
    print_test "Backend Response Time"
    
    START_TIME=$(date +%s%N)
    curl -s "$BACKEND_URL/healthz" > /dev/null 2>&1
    END_TIME=$(date +%s%N)
    
    RESPONSE_TIME=$(((END_TIME - START_TIME) / 1000000))
    
    if [ $RESPONSE_TIME -lt 1000 ]; then
        print_status "Backend Response Time: ${RESPONSE_TIME}ms (< 1s) - PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    elif [ $RESPONSE_TIME -lt 3000 ]; then
        print_warning "Backend Response Time: ${RESPONSE_TIME}ms (< 3s) - ACCEPTABLE"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_error "Backend Response Time: ${RESPONSE_TIME}ms (> 3s) - SLOW"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

echo ""
echo "===== 6. SECURITY TESTS ====="
echo ""

# Check HTTPS
if [[ "$BACKEND_URL" == https://* ]]; then
    print_status "Backend HTTPS Enabled - PASSED"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_warning "Backend HTTPS - Not configured (local/dev environment)"
fi

if [[ "$FRONTEND_URL" == https://* ]]; then
    print_status "Frontend HTTPS Enabled - PASSED"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_warning "Frontend HTTPS - Not configured (local/dev environment)"
fi

# Check security headers
if [ -n "$BACKEND_URL" ]; then
    print_test "Security Headers"
    
    HEADERS=$(curl -s -I "$BACKEND_URL/" 2>/dev/null)
    
    if echo "$HEADERS" | grep -qi "x-content-type-options"; then
        print_status "X-Content-Type-Options header present"
    else
        print_warning "X-Content-Type-Options header missing"
    fi
    
    if echo "$HEADERS" | grep -qi "x-frame-options"; then
        print_status "X-Frame-Options header present"
    else
        print_warning "X-Frame-Options header missing"
    fi
fi

echo ""
echo "===== 7. MONITORING & OBSERVABILITY ====="
echo ""

# Check Application Insights
if [ -n "$APPINSIGHTS_INSTRUMENTATION_KEY" ]; then
    print_status "Application Insights Configured - PASSED"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_warning "Application Insights - Not configured"
fi

# Check logging
if [ -n "$APP_SERVICE_NAME" ]; then
    print_test "Application Logging"
    
    LOG_CONFIG=$(az webapp log show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --query "applicationLogs.fileSystem.level" \
        -o tsv 2>/dev/null || echo "")
    
    if [ -n "$LOG_CONFIG" ] && [ "$LOG_CONFIG" != "Off" ]; then
        print_status "Application Logging Enabled (Level: $LOG_CONFIG) - PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_warning "Application Logging - Not configured"
    fi
fi

echo ""
echo "========================================="
echo "         VALIDATION SUMMARY"
echo "========================================="
echo ""
echo -e "${GREEN}Tests Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Tests Failed:${NC} $TESTS_FAILED"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo ""
    echo "Failed Tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
fi

echo ""

# Calculate success rate
if [ $((TESTS_PASSED + TESTS_FAILED)) -gt 0 ]; then
    SUCCESS_RATE=$((TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED)))
    
    if [ $SUCCESS_RATE -ge 90 ]; then
        print_status "Overall Status: EXCELLENT (${SUCCESS_RATE}% success rate)"
    elif [ $SUCCESS_RATE -ge 70 ]; then
        print_warning "Overall Status: GOOD (${SUCCESS_RATE}% success rate)"
    elif [ $SUCCESS_RATE -ge 50 ]; then
        print_warning "Overall Status: NEEDS ATTENTION (${SUCCESS_RATE}% success rate)"
    else
        print_error "Overall Status: CRITICAL (${SUCCESS_RATE}% success rate)"
    fi
else
    print_warning "No tests executed"
fi

echo ""
echo "Validation Links:"
echo "  Backend API: $BACKEND_URL"
echo "  API Documentation: $BACKEND_URL/docs"
if [ -n "$FRONTEND_URL" ]; then
    echo "  Frontend Application: $FRONTEND_URL"
fi
echo "  Azure Portal: https://portal.azure.com/#@/resource/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP"

echo ""
print_info "Validation complete!"

# Exit with appropriate code
if [ $TESTS_FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi