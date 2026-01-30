"""
Applicant Management System (AMS) REST API Integration Service

Generic REST client for integrating with external Applicant Management Systems.
Configurable endpoints, authentication, and payload transformation.
"""
import logging
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum

import httpx

from ..models.session import LivenessSession, LivenessResult

logger = logging.getLogger(__name__)


class AMSAuthType(Enum):
    """Authentication types supported for AMS integration"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC = "basic"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"


@dataclass
class AMSConfig:
    """Configuration for Applicant Management System integration"""
    base_url: str
    auth_type: AMSAuthType = AMSAuthType.NONE

    # API Key auth
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"

    # Bearer token auth
    bearer_token: Optional[str] = None

    # Basic auth
    username: Optional[str] = None
    password: Optional[str] = None

    # OAuth2 Client Credentials
    oauth2_token_url: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_scope: Optional[str] = None

    # Request configuration
    timeout_seconds: int = 30
    retry_count: int = 3
    retry_delay_seconds: float = 1.0

    # Custom headers
    custom_headers: dict = field(default_factory=dict)


@dataclass
class AMSSubmissionResult:
    """Result from AMS submission"""
    success: bool
    applicant_id: Optional[str]
    status: str
    message: Optional[str]
    raw_response: dict


class ApplicantManagementService:
    """
    REST API client for Applicant Management System integration.

    Handles submission of verified applicants after successful liveness detection.
    Supports configurable endpoints, authentication methods, and payload transformation.
    """

    def __init__(self, config: AMSConfig):
        """
        Initialize the AMS client.

        Args:
            config: AMS configuration with endpoint and auth settings
        """
        self.config = config
        self._oauth2_token: Optional[str] = None
        self._oauth2_token_expires: Optional[float] = None

    async def _get_oauth2_token(self) -> str:
        """Get OAuth2 access token using client credentials flow"""
        if self.config.auth_type != AMSAuthType.OAUTH2_CLIENT_CREDENTIALS:
            raise ValueError("OAuth2 auth not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.oauth2_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.config.oauth2_client_id,
                    "client_secret": self.config.oauth2_client_secret,
                    "scope": self.config.oauth2_scope or ""
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()

            token_data = response.json()
            self._oauth2_token = token_data["access_token"]
            return self._oauth2_token

    async def _get_auth_headers(self) -> dict:
        """Build authentication headers based on config"""
        headers = dict(self.config.custom_headers)

        if self.config.auth_type == AMSAuthType.API_KEY:
            headers[self.config.api_key_header] = self.config.api_key

        elif self.config.auth_type == AMSAuthType.BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"

        elif self.config.auth_type == AMSAuthType.OAUTH2_CLIENT_CREDENTIALS:
            token = await self._get_oauth2_token()
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def _get_basic_auth(self) -> Optional[tuple]:
        """Get basic auth credentials if configured"""
        if self.config.auth_type == AMSAuthType.BASIC:
            return (self.config.username, self.config.password)
        return None

    def _build_submission_payload(
        self,
        session: LivenessSession,
        applicant_data: dict,
        include_liveness_details: bool = True
    ) -> dict:
        """
        Build the submission payload for AMS.

        Args:
            session: The liveness detection session
            applicant_data: Custom applicant data from the client
            include_liveness_details: Whether to include liveness detection details

        Returns:
            Formatted payload for AMS submission
        """
        payload = {
            "session_id": session.session_id,
            "client_id": session.client_id,
            "submitted_at": session.updated_at.isoformat(),
            "applicant": applicant_data
        }

        if include_liveness_details and session.liveness_result:
            payload["liveness_verification"] = {
                "result": session.liveness_result.value,
                "confidence": session.liveness_confidence,
                "verified_at": session.updated_at.isoformat(),
                "is_live": session.liveness_result == LivenessResult.LIVE
            }

        return payload

    async def submit_applicant(
        self,
        session: LivenessSession,
        applicant_data: dict,
        endpoint_path: str = "/api/applicants",
        include_liveness_details: bool = True
    ) -> AMSSubmissionResult:
        """
        Submit a verified applicant to the AMS.

        Args:
            session: The liveness detection session (must have liveness result)
            applicant_data: Applicant information to submit
            endpoint_path: API endpoint path for submission
            include_liveness_details: Include liveness verification details

        Returns:
            AMSSubmissionResult with submission outcome
        """
        if not session.liveness_result:
            return AMSSubmissionResult(
                success=False,
                applicant_id=None,
                status="error",
                message="Liveness verification not completed",
                raw_response={}
            )

        if session.liveness_result != LivenessResult.LIVE:
            return AMSSubmissionResult(
                success=False,
                applicant_id=None,
                status="rejected",
                message=f"Liveness check failed: {session.liveness_result.value}",
                raw_response={}
            )

        url = f"{self.config.base_url.rstrip('/')}{endpoint_path}"
        payload = self._build_submission_payload(
            session,
            applicant_data,
            include_liveness_details
        )

        headers = await self._get_auth_headers()
        headers["Content-Type"] = "application/json"

        basic_auth = self._get_basic_auth()

        last_error = None
        for attempt in range(self.config.retry_count):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers,
                        auth=basic_auth
                    )

                    if response.status_code >= 500:
                        # Retry on server errors
                        last_error = f"Server error: {response.status_code}"
                        logger.warning(f"AMS server error (attempt {attempt + 1}): {response.status_code}")
                        continue

                    response_data = response.json() if response.content else {}

                    if response.is_success:
                        applicant_id = response_data.get("applicant_id") or response_data.get("id")
                        return AMSSubmissionResult(
                            success=True,
                            applicant_id=applicant_id,
                            status="submitted",
                            message=response_data.get("message", "Successfully submitted"),
                            raw_response=response_data
                        )
                    else:
                        return AMSSubmissionResult(
                            success=False,
                            applicant_id=None,
                            status="error",
                            message=response_data.get("error", f"HTTP {response.status_code}"),
                            raw_response=response_data
                        )

            except httpx.TimeoutException:
                last_error = "Request timeout"
                logger.warning(f"AMS request timeout (attempt {attempt + 1})")
            except httpx.RequestError as e:
                last_error = str(e)
                logger.warning(f"AMS request error (attempt {attempt + 1}): {e}")

        return AMSSubmissionResult(
            success=False,
            applicant_id=None,
            status="error",
            message=f"Failed after {self.config.retry_count} attempts: {last_error}",
            raw_response={}
        )

    async def check_applicant_status(
        self,
        applicant_id: str,
        endpoint_path: str = "/api/applicants/{applicant_id}"
    ) -> dict:
        """
        Check the status of a submitted applicant.

        Args:
            applicant_id: The applicant ID returned from submission
            endpoint_path: API endpoint path (with {applicant_id} placeholder)

        Returns:
            Applicant status information from AMS
        """
        url = f"{self.config.base_url.rstrip('/')}{endpoint_path.format(applicant_id=applicant_id)}"

        headers = await self._get_auth_headers()
        basic_auth = self._get_basic_auth()

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.get(url, headers=headers, auth=basic_auth)
            response.raise_for_status()
            return response.json()

    async def update_applicant(
        self,
        applicant_id: str,
        update_data: dict,
        endpoint_path: str = "/api/applicants/{applicant_id}"
    ) -> dict:
        """
        Update an existing applicant record.

        Args:
            applicant_id: The applicant ID to update
            update_data: Data to update
            endpoint_path: API endpoint path

        Returns:
            Updated applicant data from AMS
        """
        url = f"{self.config.base_url.rstrip('/')}{endpoint_path.format(applicant_id=applicant_id)}"

        headers = await self._get_auth_headers()
        headers["Content-Type"] = "application/json"
        basic_auth = self._get_basic_auth()

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.patch(url, json=update_data, headers=headers, auth=basic_auth)
            response.raise_for_status()
            return response.json()

    async def health_check(self, endpoint_path: str = "/health") -> bool:
        """
        Check if the AMS is available.

        Args:
            endpoint_path: Health check endpoint path

        Returns:
            True if AMS is available, False otherwise
        """
        url = f"{self.config.base_url.rstrip('/')}{endpoint_path}"

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.is_success
        except Exception as e:
            logger.warning(f"AMS health check failed: {e}")
            return False
