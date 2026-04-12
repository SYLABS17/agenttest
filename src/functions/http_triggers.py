"""
Azure Functions HTTP Triggers for Liveness Detection Pipeline

Exposes the pipeline as REST API endpoints:
- POST /api/sessions - Start a new session
- POST /api/sessions/{id}/liveness - Create Azure liveness session for mobile SDK
- POST /api/sessions/{id}/complete - Complete mobile liveness flow
- POST /api/sessions/{id}/image - Submit image for server-side liveness
- GET /api/sessions/{id} - Get session status
- DELETE /api/sessions/{id} - Cancel session
"""
import json
import logging
import os
from typing import Optional

import azure.functions as func

from ..models.session import PipelineRequest
from ..services.session_store import SessionStore
from ..services.liveness_service import AzureLivenessService
from ..services.applicant_service import ApplicantManagementService, AMSConfig, AMSAuthType
from ..services.pipeline_orchestrator import LivenessPipelineOrchestrator, PipelineConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def get_orchestrator() -> LivenessPipelineOrchestrator:
    """
    Initialize and return the pipeline orchestrator.

    Uses environment variables for configuration.
    """
    # Session store configuration
    storage_connection = os.environ.get("AzureWebJobsStorage")
    session_store = SessionStore(storage_connection)

    # Azure Liveness service configuration
    face_endpoint = os.environ.get("AZURE_FACE_ENDPOINT")
    face_key = os.environ.get("AZURE_FACE_KEY")
    use_managed_identity = os.environ.get("USE_MANAGED_IDENTITY", "false").lower() == "true"

    liveness_service = AzureLivenessService(
        endpoint=face_endpoint,
        api_key=face_key if not use_managed_identity else None,
        use_managed_identity=use_managed_identity
    )

    # AMS configuration
    ams_config = AMSConfig(
        base_url=os.environ.get("AMS_BASE_URL", ""),
        auth_type=AMSAuthType(os.environ.get("AMS_AUTH_TYPE", "api_key")),
        api_key=os.environ.get("AMS_API_KEY"),
        api_key_header=os.environ.get("AMS_API_KEY_HEADER", "X-API-Key"),
        bearer_token=os.environ.get("AMS_BEARER_TOKEN"),
        oauth2_token_url=os.environ.get("AMS_OAUTH2_TOKEN_URL"),
        oauth2_client_id=os.environ.get("AMS_OAUTH2_CLIENT_ID"),
        oauth2_client_secret=os.environ.get("AMS_OAUTH2_CLIENT_SECRET"),
        oauth2_scope=os.environ.get("AMS_OAUTH2_SCOPE")
    )
    ams_service = ApplicantManagementService(ams_config)

    # Pipeline configuration
    pipeline_config = PipelineConfig(
        token_validity_minutes=int(os.environ.get("TOKEN_VALIDITY_MINUTES", "10")),
        require_live_result_for_ams=os.environ.get("REQUIRE_LIVE_FOR_AMS", "true").lower() == "true",
        min_liveness_confidence=float(os.environ.get("MIN_LIVENESS_CONFIDENCE", "0.8"))
    )

    return LivenessPipelineOrchestrator(
        session_store=session_store,
        liveness_service=liveness_service,
        ams_service=ams_service,
        config=pipeline_config
    )


def extract_token(req: func.HttpRequest) -> Optional[str]:
    """Extract hex token from request header or query parameter"""
    # Check Authorization header first
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    # Check X-Session-Token header
    token = req.headers.get("X-Session-Token")
    if token:
        return token

    # Check query parameter
    return req.params.get("token")


def json_response(data: dict, status_code: int = 200) -> func.HttpResponse:
    """Create JSON HTTP response"""
    return func.HttpResponse(
        json.dumps(data),
        status_code=status_code,
        mimetype="application/json"
    )


