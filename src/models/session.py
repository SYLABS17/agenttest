"""
Session and Token Models for Liveness Detection Pipeline
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import uuid
import secrets


class SessionStatus(Enum):
    """Session lifecycle states"""
    CREATED = "created"
    TOKEN_ATTACHED = "token_attached"
    IMAGE_RECEIVED = "image_received"
    LIVENESS_PENDING = "liveness_pending"
    LIVENESS_COMPLETED = "liveness_completed"
    LIVENESS_FAILED = "liveness_failed"
    AMS_SUBMITTED = "ams_submitted"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ERROR = "error"


class LivenessResult(Enum):
    """Azure Liveness Detection results"""
    LIVE = "live"
    SPOOF = "spoof"
    UNCERTAIN = "uncertain"


@dataclass
class HexToken:
    """Hexadecimal token for request authentication"""
    value: str
    created_at: datetime
    expires_at: datetime

    @classmethod
    def generate(cls, validity_minutes: int = 10) -> "HexToken":
        """Generate a new cryptographically secure hex token"""
        # Generate 32-byte (256-bit) random token
        token_bytes = secrets.token_bytes(32)
        token_value = token_bytes.hex().upper()

        now = datetime.utcnow()
        return cls(
            value=token_value,
            created_at=now,
            expires_at=now + timedelta(minutes=validity_minutes)
        )

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return datetime.utcnow() < self.expires_at

    def to_dict(self) -> dict:
        return {
            "token": self.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }


@dataclass
class LivenessSession:
    """Session tracking for the liveness detection pipeline"""
    session_id: str
    client_id: str
    token: HexToken
    status: SessionStatus
    created_at: datetime
    updated_at: datetime

    # Pipeline data
    image_data: Optional[bytes] = None
    image_content_type: Optional[str] = None
    liveness_result: Optional[LivenessResult] = None
    liveness_confidence: Optional[float] = None
    liveness_response: Optional[dict] = None

    # Applicant Management System data
    applicant_id: Optional[str] = None
    ams_response: Optional[dict] = None

    # Error tracking
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Metadata
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(cls, client_id: str, token_validity_minutes: int = 10) -> "LivenessSession":
        """Create a new liveness detection session"""
        now = datetime.utcnow()
        return cls(
            session_id=str(uuid.uuid4()),
            client_id=client_id,
            token=HexToken.generate(token_validity_minutes),
            status=SessionStatus.CREATED,
            created_at=now,
            updated_at=now
        )

    def update_status(self, new_status: SessionStatus, error_message: Optional[str] = None):
        """Update session status"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if error_message:
            self.error_message = error_message

    def attach_image(self, image_data: bytes, content_type: str = "image/jpeg"):
        """Attach captured image to session"""
        self.image_data = image_data
        self.image_content_type = content_type
        self.update_status(SessionStatus.IMAGE_RECEIVED)

    def set_liveness_result(
        self,
        result: LivenessResult,
        confidence: float,
        response: dict
    ):
        """Set liveness detection result"""
        self.liveness_result = result
        self.liveness_confidence = confidence
        self.liveness_response = response

        if result == LivenessResult.LIVE:
            self.update_status(SessionStatus.LIVENESS_COMPLETED)
        else:
            self.update_status(SessionStatus.LIVENESS_FAILED)

    def set_ams_response(self, applicant_id: str, response: dict):
        """Set Applicant Management System response"""
        self.applicant_id = applicant_id
        self.ams_response = response
        self.update_status(SessionStatus.AMS_SUBMITTED)

    def complete(self):
        """Mark session as completed"""
        self.update_status(SessionStatus.COMPLETED)

    def to_dict(self) -> dict:
        """Convert session to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "client_id": self.client_id,
            "token": self.token.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "liveness_result": self.liveness_result.value if self.liveness_result else None,
            "liveness_confidence": self.liveness_confidence,
            "applicant_id": self.applicant_id,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "metadata": self.metadata
        }


@dataclass
class PipelineRequest:
    """Request model for the liveness pipeline"""
    client_id: str
    applicant_data: dict
    callback_url: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineResponse:
    """Response model for the liveness pipeline"""
    session_id: str
    status: str
    token: str
    token_expires_at: str
    liveness_result: Optional[str] = None
    liveness_confidence: Optional[float] = None
    applicant_id: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_session(cls, session: LivenessSession) -> "PipelineResponse":
        return cls(
            session_id=session.session_id,
            status=session.status.value,
            token=session.token.value,
            token_expires_at=session.token.expires_at.isoformat(),
            liveness_result=session.liveness_result.value if session.liveness_result else None,
            liveness_confidence=session.liveness_confidence,
            applicant_id=session.applicant_id,
            error=session.error_message
        )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "token": self.token,
            "token_expires_at": self.token_expires_at,
            "liveness_result": self.liveness_result,
            "liveness_confidence": self.liveness_confidence,
            "applicant_id": self.applicant_id,
            "error": self.error
        }
