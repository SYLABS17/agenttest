"""
Azure Face API Liveness Detection Service

Integrates with Azure AI Face API for liveness detection.
Supports both server-side image submission and client-side SDK flows.
"""
import logging
import base64
from typing import Tuple, Optional
from dataclasses import dataclass

import httpx
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from ..models.session import LivenessSession, LivenessResult

logger = logging.getLogger(__name__)


@dataclass
class LivenessCheckResult:
    """Result from liveness detection check"""
    is_live: bool
    result: LivenessResult
    confidence: float
    session_id: str
    raw_response: dict


class AzureLivenessService:
    """
    Azure Face API Liveness Detection Service.

    Handles both:
    1. Session-based liveness detection (for mobile SDK integration)
    2. Direct image liveness detection (for server-side processing)

    Azure Face API Liveness Detection:
    - Detects if a face in an image/video is from a live person
    - Prevents spoofing attacks (photos, videos, masks)
    - Returns confidence score and liveness determination
    """

    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        use_managed_identity: bool = False
    ):
        """
        Initialize the liveness service.

        Args:
            endpoint: Azure Face API endpoint URL
            api_key: API key for authentication (optional if using managed identity)
            use_managed_identity: Use Azure Managed Identity for auth
        """
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.use_managed_identity = use_managed_identity

        if use_managed_identity:
            self.credential = DefaultAzureCredential()
        elif api_key:
            self.credential = AzureKeyCredential(api_key)
        else:
            raise ValueError("Either api_key or use_managed_identity must be provided")

    def _get_headers(self) -> dict:
        """Get authentication headers for API requests"""
        headers = {
            "Content-Type": "application/json"
        }

        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
        elif self.use_managed_identity:
            # Get token from managed identity
            token = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            headers["Authorization"] = f"Bearer {token.token}"

        return headers

    async def create_liveness_session(
        self,
        session: LivenessSession,
        device_correlation_id: Optional[str] = None
    ) -> dict:
        """
        Create a liveness detection session for mobile SDK.

        This creates a session on Azure Face API that the mobile SDK
        can use to perform liveness detection on-device.

        Args:
            session: The pipeline session
            device_correlation_id: Optional device identifier for correlation

        Returns:
            Session creation response with session token for mobile SDK
        """
        url = f"{self.endpoint}/face/v1.1-preview.1/detectLiveness/singleModal/sessions"

        payload = {
            "livenessOperationMode": "Passive",
            "sendResultsToClient": True,
            "deviceCorrelationId": device_correlation_id or session.session_id,
            "authTokenTimeToLiveInSeconds": 600  # 10 minutes
        }

        headers = self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Created Azure liveness session: {result.get('sessionId')}")

            return {
                "azure_session_id": result.get("sessionId"),
                "auth_token": result.get("authToken"),
                "pipeline_session_id": session.session_id,
                "pipeline_token": session.token.value
            }

    async def get_liveness_session_result(
        self,
        azure_session_id: str
    ) -> LivenessCheckResult:
        """
        Get the result of a liveness detection session.

        Called after mobile SDK completes the liveness check.

        Args:
            azure_session_id: The Azure Face API session ID

        Returns:
            LivenessCheckResult with detection outcome
        """
        url = f"{self.endpoint}/face/v1.1-preview.1/detectLiveness/singleModal/sessions/{azure_session_id}"

        headers = self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            result = response.json()

            # Parse liveness result
            status = result.get("status", "")
            liveness_decision = result.get("result", {}).get("livenessDecision", "uncertain")

            if liveness_decision.lower() == "realface":
                liveness_result = LivenessResult.LIVE
                is_live = True
            elif liveness_decision.lower() == "spoofface":
                liveness_result = LivenessResult.SPOOF
                is_live = False
            else:
                liveness_result = LivenessResult.UNCERTAIN
                is_live = False

            confidence = result.get("result", {}).get("livenessScore", 0.0)

            return LivenessCheckResult(
                is_live=is_live,
                result=liveness_result,
                confidence=confidence,
                session_id=azure_session_id,
                raw_response=result
            )

    async def detect_liveness_from_image(
        self,
        image_data: bytes,
        session: LivenessSession
    ) -> LivenessCheckResult:
        """
        Perform liveness detection directly from an image.

        Alternative flow for server-side liveness detection when
        mobile SDK flow is not used.

        Args:
            image_data: Raw image bytes (JPEG/PNG)
            session: The pipeline session

        Returns:
            LivenessCheckResult with detection outcome
        """
        # First, create a session for the detection
        url = f"{self.endpoint}/face/v1.1-preview.1/detectLiveness/singleModal/sessions"

        create_payload = {
            "livenessOperationMode": "Passive",
            "sendResultsToClient": False,
            "deviceCorrelationId": session.session_id
        }

        headers = self._get_headers()

        async with httpx.AsyncClient() as client:
            # Create session
            create_response = await client.post(url, json=create_payload, headers=headers)
            create_response.raise_for_status()
            session_data = create_response.json()
            azure_session_id = session_data.get("sessionId")

            # Submit image for liveness detection
            detect_url = f"{self.endpoint}/face/v1.1-preview.1/detectLiveness/singleModal/sessions/{azure_session_id}:detectLiveness"

            # Prepare multipart form data with image
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            detect_payload = {
                "image": {
                    "content": image_base64,
                    "contentType": session.image_content_type or "image/jpeg"
                }
            }

            detect_headers = self._get_headers()
            detect_response = await client.post(
                detect_url,
                json=detect_payload,
                headers=detect_headers
            )
            detect_response.raise_for_status()

            result = detect_response.json()

            # Parse result
            liveness_decision = result.get("livenessDecision", "uncertain")

            if liveness_decision.lower() == "realface":
                liveness_result = LivenessResult.LIVE
                is_live = True
            elif liveness_decision.lower() == "spoofface":
                liveness_result = LivenessResult.SPOOF
                is_live = False
            else:
                liveness_result = LivenessResult.UNCERTAIN
                is_live = False

            confidence = result.get("livenessScore", 0.0)

            return LivenessCheckResult(
                is_live=is_live,
                result=liveness_result,
                confidence=confidence,
                session_id=azure_session_id,
                raw_response=result
            )

    async def delete_liveness_session(self, azure_session_id: str):
        """
        Delete a liveness session from Azure Face API.

        Args:
            azure_session_id: The Azure session to delete
        """
        url = f"{self.endpoint}/face/v1.1-preview.1/detectLiveness/singleModal/sessions/{azure_session_id}"

        headers = self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers)
            if response.status_code == 404:
                logger.warning(f"Azure session not found for deletion: {azure_session_id}")
            else:
                response.raise_for_status()
                logger.info(f"Deleted Azure liveness session: {azure_session_id}")


