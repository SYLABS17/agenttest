"""Data models for the query pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class UserContext:
    """Context about the user making the query."""

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    grade_level: str = "unknown"
    board: str = "curriculum_board"
    subjects: list[str] = field(default_factory=list)
    language: str = "en"


@dataclass
class QueryRequest:
    """Incoming query request."""

    query: str
    source_language: str
    user_context: UserContext = field(default_factory=UserContext)
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Optional overrides
    force_native_index: bool = False
    include_video: bool = True
    max_chunks: int = 7


@dataclass
class SourceReference:
    """Reference to a source document."""

    source_type: str
    board: str
    subject: str
    grade_level: str
    chapter: Optional[str] = None
    page_number: Optional[int] = None


@dataclass
class VideoReference:
    """Reference to a video segment."""

    video_id: str
    title: str
    instructor: str
    start_timestamp: str
    end_timestamp: str
    url: str
    thumbnail_url: str


@dataclass
class QueryResponse:
    """Response to a query."""

    query_id: str
    answer: str
    language: str
    sources: list[SourceReference]
    video_segments: list[VideoReference]
    confidence: float
    route_used: str
    translation_confidence: float
    grounded: bool

    # Metadata
    latency_ms: float = 0.0
    tokens_used: int = 0
    model: str = ""

    # For follow-up questions
    context_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "query_id": self.query_id,
            "answer": self.answer,
            "language": self.language,
            "sources": [
                {
                    "source_type": s.source_type,
                    "board": s.board,
                    "subject": s.subject,
                    "grade_level": s.grade_level,
                    "chapter": s.chapter,
                    "page_number": s.page_number,
                }
                for s in self.sources
            ],
            "video_segments": [
                {
                    "video_id": v.video_id,
                    "title": v.title,
                    "instructor": v.instructor,
                    "segment": f"{v.start_timestamp} - {v.end_timestamp}",
                    "url": v.url,
                    "thumbnail_url": v.thumbnail_url,
                }
                for v in self.video_segments
            ],
            "confidence": self.confidence,
            "metadata": {
                "route_used": self.route_used,
                "translation_confidence": self.translation_confidence,
                "grounded": self.grounded,
                "latency_ms": self.latency_ms,
                "tokens_used": self.tokens_used,
                "model": self.model,
            },
        }
