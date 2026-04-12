/**
 * Azure Infrastructure for Liveness Detection Pipeline
 *
 * Deploys:
 * - Azure Function App (Python)
 * - Azure Storage Account (for session storage)
 * - Azure Face API (Cognitive Services)
 * - Azure Key Vault (for secrets management)
 * - Application Insights (for monitoring)
 *
 * Usage:
 * az deployment group create \
 *   --resource-group <your-rg> \
 *   --template-file main.bicep \
 *   --parameters environmentName=dev
 */

@description('Environment name for resource naming')
param environmentName string = 'dev'

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('AMS Base URL for applicant submission')
param amsBaseUrl string = ''

@description('AMS API Key')
@secure()
param amsApiKey string = ''

// Naming convention
var resourceToken = toLower(uniqueString(resourceGroup().id, environmentName))
var prefix = 'liveness-${environmentName}'

// Storage Account for session data and function app
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'st${resourceToken}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Table storage for sessions
resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource sessionsTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  parent: tableService
  name: 'LivenessSessions'
}

// Application Insights for monitoring
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${prefix}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
    RetentionInDays: 30
  }
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Azure Face API (Cognitive Services)
resource faceApi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${prefix}-face'
  location: location
  kind: 'Face'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${prefix}-face-${resourceToken}'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// Key Vault for secrets
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'kv-${resourceToken}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Store Face API key in Key Vault
resource faceApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'face-api-key'
  properties: {
    value: faceApi.listKeys().key1
  }
}

// Store AMS API key in Key Vault (if provided)
resource amsApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = if (!empty(amsApiKey)) {
  parent: keyVault
  name: 'ams-api-key'
  properties: {
    value: amsApiKey
  }
}

// App Service Plan for Function App
resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: '${prefix}-plan'
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true  // Linux
  }
}

// Function App
resource functionApp 'Microsoft.Web/sites@2022-09-01' = {
  name: '${prefix}-func-${resourceToken}'
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      pythonVersion: '3.11'
      linuxFxVersion: 'PYTHON|3.11'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
        ]
        supportCredentials: false
      }
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: '${prefix}-func'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'AZURE_FACE_ENDPOINT'
          value: faceApi.properties.endpoint
        }
        {
          name: 'AZURE_FACE_KEY'
          value: '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=face-api-key)'
        }
        {
          name: 'USE_MANAGED_IDENTITY'
          value: 'false'
        }
        {
          name: 'AMS_BASE_URL'
          value: amsBaseUrl
        }
        {
          name: 'AMS_AUTH_TYPE'
          value: 'api_key'
        }
        {
          name: 'AMS_API_KEY'
          value: !empty(amsApiKey) ? '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=ams-api-key)' : ''
        }
        {
          name: 'TOKEN_VALIDITY_MINUTES'
          value: '10'
        }
        {
          name: 'REQUIRE_LIVE_FOR_AMS'
          value: 'true'
        }
        {
          name: 'MIN_LIVENESS_CONFIDENCE'
          value: '0.8'
        }
      ]
    }
  }
}

// Grant Function App access to Key Vault
resource keyVaultAccessPolicy 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant Function App access to Face API (optional, for Managed Identity)
resource faceApiAccessPolicy 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(faceApi.id, functionApp.id, 'Cognitive Services User')
  scope: faceApi
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908') // Cognitive Services User
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output functionAppName string = functionApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output faceApiEndpoint string = faceApi.properties.endpoint
output storageAccountName string = storageAccount.name
output keyVaultName string = keyVault.name
output appInsightsName string = appInsights.name
