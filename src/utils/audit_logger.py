"""
Audit Logger
Provides comprehensive audit trail for reproducibility and compliance.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class AuditLogger:
    """
    Audit trail logger for agent operations.
    Ensures reproducibility and provides compliance audit trail.
    """

    def __init__(self, log_dir: str = "audit_trails"):
        """
        Initialize the audit logger.

        Args:
            log_dir: Directory for audit trail files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.session_logs = {}

    async def log_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Log an event to the audit trail.

        Args:
            session_id: Session identifier
            event_type: Type of event
            data: Event data
        """
        if session_id not in self.session_logs:
            self.session_logs[session_id] = []

        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "event_type": event_type,
            "data": data
        }

        self.session_logs[session_id].append(event)

        # Also write to file immediately for persistence
        await self._write_to_file(session_id, event)

    async def _write_to_file(self, session_id: str, event: Dict[str, Any]):
        """
        Write event to audit trail file.

        Args:
            session_id: Session identifier
            event: Event data
        """
        log_file = self.log_dir / f"{session_id}_audit.jsonl"

        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    async def get_session_trail(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of audit events
        """
        if session_id in self.session_logs:
            return self.session_logs[session_id]

        # Read from file if not in memory
        log_file = self.log_dir / f"{session_id}_audit.jsonl"
        if log_file.exists():
            events = []
            with open(log_file, 'r') as f:
                for line in f:
                    events.append(json.loads(line))
            return events

        return []

    def generate_audit_report(
        self,
        session_id: str,
        output_format: str = "markdown"
    ) -> str:
        """
        Generate human-readable audit report.

        Args:
            session_id: Session identifier
            output_format: Output format (markdown, html, json)

        Returns:
            Formatted audit report
        """
        events = self.session_logs.get(session_id, [])

        if output_format == "markdown":
            return self._generate_markdown_report(session_id, events)
        elif output_format == "json":
            return json.dumps(events, indent=2)
        else:
            return self._generate_markdown_report(session_id, events)

    def _generate_markdown_report(
        self,
        session_id: str,
        events: List[Dict[str, Any]]
    ) -> str:
        """
        Generate markdown audit report.

        Args:
            session_id: Session identifier
            events: List of events

        Returns:
            Markdown formatted report
        """
        lines = [
            f"# Audit Trail Report",
            f"",
            f"**Session ID:** {session_id}",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Total Events:** {len(events)}",
            f"",
            f"## Event Timeline",
            f""
        ]

        for idx, event in enumerate(events, 1):
            lines.append(f"### {idx}. {event['event_type']}")
            lines.append(f"**Timestamp:** {event['timestamp']}")
            lines.append(f"**Data:**")
            lines.append(f"```json")
            lines.append(json.dumps(event['data'], indent=2))
            lines.append(f"```")
            lines.append(f"")

        return '\n'.join(lines)

    def get_copilot_studio_audit_reference(self, session_id: str) -> str:
        """
        Get Copilot Studio compatible audit trail reference.

        Args:
            session_id: Session identifier

        Returns:
            Audit trail reference string
        """
        log_file = self.log_dir / f"{session_id}_audit.jsonl"

        return (
            f"Copilot Studio Audit Trail Reference:\n"
            f"Session ID: {session_id}\n"
            f"Audit Log: {log_file.absolute()}\n"
            f"Timestamp: {datetime.now().isoformat()}\n"
            f"Event Count: {len(self.session_logs.get(session_id, []))}\n"
            f"Reproducibility: All decisions and evaluations logged for compliance"
        )
