"""
Tests for session models and token generation
"""
import pytest
from datetime import datetime, timedelta

from src.models.session import (
    HexToken,
    LivenessSession,
    SessionStatus,
    LivenessResult,
    PipelineRequest,
    PipelineResponse
)


class TestHexToken:
    """Tests for HexToken generation and validation"""

    def test_generate_creates_valid_token(self):
        """Token generation creates a 64-character hex string"""
        token = HexToken.generate()

        assert token.value is not None
        assert len(token.value) == 64  # 32 bytes = 64 hex chars
        assert all(c in '0123456789ABCDEF' for c in token.value)

    def test_generate_sets_correct_expiry(self):
        """Token expiry is set correctly based on validity minutes"""
        validity_minutes = 15
        token = HexToken.generate(validity_minutes=validity_minutes)

        expected_expiry = token.created_at + timedelta(minutes=validity_minutes)
        # Allow 1 second tolerance
        assert abs((token.expires_at - expected_expiry).total_seconds()) < 1

    def test_is_valid_returns_true_for_fresh_token(self):
        """Fresh tokens are valid"""
        token = HexToken.generate(validity_minutes=10)
        assert token.is_valid() is True

    def test_is_valid_returns_false_for_expired_token(self):
        """Expired tokens are invalid"""
        token = HexToken(
            value="TEST",
            created_at=datetime.utcnow() - timedelta(minutes=20),
            expires_at=datetime.utcnow() - timedelta(minutes=10)
        )
        assert token.is_valid() is False

    def test_to_dict_returns_correct_structure(self):
        """to_dict returns properly formatted dictionary"""
        token = HexToken.generate()
        result = token.to_dict()

        assert "token" in result
        assert "created_at" in result
        assert "expires_at" in result
        assert result["token"] == token.value

    def test_tokens_are_unique(self):
        """Each generated token is unique"""
        tokens = [HexToken.generate().value for _ in range(100)]
        assert len(set(tokens)) == 100


class TestLivenessSession:
    """Tests for LivenessSession management"""

    def test_create_generates_unique_session_id(self):
        """Session creation generates unique IDs"""
        session1 = LivenessSession.create(client_id="client1")
        session2 = LivenessSession.create(client_id="client1")

        assert session1.session_id != session2.session_id

    def test_create_attaches_hex_token(self):
        """Session creation includes a hex token"""
        session = LivenessSession.create(client_id="client1")

        assert session.token is not None
        assert len(session.token.value) == 64
        assert session.token.is_valid()

    def test_create_sets_initial_status(self):
        """New sessions start with CREATED status"""
        session = LivenessSession.create(client_id="client1")
        assert session.status == SessionStatus.CREATED

    def test_update_status_changes_status_and_timestamp(self):
        """update_status modifies status and updates timestamp"""
        session = LivenessSession.create(client_id="client1")
        original_updated = session.updated_at

        session.update_status(SessionStatus.TOKEN_ATTACHED)

        assert session.status == SessionStatus.TOKEN_ATTACHED
        assert session.updated_at >= original_updated

    def test_update_status_can_set_error_message(self):
        """update_status can set error message"""
        session = LivenessSession.create(client_id="client1")
        session.update_status(SessionStatus.ERROR, "Something went wrong")

        assert session.status == SessionStatus.ERROR
        assert session.error_message == "Something went wrong"

    def test_attach_image_updates_status(self):
        """attach_image sets status to IMAGE_RECEIVED"""
        session = LivenessSession.create(client_id="client1")
        session.attach_image(b"fake image data", "image/jpeg")

        assert session.status == SessionStatus.IMAGE_RECEIVED
        assert session.image_data == b"fake image data"
        assert session.image_content_type == "image/jpeg"

    def test_set_liveness_result_live(self):
        """Setting LIVE result updates status to LIVENESS_COMPLETED"""
        session = LivenessSession.create(client_id="client1")
        session.set_liveness_result(
            result=LivenessResult.LIVE,
            confidence=0.95,
            response={"test": "data"}
        )

        assert session.status == SessionStatus.LIVENESS_COMPLETED
        assert session.liveness_result == LivenessResult.LIVE
        assert session.liveness_confidence == 0.95
        assert session.liveness_response == {"test": "data"}

    def test_set_liveness_result_spoof(self):
        """Setting SPOOF result updates status to LIVENESS_FAILED"""
        session = LivenessSession.create(client_id="client1")
        session.set_liveness_result(
            result=LivenessResult.SPOOF,
            confidence=0.85,
            response={}
        )

        assert session.status == SessionStatus.LIVENESS_FAILED
        assert session.liveness_result == LivenessResult.SPOOF

    def test_set_ams_response(self):
        """Setting AMS response updates status to AMS_SUBMITTED"""
        session = LivenessSession.create(client_id="client1")
        session.set_ams_response(
            applicant_id="APP123",
            response={"id": "APP123"}
        )

        assert session.status == SessionStatus.AMS_SUBMITTED
        assert session.applicant_id == "APP123"
        assert session.ams_response == {"id": "APP123"}

    def test_complete_sets_final_status(self):
        """complete() sets status to COMPLETED"""
        session = LivenessSession.create(client_id="client1")
        session.complete()

        assert session.status == SessionStatus.COMPLETED

    def test_to_dict_includes_all_fields(self):
        """to_dict returns complete session data"""
        session = LivenessSession.create(client_id="client1")
        session.set_liveness_result(LivenessResult.LIVE, 0.9, {})
        session.set_ams_response("APP123", {})

        result = session.to_dict()

        assert result["session_id"] == session.session_id
        assert result["client_id"] == "client1"
        assert result["status"] == "ams_submitted"
        assert result["liveness_result"] == "live"
        assert result["applicant_id"] == "APP123"


