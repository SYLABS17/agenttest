"""Tests for document chunking."""

import pytest
from src.chunking import ParentChildChunker, Chunk, ChunkMetadata


class TestParentChildChunker:
    """Tests for ParentChildChunker."""

    def test_chunk_document(self):
        """Test basic document chunking."""
        chunker = ParentChildChunker(
            parent_size=500,
            child_size=100,
            overlap=20,
        )

        content = """
        Photosynthesis is a process used by plants and other organisms to convert
        light energy into chemical energy. This chemical energy is stored in
        carbohydrate molecules, such as sugars, which are synthesized from carbon
        dioxide and water. In most cases, oxygen is released as a waste product.

        The light reaction occurs in the thylakoid membranes of the chloroplasts.
        During this phase, light energy is captured by chlorophyll and converted
        into chemical energy in the form of ATP and NADPH.
        """

        metadata = ChunkMetadata(
            source_type="textbook",
            subject="biology",
            grade_level="class_10",
            board="NCERT",
        )

        chunks = chunker.chunk_document(content, metadata)

        assert len(chunks) > 0
        # Should have at least one parent and children
        parents = [c for c in chunks if c.is_parent]
        children = [c for c in chunks if not c.is_parent]
        assert len(parents) >= 1

    def test_parent_child_relationship(self):
        """Test that children reference their parents."""
        chunker = ParentChildChunker()
        content = "This is a test document. " * 100

        metadata = ChunkMetadata(
            source_type="test",
            subject="test",
            grade_level="test",
            board="test",
        )

        chunks = chunker.chunk_document(content, metadata)
        children = [c for c in chunks if c.parent_id is not None]

        for child in children:
            # Parent should exist
            parent = next((c for c in chunks if c.id == child.parent_id), None)
            assert parent is not None or child.parent_id is None

    def test_chunk_video_transcript(self):
        """Test video transcript chunking with timestamps."""
        chunker = ParentChildChunker(child_size=100)

        segments = [
            {"text": "Welcome to the lecture.", "start": 0, "end": 5},
            {"text": "Today we discuss photosynthesis.", "start": 5, "end": 10},
            {"text": "This process converts light to energy.", "start": 10, "end": 15},
        ]

        metadata = ChunkMetadata(
            source_type="video_transcript",
            subject="biology",
            grade_level="class_10",
            board="NCERT",
            video_id="test_video_1",
        )

        chunks = chunker.chunk_video_transcript(segments, metadata)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata.video_id == "test_video_1"
            assert chunk.metadata.start_timestamp is not None

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        chunker = ParentChildChunker()

        assert chunker._format_timestamp(65) == "01:05"
        assert chunker._format_timestamp(3665) == "01:01:05"
        assert chunker._format_timestamp(0) == "00:00"


class TestChunk:
    """Tests for Chunk model."""

    def test_chunk_creation(self):
        """Test basic chunk creation."""
        metadata = ChunkMetadata(
            source_type="textbook",
            subject="biology",
            grade_level="class_10",
            board="NCERT",
        )

        chunk = Chunk(
            content="This is test content.",
            metadata=metadata,
        )

        assert chunk.content == "This is test content."
        assert chunk.id is not None
        assert chunk.char_length == 21
        assert chunk.word_count == 4

    def test_chunk_validation(self):
        """Test that empty content raises error."""
        with pytest.raises(ValueError):
            Chunk(content="")

    def test_chunk_to_dict(self):
        """Test conversion to dictionary."""
        metadata = ChunkMetadata(
            source_type="textbook",
            subject="biology",
            grade_level="class_10",
            board="NCERT",
            chapter="Life Processes",
        )

        chunk = Chunk(
            content="Test content",
            metadata=metadata,
        )

        data = chunk.to_dict()

        assert data["content"] == "Test content"
        assert data["source_type"] == "textbook"
        assert data["subject"] == "biology"
        assert data["chapter"] == "Life Processes"

    def test_chunk_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "test-id",
            "content": "Test content",
            "source_type": "textbook",
            "subject": "biology",
            "grade_level": "class_10",
            "board": "NCERT",
        }

        chunk = Chunk.from_dict(data)

        assert chunk.id == "test-id"
        assert chunk.content == "Test content"
        assert chunk.metadata.subject == "biology"
