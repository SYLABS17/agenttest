// Main Bicep template for AI Research System Infrastructure
targetScope = 'subscription'

// Parameters
@description('Environment name (dev, test, prod)')
@allowed(['dev', 'test', 'prod'])
param environment string = 'dev'

@description('Azure region for resources')
param location string = 'eastus'

@description('Project name prefix')
@minLength(3)
@maxLength(10)
param projectName string = 'airesearch'

@description('Owner tag for resources')
param owner string = 'research-team'

@description('Cost center tag')
param costCenter string = 'RSCH-001'

@description('App Service Plan SKU')
param appServicePlanSku string = 'P1V2'

@description('Azure Cognitive Search SKU')
@allowed(['free', 'basic', 'standard', 'standard2', 'standard3'])
param searchServiceSku string = 'standard'

@description('Storage Account SKU')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_RAGRS', 'Standard_ZRS'])
param storageAccountSku string = 'Standard_LRS'

@description('Enable private endpoints')
param enablePrivateEndpoints bool = false

@description('Enable diagnostic settings')
param enableDiagnosticSettings bool = true

@description('Log retention in days')
param logRetentionDays int = 30

// Variables
var uniqueSuffix = uniqueString(subscription().id, projectName, environment)
var resourceGroupName = 'rg-${projectName}-${environment}'
var namingPrefix = '${projectName}-${environment}'

// Common tags
var tags = {
  Environment: environment
  Owner: owner
  CostCenter: costCenter
  Project: projectName
  DeployedBy: 'Bicep'
  DeploymentDate: utcNow('yyyy-MM-dd')
}

// Resource Group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Deploy resources into the resource group
module resources 'resources.bicep' = {
  name: 'deploy-resources'
  scope: resourceGroup
  params: {
    location: location
    namingPrefix: namingPrefix
    uniqueSuffix: uniqueSuffix
    tags: tags
    appServicePlanSku: appServicePlanSku
    searchServiceSku: searchServiceSku
    storageAccountSku: storageAccountSku
    enablePrivateEndpoints: enablePrivateEndpoints
    enableDiagnosticSettings: enableDiagnosticSettings
    logRetentionDays: logRetentionDays
  }
}

// Outputs
output resourceGroupName string = resourceGroup.name
output appServiceName string = resources.outputs.appServiceName
output appServiceUrl string = resources.outputs.appServiceUrl
output searchServiceName string = resources.outputs.searchServiceName
output searchServiceEndpoint string = resources.outputs.searchServiceEndpoint
output storageAccountName string = resources.outputs.storageAccountName
output applicationInsightsName string = resources.outputs.applicationInsightsName
output applicationInsightsInstrumentationKey string = resources.outputs.applicationInsightsInstrumentationKey
output logAnalyticsWorkspaceName string = resources.outputs.logAnalyticsWorkspaceName
output openAiAccountName string = resources.outputs.openAiAccountName
output openAiEndpoint string = resources.outputs.openAiEndpoint