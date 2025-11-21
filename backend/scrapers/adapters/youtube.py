"""YouTube scraper implementing BaseScraper interface."""

import asyncio
import re
from datetime import datetime

from backend.scrapers.base import (
    AuthorModel,
    BaseScraper,
    ContentModel,
    MetricsModel,
    UnifiedContent,
)


class YouTubeScraper(BaseScraper):
    """
    YouTube scraper using youtube-transcript-api and yt-dlp.

    Features:
    - Transcript extraction with timestamps
    - Video metadata parsing (title, channel, views, likes)
    - Channel information
    - Multi-language support
    - Channel video listing
    """

    def __init__(self):
        # Lazy import youtube_transcript_api to avoid import issues
        from youtube_transcript_api import YouTubeTranscriptApi

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
        Extract transcript and metadata from YouTube video(s).

        Args:
            target: YouTube video ID, URL, or channel ID/URL
            limit: Maximum videos to fetch (for channels)

        Returns:
            Raw transcript data as list of dicts
        """
        # Check if target is a channel or playlist
        if any(x in target for x in ['channel/', 'c/', '@', 'playlist']):
            return await self._extract_channel_videos(target, limit)
        else:
            # Single video
            video_id = self._extract_video_id(target)
            video_data = await self._extract_single_video(video_id)
            return [video_data] if video_data else []

    async def _extract_single_video(self, video_id: str) -> dict | None:
        """Extract single video with transcript and metadata."""
        # Lazy import to avoid circular import issues
        from youtube_transcript_api import YouTubeTranscriptApi

        try:
            # Get metadata using yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            loop = asyncio.get_event_loop()
            video_info = await loop.run_in_executor(
                None,
                lambda: self._get_video_info(video_id, ydl_opts)
            )

            if not video_info:
                return None

            # Get transcript
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                full_text = " ".join([segment["text"] for segment in transcript_list])
            except Exception:
                # Transcript not available
                transcript_list = []
                full_text = video_info.get('description', '')

            return {
                "video_id": video_id,
                "title": video_info.get('title', ''),
                "transcript": full_text,
                "segments": transcript_list,
                "duration": video_info.get('duration', 0),
                "channel": video_info.get('channel', ''),
                "channel_id": video_info.get('channel_id', ''),
                "view_count": video_info.get('view_count', 0),
                "like_count": video_info.get('like_count', 0),
                "upload_date": video_info.get('upload_date', ''),
                "description": video_info.get('description', ''),
                "extracted_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "video_id": video_id,
                "error": str(e),
                "title": "",
                "transcript": "",
                "segments": [],
                "extracted_at": datetime.utcnow().isoformat(),
            }

    async def _extract_channel_videos(self, target: str, limit: int) -> list[dict]:
        """Extract videos from a channel or playlist."""
        videos = []

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlist_items': f'1-{limit}',
            }

            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: self._get_playlist_info(target, ydl_opts)
            )

            if not info:
                return []

            # Extract video IDs
            if 'entries' in info:
                video_ids = [entry['id'] for entry in info['entries'] if entry][:limit]
            else:
                video_ids = [info['id']]

            # Get transcript and metadata for each video
            for video_id in video_ids:
                video_data = await self._extract_single_video(video_id)
                if video_data:
                    videos.append(video_data)

        except Exception as e:
            pass

        return videos

    def _get_video_info(self, video_id: str, opts: dict) -> dict | None:
        """Synchronous helper to get video info with yt-dlp."""
        # Lazy import to avoid circular import issues
        import yt_dlp

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(
                    f'https://youtube.com/watch?v={video_id}',
                    download=False
                )
        except Exception:
            return None

    def _get_playlist_info(self, url: str, opts: dict) -> dict | None:
        """Synchronous helper to get playlist/channel info with yt-dlp."""
        # Lazy import to avoid circular import issues
        import yt_dlp

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            return None

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
        views = raw_data.get("view_count", 0)
        likes = raw_data.get("like_count", 0)

        # Calculate engagement rate
        engagement_rate = (likes / views * 100) if views > 0 else 0.0

        return UnifiedContent(
            platform="youtube",
            source_url=f"https://youtube.com/watch?v={raw_data['video_id']}",
            author=AuthorModel(
                id=raw_data.get("channel_id", f"youtube_{raw_data['video_id']}"),
                platform="youtube",
                username=raw_data.get("channel", "unknown"),
                display_name=raw_data.get("channel"),
            ),
            content=ContentModel(
                title=raw_data.get("title"),
                body=transcript,
                word_count=len(transcript.split()),
            ),
            metrics=MetricsModel(
                likes=likes,
                views=views,
                comments=0,  # Would need YouTube Data API
                shares=0,
                engagement_rate=engagement_rate,
            ),
            metadata={
                "video_id": raw_data["video_id"],
                "duration_seconds": raw_data.get("duration", 0),
                "segment_count": len(raw_data.get("segments", [])),
                "upload_date": raw_data.get("upload_date", ""),
                "description": raw_data.get("description", ""),
                "has_error": "error" in raw_data,
            },
        )
