"""Video segment retrieval for query responses."""

from dataclasses import dataclass
from typing import Optional

import structlog

from src.config import get_settings
from src.chunking.models import Chunk

logger = structlog.get_logger(__name__)


@dataclass
class VideoSegment:
    """A retrievable video segment."""

    video_id: str
    title: str
    instructor: str
    subject: str
    start_time: float
    end_time: float
    start_timestamp: str
    end_timestamp: str
    transcript_excerpt: str
    url: str
    thumbnail_url: str


@dataclass
class VideoSearchResult:
    """Video retrieval result with relevance score."""

    segment: VideoSegment
    relevance_score: float
    matched_text: str


class VideoRetriever:
    """
    Video segment retrieval service.

    Retrieves specific 2-3 minute video segments that answer
    student questions, rather than full 45-minute lectures.
    """

    def __init__(
        self,
        storage_client: Optional[object] = None,
        streaming_service: Optional[object] = None,
    ):
        """
        Initialize video retriever.

        Args:
            storage_client: Azure Blob Storage client for frames
            streaming_service: Video streaming service for segment URLs
        """
        self.settings = get_settings()
        self._storage = storage_client
        self._streaming = streaming_service
        self.buffer_seconds = self.settings.video_segment_buffer_seconds

    def retrieve_segment(
        self,
        chunk: Chunk,
    ) -> Optional[VideoSegment]:
        """
        Retrieve video segment from a matched chunk.

        Args:
            chunk: Matched chunk with video metadata

        Returns:
            VideoSegment if video content available
        """
        if not chunk.metadata.video_id:
            return None

        logger.debug(
            "retrieving_video_segment",
            video_id=chunk.metadata.video_id,
            start=chunk.metadata.start_timestamp,
        )

        # Parse timestamps
        start_seconds = self._parse_timestamp(chunk.metadata.start_timestamp)
        end_seconds = self._parse_timestamp(chunk.metadata.end_timestamp)

        # Add buffer for context
        start_seconds = max(0, start_seconds - self.buffer_seconds)
        end_seconds = end_seconds + self.buffer_seconds

        # Generate segment URL
        segment_url = self._generate_segment_url(
            chunk.metadata.video_id,
            start_seconds,
            end_seconds,
        )

        # Generate thumbnail URL
        thumbnail_url = self._generate_thumbnail_url(
            chunk.metadata.video_id,
            start_seconds,
        )

        return VideoSegment(
            video_id=chunk.metadata.video_id,
            title=chunk.metadata.chapter or "Lecture",
            instructor=chunk.metadata.instructor or "Unknown",
            subject=chunk.metadata.subject,
            start_time=start_seconds,
            end_time=end_seconds,
            start_timestamp=self._format_timestamp(start_seconds),
            end_timestamp=self._format_timestamp(end_seconds),
            transcript_excerpt=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            url=segment_url,
            thumbnail_url=thumbnail_url,
        )

    def retrieve_segments_from_results(
        self,
        chunks: list[Chunk],
        max_segments: int = 3,
    ) -> list[VideoSearchResult]:
        """
        Extract video segments from search results.

        Args:
            chunks: List of matched chunks
            max_segments: Maximum number of video segments to return

        Returns:
            List of video search results
        """
        video_results = []
        seen_videos = set()

        for chunk in chunks:
            if chunk.metadata.video_id and chunk.metadata.video_id not in seen_videos:
                segment = self.retrieve_segment(chunk)
                if segment:
                    video_results.append(
                        VideoSearchResult(
                            segment=segment,
                            relevance_score=0.0,  # Would be set by reranker
                            matched_text=chunk.content,
                        )
                    )
                    seen_videos.add(chunk.metadata.video_id)

                    if len(video_results) >= max_segments:
                        break

        return video_results

    def _generate_segment_url(
        self,
        video_id: str,
        start_seconds: float,
        end_seconds: float,
    ) -> str:
        """
        Generate streaming URL for video segment.

        Args:
            video_id: Video identifier
            start_seconds: Start time
            end_seconds: End time

        Returns:
            Streaming URL for segment
        """
        # In production, this would generate Azure Media Services streaming URL
        # with time range parameters
        start = int(start_seconds)
        end = int(end_seconds)
        return f"https://streaming.example.com/videos/{video_id}?start={start}&end={end}"

    def _generate_thumbnail_url(
        self,
        video_id: str,
        timestamp: float,
    ) -> str:
        """
        Generate thumbnail URL for video at timestamp.

        Args:
            video_id: Video identifier
            timestamp: Time for thumbnail

        Returns:
            URL to thumbnail image
        """
        ts = int(timestamp)
        container = self.settings.azure_storage_container_name
        return f"https://storage.blob.core.windows.net/{container}/frames/{video_id}/{ts}.jpg"

    def _parse_timestamp(self, timestamp: Optional[str]) -> float:
        """
        Parse timestamp string to seconds.

        Args:
            timestamp: Timestamp string (MM:SS or HH:MM:SS)

        Returns:
            Time in seconds
        """
        if not timestamp:
            return 0.0

        parts = timestamp.split(":")
        if len(parts) == 2:
            # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0.0

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS."""
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    async def get_video_metadata(
        self,
        video_id: str,
    ) -> Optional[dict]:
        """
        Retrieve metadata for a video.

        Args:
            video_id: Video identifier

        Returns:
            Video metadata dict if found
        """
        # In production, would query video index/database
        return {
            "video_id": video_id,
            "title": "Mock Video",
            "instructor": "Mock Instructor",
            "duration": 2700,  # 45 minutes
        }

    def format_video_reference(
        self,
        segment: VideoSegment,
    ) -> str:
        """
        Format video reference for response.

        Args:
            segment: Video segment

        Returns:
            Formatted reference string
        """
        return (
            f"📹 **Video: {segment.title}** by {segment.instructor}\n"
            f"Watch segment: {segment.start_timestamp} - {segment.end_timestamp}\n"
            f"[Click to watch]({segment.url})"
        )