def error_response(message: str, status_code: int = 400) -> func.HttpResponse:
    """Create error HTTP response"""
    return json_response({"error": message}, status_code)


@app.route(route="sessions", methods=["POST"])
async def start_session(req: func.HttpRequest) -> func.HttpResponse:
    """
    Start a new liveness detection session.

    Request body:
    {
        "client_id": "string",
        "applicant_data": { ... },
        "callback_url": "string (optional)",
        "metadata": { ... (optional) }
    }

    Response:
    {
        "session_id": "uuid",
        "status": "token_attached",
        "token": "hex string",
        "token_expires_at": "ISO datetime"
    }
    """
    try:
        body = req.get_json()
    except ValueError:
        return error_response("Invalid JSON body")

    client_id = body.get("client_id")
    if not client_id:
        return error_response("client_id is required")

    applicant_data = body.get("applicant_data", {})

    request = PipelineRequest(
        client_id=client_id,
        applicant_data=applicant_data,
        callback_url=body.get("callback_url"),
        metadata=body.get("metadata", {})
    )

    orchestrator = get_orchestrator()
    response = await orchestrator.start_session(request)

    return json_response(response.to_dict(), 201)


@app.route(route="sessions/{session_id}/liveness", methods=["POST"])
async def create_liveness_session(req: func.HttpRequest) -> func.HttpResponse:
    """
    Create Azure liveness session for mobile SDK.

    Required header: Authorization: Bearer <hex_token>

    Request body (optional):
    {
        "device_correlation_id": "string"
    }

    Response:
    {
        "azure_session_id": "string",
        "auth_token": "string (for Azure SDK)",
        "pipeline_session_id": "uuid",
        "pipeline_token": "hex string"
    }
    """
    session_id = req.route_params.get("session_id")
    token = extract_token(req)

    if not token:
        return error_response("Authorization token required", 401)

    try:
        body = req.get_json() if req.get_body() else {}
    except ValueError:
        body = {}

    device_correlation_id = body.get("device_correlation_id")

    orchestrator = get_orchestrator()

    try:
        result = await orchestrator.create_mobile_liveness_session(
            session_id,
            token,
            device_correlation_id
        )
        return json_response(result)
    except ValueError as e:
        return error_response(str(e), 401)
    except Exception as e:
        logger.error(f"Error creating liveness session: {e}")
        return error_response("Internal server error", 500)


@app.route(route="sessions/{session_id}/complete", methods=["POST"])
async def complete_liveness(req: func.HttpRequest) -> func.HttpResponse:
    """
    Complete mobile liveness flow after SDK finishes.

    Required header: Authorization: Bearer <hex_token>

    Request body:
    {
        "azure_session_id": "string"
    }

    Response:
    {
        "session_id": "uuid",
        "status": "completed|liveness_failed|error",
        "liveness_result": "live|spoof|uncertain",
        "liveness_confidence": 0.0-1.0,
        "applicant_id": "string (if submitted to AMS)"
    }
    """
    session_id = req.route_params.get("session_id")
    token = extract_token(req)

    if not token:
        return error_response("Authorization token required", 401)

    try:
        body = req.get_json()
    except ValueError:
        return error_response("Invalid JSON body")

    azure_session_id = body.get("azure_session_id")
    if not azure_session_id:
        return error_response("azure_session_id is required")

    orchestrator = get_orchestrator()

    try:
        response = await orchestrator.complete_mobile_liveness(
            session_id,
            token,
            azure_session_id
        )
        return json_response(response.to_dict())
    except ValueError as e:
        return error_response(str(e), 401)
    except Exception as e:
        logger.error(f"Error completing liveness: {e}")
        return error_response("Internal server error", 500)


