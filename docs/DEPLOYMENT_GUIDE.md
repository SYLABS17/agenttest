# Deployment Guide - Mobile Liveness Detection Pipeline

This guide walks you through deploying the complete liveness detection pipeline to Azure.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Configuration Reference](#configuration-reference)
5. [Mobile Client Setup](#mobile-client-setup)
6. [Testing the Deployment](#testing-the-deployment)
7. [Production Considerations](#production-considerations)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| Azure CLI | 2.50+ | [Install Guide](https://docs.microsoft.com/cli/azure/install-azure-cli) |
| Python | 3.11+ | [Download](https://www.python.org/downloads/) |
| Azure Functions Core Tools | 4.x | `npm install -g azure-functions-core-tools@4` |
| Git | 2.x | [Download](https://git-scm.com/downloads) |

### Azure Requirements

- Active Azure subscription
- Contributor access to a resource group
- Azure Face API available in your region (check [regional availability](https://azure.microsoft.com/global-infrastructure/services/?products=cognitive-services))

### Verify Prerequisites

```bash
# Check Azure CLI
az --version

# Check Python
python --version

# Check Azure Functions Core Tools
func --version

# Login to Azure
az login

# Set your subscription
az account set --subscription "<your-subscription-id>"
```

---

## Quick Start

For experienced users, here's the fast path:

```bash
# 1. Clone and navigate to the repository
cd /path/to/agenttest

# 2. Create resource group
az group create --name rg-liveness-dev --location eastus

# 3. Deploy infrastructure
az deployment group create \
  --resource-group rg-liveness-dev \
  --template-file infrastructure/main.bicep \
  --parameters environmentName=dev

# 4. Get deployment outputs
az deployment group show \
  --resource-group rg-liveness-dev \
  --name main \
  --query properties.outputs

# 5. Deploy function app code
func azure functionapp publish <function-app-name> --python

# 6. Test the endpoint
curl -X POST https://<function-app-name>.azurewebsites.net/api/sessions \
  -H "Content-Type: application/json" \
  -H "x-functions-key: <your-function-key>" \
  -d '{"client_id": "test-client", "applicant_data": {}}'
```

---

## Step-by-Step Deployment

### Step 1: Prepare Your Environment

#### 1.1 Clone the Repository

```bash
git clone <repository-url>
cd agenttest
```

#### 1.2 Create Local Settings (for local testing)

```bash
cp local.settings.json.template local.settings.json
```

Edit `local.settings.json` with your values (we'll get these after Azure deployment).

#### 1.3 Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Create Azure Resources

#### 2.1 Create Resource Group

```bash
# Choose your region (must support Azure Face API)
LOCATION="eastus"
RESOURCE_GROUP="rg-liveness-dev"
ENVIRONMENT="dev"

az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

#### 2.2 Deploy Infrastructure with Bicep

**Basic deployment (without AMS):**

```bash
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infrastructure/main.bicep \
  --parameters environmentName=$ENVIRONMENT
```

**Full deployment (with AMS configuration):**

```bash
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infrastructure/main.bicep \
  --parameters \
    environmentName=$ENVIRONMENT \
    amsBaseUrl="https://your-ams-api.example.com" \
    amsApiKey="your-ams-api-key"
```

#### 2.3 Capture Deployment Outputs

```bash
# Get all outputs
az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs -o json

# Or get specific values
FUNCTION_APP_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.functionAppName.value -o tsv)

FUNCTION_APP_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.functionAppUrl.value -o tsv)

FACE_ENDPOINT=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.faceApiEndpoint.value -o tsv)

echo "Function App: $FUNCTION_APP_NAME"
echo "Function URL: $FUNCTION_APP_URL"
echo "Face API: $FACE_ENDPOINT"
```

### Step 3: Deploy Function App Code

#### 3.1 Deploy Using Azure Functions Core Tools

```bash
# Navigate to project root
cd /path/to/agenttest

# Deploy
func azure functionapp publish $FUNCTION_APP_NAME --python
```

#### 3.2 Verify Deployment

```bash
# Check function app is running
az functionapp show \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query state -o tsv
```

### Step 4: Configure Application Settings

#### 4.1 Get Function App Key

```bash
# Get the default function key
FUNCTION_KEY=$(az functionapp keys list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query functionKeys.default -o tsv)

echo "Function Key: $FUNCTION_KEY"
```

#### 4.2 Update AMS Configuration (if not done during deployment)

```bash
# Set AMS configuration
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AMS_BASE_URL="https://your-ams-api.example.com" \
    AMS_AUTH_TYPE="api_key" \
    AMS_API_KEY="your-api-key"
```

#### 4.3 Adjust Pipeline Settings (optional)

```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    TOKEN_VALIDITY_MINUTES="15" \
    MIN_LIVENESS_CONFIDENCE="0.85" \
    REQUIRE_LIVE_FOR_AMS="true"
```

### Step 5: Verify the Deployment

#### 5.1 Health Check

```bash
curl -s "$FUNCTION_APP_URL/api/health" | jq .
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "storage": true,
    "face_api": true,
    "ams": true
  }
}
```

#### 5.2 Create a Test Session

```bash
curl -X POST "$FUNCTION_APP_URL/api/sessions" \
  -H "Content-Type: application/json" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -d '{
    "client_id": "test-client",
    "applicant_data": {
      "first_name": "Test",
      "last_name": "User",
      "email": "test@example.com"
    }
  }' | jq .
```

Expected response:
```json
{
  "session_id": "abc123...",
  "status": "token_attached",
  "token": "A1B2C3D4...",
  "token_expires_at": "2024-01-15T12:30:00Z"
}
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AZURE_FACE_ENDPOINT` | Azure Face API endpoint URL | - | Yes |
| `AZURE_FACE_KEY` | Azure Face API key | - | Yes* |
| `USE_MANAGED_IDENTITY` | Use Managed Identity for Face API | `false` | No |
| `AMS_BASE_URL` | Applicant Management System base URL | - | Yes |
| `AMS_AUTH_TYPE` | AMS auth type: `api_key`, `bearer_token`, `basic`, `oauth2_client_credentials` | `api_key` | No |
| `AMS_API_KEY` | API key for AMS | - | If auth type is `api_key` |
| `AMS_API_KEY_HEADER` | Header name for API key | `X-API-Key` | No |
| `AMS_BEARER_TOKEN` | Bearer token for AMS | - | If auth type is `bearer_token` |
| `AMS_OAUTH2_TOKEN_URL` | OAuth2 token endpoint | - | If auth type is `oauth2_client_credentials` |
| `AMS_OAUTH2_CLIENT_ID` | OAuth2 client ID | - | If auth type is `oauth2_client_credentials` |
| `AMS_OAUTH2_CLIENT_SECRET` | OAuth2 client secret | - | If auth type is `oauth2_client_credentials` |
| `TOKEN_VALIDITY_MINUTES` | Session token validity in minutes | `10` | No |
| `MIN_LIVENESS_CONFIDENCE` | Minimum liveness confidence (0.0-1.0) | `0.8` | No |
| `REQUIRE_LIVE_FOR_AMS` | Only submit to AMS if liveness passed | `true` | No |

*Not required if `USE_MANAGED_IDENTITY` is `true`

### AMS Authentication Examples

**API Key:**
```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AMS_AUTH_TYPE="api_key" \
    AMS_API_KEY="sk-your-api-key" \
    AMS_API_KEY_HEADER="X-API-Key"
```

**Bearer Token:**
```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AMS_AUTH_TYPE="bearer_token" \
    AMS_BEARER_TOKEN="your-bearer-token"
```

**OAuth2 Client Credentials:**
```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AMS_AUTH_TYPE="oauth2_client_credentials" \
    AMS_OAUTH2_TOKEN_URL="https://auth.example.com/oauth2/token" \
    AMS_OAUTH2_CLIENT_ID="your-client-id" \
    AMS_OAUTH2_CLIENT_SECRET="your-client-secret" \
    AMS_OAUTH2_SCOPE="api://your-api/.default"
```

---

## Mobile Client Setup

### iOS Setup

#### 1. Add the Client to Your Project

Copy `src/mobile-client/ios/LivenessClient.swift` to your Xcode project.

#### 2. Add Azure Face SDK (Optional, for client-side liveness)

Add to your `Podfile`:
```ruby
pod 'AzureAIVisionFace', '~> 0.17'
```

Or via Swift Package Manager:
```
https://github.com/Azure-Samples/azure-ai-vision-sdk
```

#### 3. Configure the Client

```swift
import UIKit

class ViewController: UIViewController {

    let livenessClient = LivenessClient(config: LivenessClientConfig(
        baseUrl: "https://your-function-app.azurewebsites.net",
        clientId: "your-mobile-app-client-id",
        functionKey: "your-function-key"  // Optional if using other auth
    ))

    func performLivenessCheck() async {
        do {
            // Option 1: Direct image submission
            let result = try await livenessClient.performLivenessCheck(
                applicantData: ApplicantData(
                    firstName: "John",
                    lastName: "Doe",
                    email: "john@example.com"
                ),
                image: capturedImage
            )

            if result.isSuccess {
                print("Verified! Applicant ID: \(result.applicantId!)")
            } else {
                print("Failed: \(result.error ?? "Unknown")")
            }

            // Option 2: Azure SDK flow (for better liveness detection)
            // let result = try await livenessClient.performAzureLivenessCheck(
            //     applicantData: applicantData,
            //     presentingViewController: self
            // )

        } catch {
            print("Error: \(error)")
        }
    }
}
```

### Android Setup

#### 1. Add Dependencies

In your `build.gradle.kts`:

```kotlin
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")

    // Optional: Azure Face SDK for client-side liveness
    // implementation("com.azure.android:azure-ai-vision-face:0.17.0")
}
```

#### 2. Add the Client

Copy `src/mobile-client/android/LivenessClient.kt` to your project.

#### 3. Configure and Use

```kotlin
import com.liveness.pipeline.client.*
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private val livenessClient = LivenessClient(LivenessClientConfig(
        baseUrl = "https://your-function-app.azurewebsites.net",
        clientId = "your-mobile-app-client-id",
        functionKey = "your-function-key"
    ))

    private fun performLivenessCheck(capturedImage: Bitmap) {
        lifecycleScope.launch {
            try {
                val result = livenessClient.performLivenessCheck(
                    applicantData = ApplicantData(
                        firstName = "John",
                        lastName = "Doe",
                        email = "john@example.com"
                    ),
                    image = capturedImage
                )

                if (result.isSuccess) {
                    Log.d("Liveness", "Verified! Applicant ID: ${result.applicantId}")
                } else {
                    Log.e("Liveness", "Failed: ${result.error}")
                }

            } catch (e: LivenessClientException) {
                Log.e("Liveness", "Error: ${e.message}")
            }
        }
    }
}
```

---

## Testing the Deployment

### Run Unit Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest tests/ -v
```

### End-to-End Test Script

Create a test script `scripts/e2e_test.sh`:

```bash
#!/bin/bash
set -e

BASE_URL="${1:-https://your-function-app.azurewebsites.net}"
FUNCTION_KEY="${2:-your-function-key}"

echo "=== Testing Liveness Detection Pipeline ==="
echo "Base URL: $BASE_URL"
echo ""

# 1. Health Check
echo "1. Health Check..."
HEALTH=$(curl -s "$BASE_URL/api/health")
echo "   Response: $HEALTH"
echo ""

# 2. Create Session
echo "2. Creating session..."
SESSION=$(curl -s -X POST "$BASE_URL/api/sessions" \
  -H "Content-Type: application/json" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -d '{
    "client_id": "e2e-test",
    "applicant_data": {
      "first_name": "E2E",
      "last_name": "Test",
      "email": "e2e@test.com"
    }
  }')

SESSION_ID=$(echo $SESSION | jq -r '.session_id')
TOKEN=$(echo $SESSION | jq -r '.token')

echo "   Session ID: $SESSION_ID"
echo "   Token: ${TOKEN:0:20}..."
echo ""

# 3. Check Session Status
echo "3. Checking session status..."
STATUS=$(curl -s "$BASE_URL/api/sessions/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-functions-key: $FUNCTION_KEY")
echo "   Status: $(echo $STATUS | jq -r '.status')"
echo ""

# 4. Cancel Session (cleanup)
echo "4. Cancelling session..."
curl -s -X DELETE "$BASE_URL/api/sessions/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-functions-key: $FUNCTION_KEY"
echo "   Done"
echo ""

echo "=== E2E Test Complete ==="
```

Run it:
```bash
chmod +x scripts/e2e_test.sh
./scripts/e2e_test.sh "https://your-app.azurewebsites.net" "your-key"
```

---

## Production Considerations

### Security Hardening

#### 1. Enable HTTPS Only

Already configured in Bicep, but verify:
```bash
az functionapp show \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query httpsOnly
```

#### 2. Restrict CORS

Update in Azure Portal or via CLI:
```bash
az functionapp cors remove \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "*"

az functionapp cors add \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://your-app.com"
```

#### 3. Use Managed Identity (Recommended)

```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings USE_MANAGED_IDENTITY="true"
```

#### 4. Enable Key Vault References

Already configured in Bicep. Secrets are accessed via:
```
@Microsoft.KeyVault(VaultName=kv-xxx;SecretName=face-api-key)
```

### Scaling

#### Upgrade to Premium Plan (for high volume)

```bash
# Create Premium plan
az functionapp plan create \
  --name liveness-premium-plan \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku EP1 \
  --is-linux true

# Move function app to Premium
az functionapp update \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan liveness-premium-plan
```

### Monitoring

#### View Application Insights

```bash
# Get instrumentation key
az monitor app-insights component show \
  --app liveness-dev-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey
```

#### Set Up Alerts

```bash
# Alert on high error rate
az monitor metrics alert create \
  --name "High Error Rate" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/.../resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$FUNCTION_APP_NAME" \
  --condition "count requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m
```

### Backup and Disaster Recovery

#### Export Configuration

```bash
# Export function app settings
az functionapp config appsettings list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  -o json > backup/appsettings.json

# Export Bicep parameters
az deployment group export \
  --resource-group $RESOURCE_GROUP \
  --name main > backup/deployment.json
```

---

## Troubleshooting

### Common Issues

#### 1. "Invalid or expired token"

**Cause:** Token has expired (default: 10 minutes)

**Solution:**
- Create a new session
- Increase `TOKEN_VALIDITY_MINUTES` if needed

```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings TOKEN_VALIDITY_MINUTES="30"
```

#### 2. "Face API connection failed"

**Cause:** Incorrect endpoint or key

**Solution:**
```bash
# Verify Face API is accessible
curl -X POST "$FACE_ENDPOINT/face/v1.0/detect" \
  -H "Ocp-Apim-Subscription-Key: $FACE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/face.jpg"}'
```

#### 3. "AMS submission failed"

**Cause:** AMS authentication or connectivity issue

**Solution:**
- Verify AMS_BASE_URL is correct
- Check authentication settings
- Review AMS API logs

```bash
# Check current AMS settings
az functionapp config appsettings list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?contains(name, 'AMS')]"
```

#### 4. Function App Not Starting

**Check logs:**
```bash
az functionapp log tail \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

**Check Application Insights:**
```bash
az monitor app-insights query \
  --app liveness-dev-insights \
  --resource-group $RESOURCE_GROUP \
  --analytics-query "exceptions | order by timestamp desc | take 10"
```

#### 5. Key Vault Access Denied

**Cause:** Function app identity doesn't have access

**Solution:**
```bash
# Get function app identity
IDENTITY=$(az functionapp identity show \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Grant Key Vault access
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --object-id $IDENTITY \
  --secret-permissions get list
```

### Debug Mode

Enable detailed logging:

```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHON_ENABLE_DEBUG_LOGGING="1" \
    FUNCTIONS_WORKER_PROCESS_COUNT="1"
```

### Getting Help

1. Check logs in Application Insights
2. Review Azure Function App diagnostics in Azure Portal
3. Enable debug logging (see above)
4. Contact Azure Support for Face API issues

---

## Appendix

### Sample Bicep Parameters File

Create `infrastructure/parameters.dev.json`:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": {
      "value": "dev"
    },
    "location": {
      "value": "eastus"
    },
    "amsBaseUrl": {
      "value": "https://your-ams-api.example.com"
    },
    "amsApiKey": {
      "value": "your-api-key"
    }
  }
}
```

Deploy with parameters file:
```bash
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infrastructure/main.bicep \
  --parameters @infrastructure/parameters.dev.json
```

### Useful Azure CLI Commands

```bash
# List all resources in the group
az resource list --resource-group $RESOURCE_GROUP -o table

# View function app logs
az functionapp log tail --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP

# Restart function app
az functionapp restart --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP

# View function app settings
az functionapp config appsettings list --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP -o table

# Delete all resources (cleanup)
az group delete --name $RESOURCE_GROUP --yes --no-wait
```
