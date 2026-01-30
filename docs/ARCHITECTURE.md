# Mobile Liveness Detection Pipeline - Architecture

## Overview

This document describes the architecture for a session-based, credential-driven liveness detection pipeline that integrates mobile applications with Azure Face API and an Applicant Management System (AMS).

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Mobile Application                              │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────┐ │
│  │  Capture Live Image │───▶│  Attach Hex Token   │───▶│ Submit to API   │ │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Azure Function App (API)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Pipeline Orchestrator                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Session     │  │  Liveness    │  │    AMS       │              │   │
│  │  │  Manager     │  │  Service     │  │  Integration │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐
│ Azure Table     │  │ Azure Face API   │  │ Applicant Management System │
│ Storage         │  │ (Liveness)       │  │ (External REST API)         │
│                 │  │                  │  │                             │
│ - Sessions      │  │ - Liveness       │  │ - Create Applicant          │
│ - Tokens        │  │   Detection      │  │ - Update Status             │
│ - Status        │  │ - Spoof          │  │ - Query Records             │
└─────────────────┘  │   Detection      │  └─────────────────────────────┘
                     └──────────────────┘
```

## Data Flow

### 1. Session Initialization

```
Mobile App                    Azure Functions               Azure Storage
    │                              │                             │
    │  POST /api/sessions          │                             │
    │  {client_id, applicant_data} │                             │
    │─────────────────────────────▶│                             │
    │                              │                             │
    │                              │  Generate Session + Token   │
    │                              │────────────────────────────▶│
    │                              │                             │
    │  {session_id, token,         │                             │
    │   token_expires_at}          │                             │
    │◀─────────────────────────────│                             │
```

### 2. Liveness Detection (Mobile SDK Flow)

```
Mobile App           Azure Functions        Azure Face API
    │                      │                      │
    │ POST /sessions/{id}  │                      │
    │ /liveness            │                      │
    │ Token: <hex_token>   │                      │
    │─────────────────────▶│                      │
    │                      │                      │
    │                      │ Create Liveness      │
    │                      │ Session              │
    │                      │─────────────────────▶│
    │                      │                      │
    │ {azure_session_id,   │ {session_id,         │
    │  auth_token}         │  auth_token}         │
    │◀─────────────────────│◀─────────────────────│
    │                      │                      │
    │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
    │  Azure SDK Liveness  │                      │
    │  Check (client-side) │                      │
    │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─▶│
    │                      │                      │
    │ POST /sessions/{id}  │                      │
    │ /complete            │                      │
    │ {azure_session_id}   │                      │
    │─────────────────────▶│                      │
    │                      │ Get Session Result   │
    │                      │─────────────────────▶│
    │                      │                      │
    │                      │ {liveness_decision,  │
    │                      │  confidence}         │
    │                      │◀─────────────────────│
```

### 3. AMS Submission

```
Azure Functions              Applicant Management System
      │                              │
      │  POST /api/applicants        │
      │  {session_data,              │
      │   applicant_data,            │
      │   liveness_verification}     │
      │─────────────────────────────▶│
      │                              │
      │  {applicant_id, status}      │
      │◀─────────────────────────────│
```

## Components

### 1. Session Model (`src/models/session.py`)

**HexToken**
- Cryptographically secure 256-bit hex token
- Time-limited validity (configurable, default 10 minutes)
- Used for request authentication

**LivenessSession**
- Tracks complete pipeline state
- Status progression:
  ```
  CREATED → TOKEN_ATTACHED → IMAGE_RECEIVED → LIVENESS_PENDING
         → LIVENESS_COMPLETED/FAILED → AMS_SUBMITTED → COMPLETED
  ```

### 2. Session Store (`src/services/session_store.py`)

- Azure Table Storage backend
- Partitioned by `client_id` for efficient queries
- Token-based session lookup
- Automatic expiry cleanup

### 3. Liveness Service (`src/services/liveness_service.py`)

- Azure Face API integration
- Two detection modes:
  - **Mobile SDK Flow**: Creates session for client-side detection
  - **Server-Side Flow**: Accepts image directly for analysis
- Optional face verification against reference image

### 4. AMS Integration (`src/services/applicant_service.py`)

- Generic REST client for AMS
- Multiple auth methods:
  - API Key
  - Bearer Token
  - Basic Auth
  - OAuth2 Client Credentials
- Automatic retry with exponential backoff

### 5. Pipeline Orchestrator (`src/services/pipeline_orchestrator.py`)

- Coordinates all components
- Enforces business rules:
  - Token validation
  - Minimum confidence thresholds
  - Live-only AMS submission

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | POST | Start new session, get hex token |
| `/api/sessions/{id}/liveness` | POST | Create Azure liveness session for mobile SDK |
| `/api/sessions/{id}/complete` | POST | Complete mobile liveness flow |
| `/api/sessions/{id}/image` | POST | Submit image for server-side liveness |
| `/api/sessions/{id}` | GET | Get session status |
| `/api/sessions/{id}` | DELETE | Cancel session |
| `/api/health` | GET | Health check |

## Security

### Token Security
- 256-bit cryptographically random tokens
- Short-lived (configurable TTL)
- Required for all session operations
- Prevents unauthorized access to sessions

### Credential Management
- Azure Key Vault for secrets
- Managed Identity support for Azure services
- No credentials in code or config files

### API Security
- Function-level authentication keys
- HTTPS only
- CORS configuration
- Input validation on all endpoints

## Deployment

### Azure Resources (via Bicep)

1. **Azure Function App** - Serverless compute
2. **Azure Storage Account** - Session persistence
3. **Azure Face API** - Liveness detection
4. **Azure Key Vault** - Secrets management
5. **Application Insights** - Monitoring

### Environment Configuration

```bash
# Azure Face API
AZURE_FACE_ENDPOINT=https://your-face-api.cognitiveservices.azure.com/
AZURE_FACE_KEY=<from-key-vault>

# AMS Integration
AMS_BASE_URL=https://your-ams.example.com
AMS_AUTH_TYPE=api_key
AMS_API_KEY=<from-key-vault>

# Pipeline Settings
TOKEN_VALIDITY_MINUTES=10
MIN_LIVENESS_CONFIDENCE=0.8
REQUIRE_LIVE_FOR_AMS=true
```

## Mobile Integration

### iOS (Swift)
- `LivenessClient` class handles all API communication
- Supports both direct image submission and Azure SDK flow
- Async/await pattern for all operations

### Android (Kotlin)
- Coroutines-based async operations
- kotlinx.serialization for JSON handling
- Same dual-flow support as iOS

## Error Handling

| Error | HTTP Status | Handling |
|-------|-------------|----------|
| Invalid token | 401 | Request new session |
| Session expired | 401 | Request new session |
| Liveness failed | 200 | Return result, no AMS submission |
| AMS error | 200 | Return partial success, log error |
| Internal error | 500 | Retry with backoff |

## Monitoring

- Application Insights for all API calls
- Custom metrics for:
  - Session creation rate
  - Liveness detection success rate
  - AMS submission success rate
  - Token expiry rate

## Future Considerations

1. **Caching**: Redis for high-volume session lookups
2. **Queuing**: Azure Service Bus for async AMS submission
3. **Multi-Region**: Traffic Manager for global distribution
4. **Compliance**: Data residency controls, audit logging
