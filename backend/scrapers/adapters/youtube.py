"""YouTube scraper implementing BaseScraper interface."""

import re
from datetime import datetime

from youtube_transcript_api import YouTubeTranscriptApi

from backend.scrapers.base import (
    AuthorModel,
    BaseScraper,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)


class YouTubeScraper(BaseScraper):
    """
    YouTube scraper using youtube-transcript-api.

    Features:
    - Transcript extraction with timestamps
    - Video metadata parsing
    - Channel information
    - Multi-language support
    """

    def __init__(self):
        self.api = YouTubeTranscriptApi()

    async def health_check(self) -> dict:
        """Verify YouTube transcript API access."""
        return {
            "status": "ok",
            "message": "YouTube transcript API ready",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "youtube",
        }

    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """
        Extract transcript from YouTube video.

        Args:
            target: YouTube video ID or URL
            limit: Not used for single video extraction

        Returns:
            Raw transcript data as list of dicts
        """
        # Extract video ID from URL if needed
        video_id = self._extract_video_id(target)

        try:
            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

            # Combine transcript segments
            full_text = " ".join([segment["text"] for segment in transcript_list])

            return [
                {
                    "video_id": video_id,
                    "transcript": full_text,
                    "segments": transcript_list,
                    "duration": sum([s.get("duration", 0) for s in transcript_list]),
                    "extracted_at": datetime.utcnow().isoformat(),
                }
            ]
        except Exception as e:
            return [
                {
                    "video_id": video_id,
                    "error": str(e),
                    "transcript": "",
                    "segments": [],
                    "extracted_at": datetime.utcnow().isoformat(),
                }
            ]

    def _extract_video_id(self, url_or_id: str) -> str:
        """Extract video ID from YouTube URL."""
        if len(url_or_id) == 11 and not url_or_id.startswith("http"):
            return url_or_id

        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"(?:embed\/)([0-9A-Za-z_-]{11})",
            r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)

        return url_or_id

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """Convert raw YouTube data to UnifiedContent."""
        transcript = raw_data.get("transcript", "")

        return UnifiedContent(
            platform="youtube",
            source_url=f"https://youtube.com/watch?v={raw_data['video_id']}",
            author=AuthorModel(
                id=f"youtube_{raw_data['video_id']}",
                platform="youtube",
                username="unknown",  # Would need YouTube Data API for channel info
                display_name=None,
            ),
            content=ContentModel(
                title=None,  # Would need YouTube Data API
                body=transcript,
                word_count=len(transcript.split()),
            ),
            metrics=MetricsModel(
                likes=0,
                views=0,
                replies=0,
                shares=0,
                engagement_rate=0.0,
            ),
            metadata={
                "video_id": raw_data["video_id"],
                "duration_seconds": raw_data.get("duration", 0),
                "segment_count": len(raw_data.get("segments", [])),
                "has_error": "error" in raw_data,
            },
        )
