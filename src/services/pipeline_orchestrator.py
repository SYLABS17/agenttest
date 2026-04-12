"""
Liveness Detection Pipeline Orchestrator

Coordinates the complete workflow:
1. Session creation with hex token generation
2. Azure Face API liveness detection
3. Applicant Management System submission
"""
import logging
from typing import Optional
from dataclasses import dataclass

from ..models.session import (
    LivenessSession,
    SessionStatus,
    LivenessResult,
    PipelineRequest,
    PipelineResponse
)
from .session_store import SessionStore
from .liveness_service import AzureLivenessService, LivenessCheckResult
from .applicant_service import ApplicantManagementService, AMSSubmissionResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the pipeline orchestrator"""
    token_validity_minutes: int = 10
    require_live_result_for_ams: bool = True
    auto_cleanup_expired: bool = True
    min_liveness_confidence: float = 0.8


class LivenessPipelineOrchestrator:
    """
    Main orchestrator for the liveness detection pipeline.

    Manages the complete workflow from session initialization
    through liveness detection to AMS submission.

    Workflow:
    1. Client requests new session -> generates session + hex token
    2. Client submits image with token -> validates token
    3. Image sent to Azure Liveness API -> liveness determination
    4. If live, submit to AMS -> applicant created
    5. Return final result to client

    Supports both:
    - Mobile SDK flow (client-side liveness detection)
    - Server-side flow (image submitted directly)
    """

    def __init__(
        self,
        session_store: SessionStore,
        liveness_service: AzureLivenessService,
        ams_service: ApplicantManagementService,
        config: Optional[PipelineConfig] = None
    ):
        """
        Initialize the pipeline orchestrator.

        Args:
            session_store: Session persistence service
            liveness_service: Azure liveness detection service
            ams_service: Applicant management service
            config: Pipeline configuration
        """
        self.session_store = session_store
        self.liveness_service = liveness_service
        self.ams_service = ams_service
        self.config = config or PipelineConfig()

    async def start_session(self, request: PipelineRequest) -> PipelineResponse:
        """
        Start a new liveness detection session.

        Creates a session with a unique hex token that must be
        included with all subsequent requests.

        Args:
            request: Pipeline request with client and applicant info

        Returns:
            PipelineResponse with session ID and hex token
        """
        # Create new session with hex token
        session = LivenessSession.create(
            client_id=request.client_id,
            token_validity_minutes=self.config.token_validity_minutes
        )
        session.metadata = {
            "applicant_data": request.applicant_data,
            "callback_url": request.callback_url,
            **request.metadata
        }
        session.update_status(SessionStatus.TOKEN_ATTACHED)

        # Persist session
        self.session_store.create_session(session)

        logger.info(f"Started session {session.session_id} for client {request.client_id}")

        return PipelineResponse.from_session(session)

    async def create_mobile_liveness_session(
        self,
        session_id: str,
        token: str,
        device_correlation_id: Optional[str] = None
    ) -> dict:
        """
        Create an Azure liveness session for mobile SDK integration.

        Mobile apps call this to get the Azure auth token needed
        for client-side liveness detection.

        Args:
            session_id: The pipeline session ID
            token: The hex token for validation
            device_correlation_id: Optional device identifier

        Returns:
            Azure session info with auth token for mobile SDK
        """
        # Validate token and get session
        session = self.session_store.get_session_by_token(token)

        if not session:
            raise ValueError("Invalid or expired token")

        if session.session_id != session_id:
            raise ValueError("Token does not match session")

        # Create Azure liveness session
        azure_session = await self.liveness_service.create_liveness_session(
            session,
            device_correlation_id
        )

        # Update session status
        session.update_status(SessionStatus.LIVENESS_PENDING)
        session.metadata["azure_session_id"] = azure_session["azure_session_id"]
        self.session_store.update_session(session)

        return azure_session

    async def complete_mobile_liveness(
        self,
        session_id: str,
        token: str,
        azure_session_id: str
    ) -> PipelineResponse:
        """
        Complete the mobile liveness flow after SDK finishes.

        Called by mobile app after Azure SDK liveness check completes.
        Retrieves result from Azure and proceeds to AMS submission if live.

        Args:
            session_id: The pipeline session ID
            token: The hex token for validation
            azure_session_id: The Azure Face API session ID

        Returns:
            PipelineResponse with final result
        """
        # Validate token and get session
        session = self.session_store.get_session_by_token(token)

        if not session:
            raise ValueError("Invalid or expired token")

        if session.session_id != session_id:
            raise ValueError("Token does not match session")

        # Get liveness result from Azure
        liveness_result = await self.liveness_service.get_liveness_session_result(
            azure_session_id
        )

        # Update session with liveness result
        session.set_liveness_result(
            result=liveness_result.result,
            confidence=liveness_result.confidence,
            response=liveness_result.raw_response
        )
        self.session_store.update_session(session)

        # If live and meets confidence threshold, submit to AMS
        if liveness_result.is_live and liveness_result.confidence >= self.config.min_liveness_confidence:
            await self._submit_to_ams(session)

        return PipelineResponse.from_session(session)

    async def submit_image(
        self,
        session_id: str,
        token: str,
        image_data: bytes,
        content_type: str = "image/jpeg"
    ) -> PipelineResponse:
        """
        Submit an image for server-side liveness detection.

        Alternative to mobile SDK flow - sends image directly
        to Azure for liveness detection.

        Args:
            session_id: The pipeline session ID
            token: The hex token for validation
            image_data: Raw image bytes
            content_type: Image MIME type

        Returns:
            PipelineResponse with liveness result
        """
        # Validate token and get session
        session = self.session_store.get_session_by_token(token)

        if not session:
            raise ValueError("Invalid or expired token")

        if session.session_id != session_id:
            raise ValueError("Token does not match session")

        # Attach image to session
        session.attach_image(image_data, content_type)
        session.update_status(SessionStatus.LIVENESS_PENDING)
        self.session_store.update_session(session)

        # Perform liveness detection
        try:
            liveness_result = await self.liveness_service.detect_liveness_from_image(
                image_data,
                session
            )

            # Update session with result
            session.set_liveness_result(
                result=liveness_result.result,
                confidence=liveness_result.confidence,
                response=liveness_result.raw_response
            )
            self.session_store.update_session(session)

            # If live and meets confidence threshold, submit to AMS
            if liveness_result.is_live and liveness_result.confidence >= self.config.min_liveness_confidence:
                await self._submit_to_ams(session)

        except Exception as e:
            logger.error(f"Liveness detection failed for session {session_id}: {e}")
            session.update_status(SessionStatus.ERROR, str(e))
            session.error_code = "LIVENESS_DETECTION_FAILED"
            self.session_store.update_session(session)

        return PipelineResponse.from_session(session)

    async def _submit_to_ams(self, session: LivenessSession) -> Optional[AMSSubmissionResult]:
        """
        Submit verified applicant to AMS.

        Args:
            session: The session with completed liveness check

        Returns:
            AMS submission result if successful
        """
        if self.config.require_live_result_for_ams:
            if session.liveness_result != LivenessResult.LIVE:
                logger.info(f"Skipping AMS submission - not live: {session.session_id}")
                return None

        applicant_data = session.metadata.get("applicant_data", {})

        try:
            result = await self.ams_service.submit_applicant(
                session,
                applicant_data
            )

            if result.success:
                session.set_ams_response(result.applicant_id, result.raw_response)
                session.complete()
                logger.info(f"AMS submission successful: {result.applicant_id}")
            else:
                session.update_status(SessionStatus.ERROR, result.message)
                session.error_code = "AMS_SUBMISSION_FAILED"
                logger.error(f"AMS submission failed: {result.message}")

            self.session_store.update_session(session)
            return result

        except Exception as e:
            logger.error(f"AMS submission error for session {session.session_id}: {e}")
            session.update_status(SessionStatus.ERROR, str(e))
            session.error_code = "AMS_SUBMISSION_ERROR"
            self.session_store.update_session(session)
            return None

    async def get_session_status(self, session_id: str, token: str) -> PipelineResponse:
        """
        Get the current status of a session.

        Args:
            session_id: The pipeline session ID
            token: The hex token for validation

        Returns:
            Current session status
        """
        session = self.session_store.get_session_by_token(token)

        if not session:
            raise ValueError("Invalid or expired token")

        if session.session_id != session_id:
            raise ValueError("Token does not match session")

        return PipelineResponse.from_session(session)

    async def cancel_session(self, session_id: str, token: str) -> bool:
        """
        Cancel an active session.

        Args:
            session_id: The pipeline session ID
            token: The hex token for validation

        Returns:
            True if cancelled successfully
        """
        session = self.session_store.get_session_by_token(token)

        if not session:
            return False

        if session.session_id != session_id:
            return False

        # Clean up Azure session if exists
        azure_session_id = session.metadata.get("azure_session_id")
        if azure_session_id:
            try:
                await self.liveness_service.delete_liveness_session(azure_session_id)
            except Exception as e:
                logger.warning(f"Failed to delete Azure session: {e}")

        # Delete session
        self.session_store.delete_session(session.client_id, session_id)
        logger.info(f"Cancelled session: {session_id}")

        return True

    async def cleanup_expired(self, client_id: Optional[str] = None) -> int:
        """
        Clean up expired sessions.

        Args:
            client_id: Optional client ID to limit cleanup scope

        Returns:
            Number of sessions cleaned up
        """
        return self.session_store.cleanup_expired_sessions(client_id)