@app.route(route="sessions/{session_id}/image", methods=["POST"])
async def submit_image(req: func.HttpRequest) -> func.HttpResponse:
    """
    Submit image for server-side liveness detection.

    Required header: Authorization: Bearer <hex_token>
    Content-Type: image/jpeg or image/png (or multipart/form-data)

    Response:
    {
        "session_id": "uuid",
        "status": "completed|liveness_failed|error",
        "liveness_result": "live|spoof|uncertain",
        "liveness_confidence": 0.0-1.0,
        "applicant_id": "string (if submitted to AMS)"
    }
    """
    session_id = req.route_params.get("session_id")
    token = extract_token(req)

    if not token:
        return error_response("Authorization token required", 401)

    content_type = req.headers.get("Content-Type", "image/jpeg")

    # Get image data
    image_data = req.get_body()
    if not image_data:
        return error_response("Image data required")

    orchestrator = get_orchestrator()

    try:
        response = await orchestrator.submit_image(
            session_id,
            token,
            image_data,
            content_type
        )
        return json_response(response.to_dict())
    except ValueError as e:
        return error_response(str(e), 401)
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return error_response("Internal server error", 500)


@app.route(route="sessions/{session_id}", methods=["GET"])
async def get_session(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get current session status.

    Required header: Authorization: Bearer <hex_token>

    Response:
    {
        "session_id": "uuid",
        "status": "string",
        "token": "hex string",
        "token_expires_at": "ISO datetime",
        "liveness_result": "live|spoof|uncertain|null",
        "liveness_confidence": 0.0-1.0|null,
        "applicant_id": "string|null",
        "error": "string|null"
    }
    """
    session_id = req.route_params.get("session_id")
    token = extract_token(req)

    if not token:
        return error_response("Authorization token required", 401)

    orchestrator = get_orchestrator()

    try:
        response = await orchestrator.get_session_status(session_id, token)
        return json_response(response.to_dict())
    except ValueError as e:
        return error_response(str(e), 401)
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return error_response("Internal server error", 500)


@app.route(route="sessions/{session_id}", methods=["DELETE"])
async def cancel_session(req: func.HttpRequest) -> func.HttpResponse:
    """
    Cancel an active session.

    Required header: Authorization: Bearer <hex_token>

    Response: 204 No Content on success
    """
    session_id = req.route_params.get("session_id")
    token = extract_token(req)

    if not token:
        return error_response("Authorization token required", 401)

    orchestrator = get_orchestrator()

    try:
        success = await orchestrator.cancel_session(session_id, token)
        if success:
            return func.HttpResponse(status_code=204)
        else:
            return error_response("Session not found", 404)
    except Exception as e:
        logger.error(f"Error cancelling session: {e}")
        return error_response("Internal server error", 500)


@app.route(route="health", methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint.

    Response:
    {
        "status": "healthy",
        "services": {
            "storage": true|false,
            "face_api": true|false,
            "ams": true|false
        }
    }
    """
    health = {
        "status": "healthy",
        "services": {
            "storage": True,
            "face_api": True,
            "ams": True
        }
    }

    try:
        orchestrator = get_orchestrator()

        # Check AMS health
        ams_healthy = await orchestrator.ams_service.health_check()
        health["services"]["ams"] = ams_healthy

        if not ams_healthy:
            health["status"] = "degraded"

    except Exception as e:
        logger.error(f"Health check error: {e}")
        health["status"] = "unhealthy"
        health["services"]["storage"] = False
        health["services"]["face_api"] = False

    status_code = 200 if health["status"] == "healthy" else 503
    return json_response(health, status_code)


@app.route(route="cleanup", methods=["POST"])
async def cleanup_expired(req: func.HttpRequest) -> func.HttpResponse:
    """
    Trigger cleanup of expired sessions.

    Optional query parameter: client_id

    Response:
    {
        "cleaned_up": number
    }
    """
    client_id = req.params.get("client_id")

    orchestrator = get_orchestrator()

    try:
        count = await orchestrator.cleanup_expired(client_id)
        return json_response({"cleaned_up": count})
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return error_response("Internal server error", 500)
