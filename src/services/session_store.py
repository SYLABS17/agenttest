"""
Session Store Service - Azure Table Storage backed session management
"""
import json
import logging
from datetime import datetime
from typing import Optional

from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from ..models.session import LivenessSession, SessionStatus, HexToken, LivenessResult

logger = logging.getLogger(__name__)


class SessionStore:
    """
    Azure Table Storage backed session store for liveness detection sessions.

    Uses Azure Table Storage for scalable, serverless session persistence.
    Sessions are partitioned by client_id for efficient queries.
    """

    TABLE_NAME = "LivenessSessions"

    def __init__(self, connection_string: str):
        """
        Initialize the session store.

        Args:
            connection_string: Azure Storage account connection string
        """
        self.table_service = TableServiceClient.from_connection_string(connection_string)
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create the sessions table if it doesn't exist"""
        try:
            self.table_service.create_table(self.TABLE_NAME)
            logger.info(f"Created table: {self.TABLE_NAME}")
        except ResourceExistsError:
            logger.debug(f"Table already exists: {self.TABLE_NAME}")

    def _get_table_client(self) -> TableClient:
        """Get table client for operations"""
        return self.table_service.get_table_client(self.TABLE_NAME)

    def _session_to_entity(self, session: LivenessSession) -> dict:
        """Convert session to Azure Table Storage entity"""
        return {
            "PartitionKey": session.client_id,
            "RowKey": session.session_id,
            "client_id": session.client_id,
            "session_id": session.session_id,
            "token_value": session.token.value,
            "token_created_at": session.token.created_at.isoformat(),
            "token_expires_at": session.token.expires_at.isoformat(),
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "liveness_result": session.liveness_result.value if session.liveness_result else None,
            "liveness_confidence": session.liveness_confidence,
            "liveness_response": json.dumps(session.liveness_response) if session.liveness_response else None,
            "applicant_id": session.applicant_id,
            "ams_response": json.dumps(session.ams_response) if session.ams_response else None,
            "error_message": session.error_message,
            "error_code": session.error_code,
            "metadata": json.dumps(session.metadata)
        }

    def _entity_to_session(self, entity: dict) -> LivenessSession:
        """Convert Azure Table Storage entity to session"""
        token = HexToken(
            value=entity["token_value"],
            created_at=datetime.fromisoformat(entity["token_created_at"]),
            expires_at=datetime.fromisoformat(entity["token_expires_at"])
        )

        liveness_result = None
        if entity.get("liveness_result"):
            liveness_result = LivenessResult(entity["liveness_result"])

        return LivenessSession(
            session_id=entity["session_id"],
            client_id=entity["client_id"],
            token=token,
            status=SessionStatus(entity["status"]),
            created_at=datetime.fromisoformat(entity["created_at"]),
            updated_at=datetime.fromisoformat(entity["updated_at"]),
            liveness_result=liveness_result,
            liveness_confidence=entity.get("liveness_confidence"),
            liveness_response=json.loads(entity["liveness_response"]) if entity.get("liveness_response") else None,
            applicant_id=entity.get("applicant_id"),
            ams_response=json.loads(entity["ams_response"]) if entity.get("ams_response") else None,
            error_message=entity.get("error_message"),
            error_code=entity.get("error_code"),
            metadata=json.loads(entity.get("metadata", "{}"))
        )

    def create_session(self, session: LivenessSession) -> LivenessSession:
        """
        Create a new session in the store.

        Args:
            session: The session to store

        Returns:
            The stored session

        Raises:
            ValueError: If session already exists
        """
        table_client = self._get_table_client()
        entity = self._session_to_entity(session)

        try:
            table_client.create_entity(entity)
            logger.info(f"Created session: {session.session_id}")
            return session
        except ResourceExistsError:
            raise ValueError(f"Session already exists: {session.session_id}")

    def get_session(self, client_id: str, session_id: str) -> Optional[LivenessSession]:
        """
        Retrieve a session from the store.

        Args:
            client_id: The client ID (partition key)
            session_id: The session ID (row key)

        Returns:
            The session if found, None otherwise
        """
        table_client = self._get_table_client()

        try:
            entity = table_client.get_entity(partition_key=client_id, row_key=session_id)
            return self._entity_to_session(entity)
        except ResourceNotFoundError:
            logger.warning(f"Session not found: {session_id}")
            return None

    def get_session_by_token(self, token: str) -> Optional[LivenessSession]:
        """
        Retrieve a session by its hex token.

        Args:
            token: The hex token value

        Returns:
            The session if found and token is valid, None otherwise
        """
        table_client = self._get_table_client()

        # Query by token value
        filter_query = f"token_value eq '{token}'"
        entities = table_client.query_entities(filter_query)

        for entity in entities:
            session = self._entity_to_session(entity)
            if session.token.is_valid():
                return session
            else:
                logger.warning(f"Token expired for session: {session.session_id}")
                return None

        return None

    def update_session(self, session: LivenessSession) -> LivenessSession:
        """
        Update an existing session.

        Args:
            session: The session with updated values

        Returns:
            The updated session
        """
        table_client = self._get_table_client()
        entity = self._session_to_entity(session)

        table_client.update_entity(entity, mode="replace")
        logger.info(f"Updated session: {session.session_id} -> {session.status.value}")
        return session

    def delete_session(self, client_id: str, session_id: str):
        """
        Delete a session from the store.

        Args:
            client_id: The client ID (partition key)
            session_id: The session ID (row key)
        """
        table_client = self._get_table_client()

        try:
            table_client.delete_entity(partition_key=client_id, row_key=session_id)
            logger.info(f"Deleted session: {session_id}")
        except ResourceNotFoundError:
            logger.warning(f"Session not found for deletion: {session_id}")

    def get_sessions_by_client(self, client_id: str, limit: int = 100) -> list[LivenessSession]:
        """
        Get all sessions for a client.

        Args:
            client_id: The client ID
            limit: Maximum number of sessions to return

        Returns:
            List of sessions for the client
        """
        table_client = self._get_table_client()

        filter_query = f"PartitionKey eq '{client_id}'"
        entities = table_client.query_entities(filter_query)

        sessions = []
        for i, entity in enumerate(entities):
            if i >= limit:
                break
            sessions.append(self._entity_to_session(entity))

        return sessions

    def cleanup_expired_sessions(self, client_id: Optional[str] = None) -> int:
        """
        Clean up expired sessions.

        Args:
            client_id: Optional client ID to limit cleanup scope

        Returns:
            Number of sessions cleaned up
        """
        table_client = self._get_table_client()
        now = datetime.utcnow().isoformat()

        filter_query = f"token_expires_at lt '{now}'"
        if client_id:
            filter_query = f"PartitionKey eq '{client_id}' and {filter_query}"

        entities = table_client.query_entities(filter_query)

        count = 0
        for entity in entities:
            table_client.delete_entity(
                partition_key=entity["PartitionKey"],
                row_key=entity["RowKey"]
            )
            count += 1

        logger.info(f"Cleaned up {count} expired sessions")
        return count
