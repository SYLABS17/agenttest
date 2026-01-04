"""Azure Video Indexer processor."""

from dataclasses import dataclass
from typing import Optional
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class TranscriptSegment:
    """Video transcript segment with timing."""

    text: str
    start: float
    end: float
    confidence: float = 1.0


class AzureVideoProcessor:
    """Video processing using Azure Video Indexer."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None

    async def process_video(
        self, video_path: str, video_id: str
    ) -> dict:
        """Process video through Azure Video Indexer."""
        logger.info("processing_video_azure", video_id=video_id)

        # Get transcript
        segments = await self._transcribe_video(video_path)

        return {
            "video_id": video_id,
            "segments": segments,
            "duration": segments[-1].end if segments else 0,
        }

    async def _transcribe_video(
        self, video_path: str
    ) -> list[TranscriptSegment]:
        """Transcribe video using Azure Video Indexer."""
        # In production, would call Azure Video Indexer API
        logger.debug("transcribing_with_azure_vi", path=video_path)

        # Mock implementation
        return [
            TranscriptSegment("Welcome to this lecture.", 0.0, 5.0),
            TranscriptSegment("Today we discuss photosynthesis.", 5.0, 10.0),
        ]

    def format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS."""
        seconds = int(seconds)
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
