"""Data models for document chunks."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class ChunkMetadata:
    """Metadata associated with a document chunk."""

    source_type: str  # "textbook", "lecture_notes", "video_transcript", etc.
    subject: str  # "biology", "mathematics", "physics", etc.
    grade_level: str  # "class_10", "undergraduate", etc.
    board: str  # "curriculum_board", "state_board", etc.
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None
    language: str = "en"

    # Video-specific metadata
    video_id: Optional[str] = None
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    instructor: Optional[str] = None

    # Processing metadata
    processed_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"


@dataclass
class Chunk:
    """
    Represents a document chunk with hierarchical relationship.

    Parent chunks provide context, child chunks enable precise matching.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    parent_id: Optional[str] = None
    is_parent: bool = False
    metadata: ChunkMetadata = field(default_factory=lambda: ChunkMetadata(
        source_type="unknown",
        subject="unknown",
        grade_level="unknown",
        board="unknown",
    ))

    # Position within source document
    start_char: int = 0
    end_char: int = 0

    # Embedding (populated during indexing)
    embedding: Optional[list[float]] = None

    def __post_init__(self):
        """Validate chunk after initialization."""
        if not self.content:
            raise ValueError("Chunk content cannot be empty")

    @property
    def char_length(self) -> int:
        """Return character length of content."""
        return len(self.content)

    @property
    def word_count(self) -> int:
        """Return approximate word count."""
        return len(self.content.split())

    def to_dict(self) -> dict:
        """Convert to dictionary for indexing."""
        return {
            "id": self.id,
            "content": self.content,
            "parent_id": self.parent_id,
            "is_parent": self.is_parent,
            "source_type": self.metadata.source_type,
            "subject": self.metadata.subject,
            "grade_level": self.metadata.grade_level,
            "board": self.metadata.board,
            "chapter": self.metadata.chapter,
            "section": self.metadata.section,
            "page_number": self.metadata.page_number,
            "language": self.metadata.language,
            "video_id": self.metadata.video_id,
            "start_timestamp": self.metadata.start_timestamp,
            "end_timestamp": self.metadata.end_timestamp,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        """Create chunk from dictionary."""
        metadata = ChunkMetadata(
            source_type=data.get("source_type", "unknown"),
            subject=data.get("subject", "unknown"),
            grade_level=data.get("grade_level", "unknown"),
            board=data.get("board", "unknown"),
            chapter=data.get("chapter"),
            section=data.get("section"),
            page_number=data.get("page_number"),
            language=data.get("language", "en"),
            video_id=data.get("video_id"),
            start_timestamp=data.get("start_timestamp"),
            end_timestamp=data.get("end_timestamp"),
        )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data["content"],
            parent_id=data.get("parent_id"),
            is_parent=data.get("is_parent", False),
            metadata=metadata,
            start_char=data.get("start_char", 0),
            end_char=data.get("end_char", 0),
        )


@dataclass
class ChunkWithContext:
    """Chunk with its parent context for LLM generation."""

    matched_chunk: Chunk
    parent_chunk: Optional[Chunk]
    relevance_score: float = 0.0

    @property
    def context_text(self) -> str:
        """Get full context text (parent if available, else matched)."""
        if self.parent_chunk:
            return self.parent_chunk.content
        return self.matched_chunk.content

    @property
    def matched_text(self) -> str:
        """Get the specifically matched text."""
        return self.matched_chunk.content
