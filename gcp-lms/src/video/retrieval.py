"""Video segment retrieval for GCP."""

from dataclasses import dataclass
from typing import Optional
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class VideoSegment:
    """A retrievable video segment."""

    video_id: str
    title: str
    instructor: str
    start_timestamp: str
    end_timestamp: str
    url: str
    thumbnail_url: str


class VideoRetriever:
    """Video segment retrieval service using Cloud Storage."""

    def __init__(self):
        self.settings = get_settings()

    def retrieve_segments_from_results(
        self, chunks: list, max_segments: int = 3
    ) -> list:
        """Extract video segments from search results."""
        video_results = []
        seen_videos = set()

        for chunk in chunks:
            metadata = getattr(chunk, 'metadata', {})
            if isinstance(metadata, dict):
                video_id = metadata.get('video_id')
            else:
                video_id = getattr(metadata, 'video_id', None)

            if video_id and video_id not in seen_videos:
                segment = VideoSegment(
                    video_id=video_id,
                    title=metadata.get('chapter', 'Lecture') if isinstance(metadata, dict) else getattr(metadata, 'chapter', 'Lecture'),
                    instructor="Instructor",
                    start_timestamp=metadata.get('start_timestamp', '00:00') if isinstance(metadata, dict) else getattr(metadata, 'start_timestamp', '00:00'),
                    end_timestamp=metadata.get('end_timestamp', '00:00') if isinstance(metadata, dict) else getattr(metadata, 'end_timestamp', '00:00'),
                    url=f"https://storage.googleapis.com/{self.settings.gcs_bucket_name}/videos/{video_id}",
                    thumbnail_url=f"https://storage.googleapis.com/{self.settings.gcs_bucket_name}/{self.settings.gcs_frames_prefix}{video_id}/thumb.jpg",
                )
                video_results.append(segment)
                seen_videos.add(video_id)

                if len(video_results) >= max_segments:
                    break

        return video_results