class TestPipelineRequest:
    """Tests for PipelineRequest model"""

    def test_create_with_minimal_data(self):
        """Request can be created with just client_id"""
        request = PipelineRequest(
            client_id="client1",
            applicant_data={}
        )

        assert request.client_id == "client1"
        assert request.applicant_data == {}
        assert request.callback_url is None
        assert request.metadata == {}

    def test_create_with_full_data(self):
        """Request can include all optional fields"""
        request = PipelineRequest(
            client_id="client1",
            applicant_data={"name": "John"},
            callback_url="https://callback.example.com",
            metadata={"source": "mobile"}
        )

        assert request.client_id == "client1"
        assert request.applicant_data == {"name": "John"}
        assert request.callback_url == "https://callback.example.com"
        assert request.metadata == {"source": "mobile"}


class TestPipelineResponse:
    """Tests for PipelineResponse model"""

    def test_from_session_creates_correct_response(self):
        """from_session creates response from session"""
        session = LivenessSession.create(client_id="client1")
        session.set_liveness_result(LivenessResult.LIVE, 0.95, {})
        session.set_ams_response("APP123", {})

        response = PipelineResponse.from_session(session)

        assert response.session_id == session.session_id
        assert response.status == "ams_submitted"
        assert response.token == session.token.value
        assert response.liveness_result == "live"
        assert response.liveness_confidence == 0.95
        assert response.applicant_id == "APP123"

    def test_to_dict_returns_correct_structure(self):
        """to_dict returns properly formatted dictionary"""
        session = LivenessSession.create(client_id="client1")
        response = PipelineResponse.from_session(session)
        result = response.to_dict()

        assert "session_id" in result
        assert "status" in result
        assert "token" in result
        assert "token_expires_at" in result


class TestSessionStatus:
    """Tests for SessionStatus enum"""

    def test_all_statuses_have_string_values(self):
        """All statuses have lowercase string values"""
        expected_statuses = [
            "created",
            "token_attached",
            "image_received",
            "liveness_pending",
            "liveness_completed",
            "liveness_failed",
            "ams_submitted",
            "completed",
            "expired",
            "error"
        ]

        actual_values = [s.value for s in SessionStatus]
        assert sorted(actual_values) == sorted(expected_statuses)


class TestLivenessResult:
    """Tests for LivenessResult enum"""

    def test_all_results_have_string_values(self):
        """All results have lowercase string values"""
        expected_results = ["live", "spoof", "uncertain"]

        actual_values = [r.value for r in LivenessResult]
        assert sorted(actual_values) == sorted(expected_results)
