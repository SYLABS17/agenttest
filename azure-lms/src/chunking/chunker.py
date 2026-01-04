"""Parent-child document chunking implementation."""

import re
from typing import Optional
import uuid

import structlog

from src.config import get_settings
from src.chunking.models import Chunk, ChunkMetadata

logger = structlog.get_logger(__name__)


class ParentChildChunker:
    """
    Hierarchical chunking strategy for educational content.

    Creates a two-level hierarchy:
    - Parent chunks: Larger context (e.g., full section on photosynthesis)
    - Child chunks: Smaller, specific segments (e.g., paragraph about light reactions)

    Benefits:
    - Semantic matching on specific child chunks
    - Full context available from parent for accurate LLM generation
    - Prevents fragmented, context-less responses
    """

    def __init__(
        self,
        parent_size: int = 2000,
        child_size: int = 400,
        overlap: int = 50,
    ):
        """
        Initialize the chunker.

        Args:
            parent_size: Target character size for parent chunks
            child_size: Target character size for child chunks
            overlap: Character overlap between chunks
        """
        self.settings = get_settings()
        self.parent_size = parent_size or self.settings.parent_chunk_size
        self.child_size = child_size or self.settings.child_chunk_size
        self.overlap = overlap or self.settings.chunk_overlap

        # Sentence-ending patterns for clean breaks
        self.sentence_pattern = re.compile(r'(?<=[.!?।॥])\s+')

        # Section header patterns
        self.section_patterns = [
            re.compile(r'^#{1,6}\s+.+$', re.MULTILINE),  # Markdown headers
            re.compile(r'^Chapter\s+\d+', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^Section\s+\d+', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^\d+\.\d+\s+[A-Z]', re.MULTILINE),  # Numbered sections
        ]

    def chunk_document(
        self,
        content: str,
        metadata: ChunkMetadata,
    ) -> list[Chunk]:
        """
        Chunk a document into parent-child hierarchy.

        Args:
            content: Full document text
            metadata: Metadata to attach to all chunks

        Returns:
            List of chunks (both parents and children)
        """
        if not content or not content.strip():
            logger.warning("empty_document_skipped")
            return []

        logger.debug(
            "chunking_document",
            content_length=len(content),
            source=metadata.source_type,
        )

        # First, create parent chunks
        parents = self._create_parent_chunks(content, metadata)

        # Then, create child chunks for each parent
        all_chunks = []
        for parent in parents:
            all_chunks.append(parent)
            children = self._create_child_chunks(parent, metadata)
            all_chunks.extend(children)

        logger.info(
            "document_chunked",
            parent_count=len(parents),
            total_chunks=len(all_chunks),
        )

        return all_chunks

    def _create_parent_chunks(
        self,
        content: str,
        metadata: ChunkMetadata,
    ) -> list[Chunk]:
        """
        Create parent-level chunks from document.

        Respects natural section boundaries where possible.
        """
        # Try to split by sections first
        sections = self._split_by_sections(content)

        parents = []
        for section in sections:
            if not section.strip():
                continue

            # If section is too large, split further
            if len(section) > self.parent_size * 1.5:
                sub_sections = self._split_by_size(
                    section, self.parent_size, self.overlap
                )
                for sub in sub_sections:
                    parents.append(self._create_parent_chunk(sub, metadata))
            else:
                parents.append(self._create_parent_chunk(section, metadata))

        return parents

    def _create_parent_chunk(
        self,
        content: str,
        metadata: ChunkMetadata,
    ) -> Chunk:
        """Create a single parent chunk."""
        return Chunk(
            id=str(uuid.uuid4()),
            content=content.strip(),
            parent_id=None,
            is_parent=True,
            metadata=metadata,
            start_char=0,  # Would be set properly in full implementation
            end_char=len(content),
        )

    def _create_child_chunks(
        self,
        parent: Chunk,
        metadata: ChunkMetadata,
    ) -> list[Chunk]:
        """
        Create child chunks from a parent chunk.

        Each child references its parent for context expansion.
        """
        children = []
        content = parent.content

        # Split into sentences first for cleaner boundaries
        sentences = self.sentence_pattern.split(content)

        current_chunk = ""
        current_start = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if adding this sentence exceeds child size
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence

            if len(test_chunk) > self.child_size and current_chunk:
                # Save current chunk and start new one
                child = Chunk(
                    id=str(uuid.uuid4()),
                    content=current_chunk.strip(),
                    parent_id=parent.id,
                    is_parent=False,
                    metadata=metadata,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                )
                children.append(child)

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                current_start = current_start + len(current_chunk) - len(overlap_text)
            else:
                current_chunk = test_chunk

        # Add final chunk
        if current_chunk.strip():
            child = Chunk(
                id=str(uuid.uuid4()),
                content=current_chunk.strip(),
                parent_id=parent.id,
                is_parent=False,
                metadata=metadata,
                start_char=current_start,
                end_char=current_start + len(current_chunk),
            )
            children.append(child)

        return children

    def _split_by_sections(self, content: str) -> list[str]:
        """Split content by natural section boundaries."""
        # Find all section markers
        markers = []
        for pattern in self.section_patterns:
            for match in pattern.finditer(content):
                markers.append(match.start())

        if not markers:
            return [content]

        # Sort markers and split
        markers = sorted(set(markers))
        sections = []
        prev = 0

        for marker in markers:
            if marker > prev:
                sections.append(content[prev:marker])
            prev = marker

        # Add final section
        if prev < len(content):
            sections.append(content[prev:])

        return sections

    def _split_by_size(
        self,
        content: str,
        target_size: int,
        overlap: int,
    ) -> list[str]:
        """Split content by target size with overlap."""
        chunks = []
        sentences = self.sentence_pattern.split(content)

        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) > target_size and current:
                chunks.append(current.strip())
                # Get overlap from end of current chunk
                overlap_text = current[-overlap:] if len(current) > overlap else current
                current = overlap_text + " " + sentence
            else:
                current = current + " " + sentence if current else sentence

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from end of a chunk."""
        if len(text) <= self.overlap:
            return text

        # Try to break at sentence boundary within overlap zone
        overlap_zone = text[-self.overlap * 2:]
        sentences = self.sentence_pattern.split(overlap_zone)

        if len(sentences) > 1:
            return sentences[-1].strip()

        return text[-self.overlap:]

    def get_parent_context(self, chunk: Chunk) -> Optional[Chunk]:
        """
        Retrieve parent chunk for a matched child chunk.

        This is typically called after search to expand context.
        In production, this would query the search index.

        Args:
            chunk: Child chunk that was matched

        Returns:
            Parent chunk if available, None otherwise
        """
        if chunk.is_parent:
            return chunk

        # In production, this queries the index for parent_id
        # Here we return None as placeholder
        logger.debug(
            "get_parent_context",
            child_id=chunk.id,
            parent_id=chunk.parent_id,
        )
        return None

    def chunk_video_transcript(
        self,
        transcript_segments: list[dict],
        metadata: ChunkMetadata,
    ) -> list[Chunk]:
        """
        Chunk video transcript with timestamp preservation.

        Args:
            transcript_segments: List of {text, start, end} segments
            metadata: Base metadata for chunks

        Returns:
            List of chunks with video timestamps
        """
        chunks = []

        current_text = ""
        current_start = None
        current_end = None

        for segment in transcript_segments:
            text = segment.get("text", "").strip()
            start = segment.get("start", 0)
            end = segment.get("end", 0)

            if not text:
                continue

            if current_start is None:
                current_start = start

            test_text = current_text + " " + text if current_text else text

            if len(test_text) > self.child_size and current_text:
                # Create chunk with current content
                chunk_metadata = ChunkMetadata(
                    source_type="video_transcript",
                    subject=metadata.subject,
                    grade_level=metadata.grade_level,
                    board=metadata.board,
                    video_id=metadata.video_id,
                    start_timestamp=self._format_timestamp(current_start),
                    end_timestamp=self._format_timestamp(current_end),
                    instructor=metadata.instructor,
                    language=metadata.language,
                )

                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    content=current_text.strip(),
                    metadata=chunk_metadata,
                )
                chunks.append(chunk)

                # Start new chunk
                current_text = text
                current_start = start
                current_end = end
            else:
                current_text = test_text
                current_end = end

        # Add final chunk
        if current_text.strip():
            chunk_metadata = ChunkMetadata(
                source_type="video_transcript",
                subject=metadata.subject,
                grade_level=metadata.grade_level,
                board=metadata.board,
                video_id=metadata.video_id,
                start_timestamp=self._format_timestamp(current_start),
                end_timestamp=self._format_timestamp(current_end),
                instructor=metadata.instructor,
                language=metadata.language,
            )

            chunk = Chunk(
                id=str(uuid.uuid4()),
                content=current_text.strip(),
                metadata=chunk_metadata,
            )
            chunks.append(chunk)

        logger.info(
            "video_transcript_chunked",
            chunk_count=len(chunks),
            video_id=metadata.video_id,
        )

        return chunks

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS."""
        if seconds is None:
            return "00:00"

        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