class LivenessWithVerificationService(AzureLivenessService):
    """
    Extended liveness service with face verification.

    Combines liveness detection with face matching against a reference image.
    Useful for identity verification workflows.
    """

    async def create_liveness_with_verify_session(
        self,
        session: LivenessSession,
        reference_image: bytes,
        device_correlation_id: Optional[str] = None
    ) -> dict:
        """
        Create a liveness session that also verifies against a reference image.

        Args:
            session: The pipeline session
            reference_image: Reference face image for verification
            device_correlation_id: Optional device identifier

        Returns:
            Session creation response with verification enabled
        """
        url = f"{self.endpoint}/face/v1.1-preview.1/detectLivenessWithVerify/singleModal/sessions"

        reference_base64 = base64.b64encode(reference_image).decode("utf-8")

        payload = {
            "livenessOperationMode": "Passive",
            "sendResultsToClient": True,
            "deviceCorrelationId": device_correlation_id or session.session_id,
            "authTokenTimeToLiveInSeconds": 600,
            "verifyImage": {
                "content": reference_base64,
                "contentType": "image/jpeg"
            }
        }

        headers = self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Created Azure liveness+verify session: {result.get('sessionId')}")

            return {
                "azure_session_id": result.get("sessionId"),
                "auth_token": result.get("authToken"),
                "pipeline_session_id": session.session_id,
                "pipeline_token": session.token.value
            }

    async def get_liveness_with_verify_result(
        self,
        azure_session_id: str
    ) -> Tuple[LivenessCheckResult, dict]:
        """
        Get result of liveness detection with face verification.

        Args:
            azure_session_id: The Azure session ID

        Returns:
            Tuple of (LivenessCheckResult, verification_result)
        """
        url = f"{self.endpoint}/face/v1.1-preview.1/detectLivenessWithVerify/singleModal/sessions/{azure_session_id}"

        headers = self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            result = response.json()

            # Parse liveness result
            liveness_decision = result.get("result", {}).get("livenessDecision", "uncertain")

            if liveness_decision.lower() == "realface":
                liveness_result = LivenessResult.LIVE
                is_live = True
            elif liveness_decision.lower() == "spoofface":
                liveness_result = LivenessResult.SPOOF
                is_live = False
            else:
                liveness_result = LivenessResult.UNCERTAIN
                is_live = False

            confidence = result.get("result", {}).get("livenessScore", 0.0)

            liveness_check = LivenessCheckResult(
                is_live=is_live,
                result=liveness_result,
                confidence=confidence,
                session_id=azure_session_id,
                raw_response=result
            )

            # Parse verification result
            verification_result = {
                "is_identical": result.get("result", {}).get("verifyResult", {}).get("isIdentical", False),
                "confidence": result.get("result", {}).get("verifyResult", {}).get("matchConfidence", 0.0)
            }

            return liveness_check, verification_result
