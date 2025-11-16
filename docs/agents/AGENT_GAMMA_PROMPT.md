# AGENT GAMMA: YouTube Scraper Implementation

## MISSION: Extract Video Intelligence with Dual Transcription Strategy

**Agent ID**: Gamma
**Role**: YouTube Platform Adapter
**Priority**: HIGH (Core platform for thought leader analysis)
**Estimated Time**: 2-3 hours

---

## EXECUTIVE SUMMARY

Build a YouTube scraper that extracts video transcripts and metadata using a two-tier strategy:
1. **Primary**: `youtube-transcript-api` for videos with available captions (fast, free, reliable)
2. **Fallback**: OpenAI Whisper for videos without captions (local transcription, 100% success rate)

This adapter implements the `BaseScraper` interface defined by Agent Beta, normalizing YouTube data into the `UnifiedContent` schema for PostgreSQL storage.

**Key Insight**: Many thought leaders (Dan Koe, Cal Newport, James Clear) post videos with auto-generated captions. Whisper fallback ensures we can analyze ANY video regardless of caption availability.

---

## DEPENDENCIES TO ADD

### Update `backend/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing deps ...

    # YouTube Transcription (Primary - no API key required)
    "youtube-transcript-api>=0.6.0",

    # YouTube Metadata Extraction
    "yt-dlp>=2023.11.0",
    "pytube>=15.0.0",  # Backup for metadata

    # Whisper Fallback (Local Transcription)
    "openai-whisper>=20231117",
    "pydub>=0.25.1",

    # Audio Processing
    "ffmpeg-python>=0.2.0",
]
```

### System Requirements:

```bash
# FFmpeg is REQUIRED for Whisper fallback
# macOS (using Homebrew for system tools is OK per CLAUDE.md)
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

---

## FILES TO CREATE

### Directory Structure
```
backend/
  scrapers/
    adapters/
      youtube.py                    # YouTubeScraper (main adapter)
      _youtube_transcript.py        # Primary: Caption extraction
      _youtube_whisper.py           # Fallback: Whisper transcription
```

---

## STEP 1: Create YouTube Transcript Extractor (Primary)

### File: `backend/scrapers/adapters/_youtube_transcript.py`

```python
"""
YouTube Transcript Extractor
Primary method: Extract captions from YouTube videos
Uses youtube-transcript-api (no API key required)
"""

from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    NoTranscriptAvailable
)


class YouTubeTranscriptExtractor:
    """
    Extract transcripts from YouTube videos using captions API

    Supports:
    - Manual captions (highest quality)
    - Auto-generated captions (good quality)
    - Multiple languages (defaults to English)
    """

    def __init__(self):
        self.formatter = TextFormatter()
        self.preferred_languages = ['en', 'en-US', 'en-GB']

    def extract_transcript(self, video_id: str) -> Optional[dict]:
        """
        Extract transcript from YouTube video

        Args:
            video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ')

        Returns:
            dict: {
                'text': str,           # Full transcript text
                'segments': list,      # Timestamped segments
                'language': str,       # Detected language
                'is_generated': bool,  # Auto-generated vs manual
                'duration': float      # Total duration in seconds
            }

            OR None if no transcript available
        """
        try:
            # Get list of available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to get manual transcript first (highest quality)
            transcript = None
            is_generated = False
            language = 'en'

            try:
                transcript = transcript_list.find_manually_created_transcript(
                    self.preferred_languages
                )
                is_generated = False
                language = transcript.language_code
            except NoTranscriptFound:
                # Fall back to auto-generated
                try:
                    transcript = transcript_list.find_generated_transcript(
                        self.preferred_languages
                    )
                    is_generated = True
                    language = transcript.language_code
                except NoTranscriptFound:
                    # Try any available transcript
                    for t in transcript_list:
                        transcript = t
                        is_generated = t.is_generated
                        language = t.language_code
                        break

            if not transcript:
                return None

            # Fetch the actual transcript data
            segments = transcript.fetch()

            # Format as continuous text
            full_text = self.formatter.format_transcript(segments)

            # Calculate total duration
            if segments:
                last_segment = segments[-1]
                duration = last_segment['start'] + last_segment.get('duration', 0)
            else:
                duration = 0.0

            return {
                'text': full_text,
                'segments': segments,
                'language': language,
                'is_generated': is_generated,
                'duration': duration
            }

        except TranscriptsDisabled:
            print(f"Transcripts disabled for video {video_id}")
            return None
        except VideoUnavailable:
            print(f"Video {video_id} is unavailable")
            return None
        except NoTranscriptAvailable:
            print(f"No transcript available for video {video_id}")
            return None
        except Exception as e:
            print(f"Error extracting transcript for {video_id}: {e}")
            return None

    def get_available_languages(self, video_id: str) -> list[str]:
        """
        Get list of available transcript languages for a video

        Args:
            video_id: YouTube video ID

        Returns:
            list[str]: Language codes (e.g., ['en', 'es', 'fr'])
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            languages = []
            for transcript in transcript_list:
                languages.append(transcript.language_code)
            return languages
        except Exception:
            return []


# Convenience function
def extract_youtube_transcript(video_id: str) -> Optional[dict]:
    """Quick transcript extraction"""
    extractor = YouTubeTranscriptExtractor()
    return extractor.extract_transcript(video_id)


if __name__ == "__main__":
    # Test with a known video (Dan Koe content)
    test_id = "XOmQqBX6Dn4"  # Replace with actual Dan Koe video ID

    extractor = YouTubeTranscriptExtractor()
    result = extractor.extract_transcript(test_id)

    if result:
        print(f"Language: {result['language']}")
        print(f"Auto-generated: {result['is_generated']}")
        print(f"Duration: {result['duration']:.2f} seconds")
        print(f"Transcript preview: {result['text'][:500]}...")
    else:
        print("No transcript available")
```

---

## STEP 2: Create Whisper Fallback Transcriber

### File: `backend/scrapers/adapters/_youtube_whisper.py`

```python
"""
YouTube Whisper Fallback Transcriber
Secondary method: Download audio and transcribe locally with Whisper
Used when youtube-transcript-api fails (no captions available)
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

import whisper
import yt_dlp
from pydub import AudioSegment


class YouTubeWhisperTranscriber:
    """
    Transcribe YouTube videos using OpenAI Whisper

    Fallback for videos without captions. Downloads audio, transcribes locally.

    Requirements:
    - FFmpeg installed (brew install ffmpeg)
    - Sufficient RAM for Whisper model (8GB+ for 'base')
    - GPU optional but recommended for speed
    """

    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper transcriber

        Args:
            model_size: Whisper model size
                - 'tiny': ~1GB VRAM, fastest, least accurate
                - 'base': ~1GB VRAM, good balance (DEFAULT)
                - 'small': ~2GB VRAM, better accuracy
                - 'medium': ~5GB VRAM, high accuracy
                - 'large': ~10GB VRAM, best accuracy
        """
        self.model_size = model_size
        self.model = None
        self._temp_dir = tempfile.mkdtemp(prefix="youtube_whisper_")

    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            print(f"Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size)
            print("Model loaded successfully")

    def _download_audio(self, video_id: str) -> Optional[str]:
        """
        Download audio from YouTube video

        Args:
            video_id: YouTube video ID

        Returns:
            str: Path to downloaded audio file (WAV format)
        """
        output_path = os.path.join(self._temp_dir, f"{video_id}.wav")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self._temp_dir, f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

            # yt-dlp may save with different extension, find the file
            for ext in ['.wav', '.webm', '.m4a', '.mp3']:
                potential_path = os.path.join(self._temp_dir, f"{video_id}{ext}")
                if os.path.exists(potential_path):
                    # Convert to WAV if not already
                    if ext != '.wav':
                        audio = AudioSegment.from_file(potential_path)
                        audio.export(output_path, format="wav")
                        os.remove(potential_path)
                    else:
                        output_path = potential_path
                    break

            if os.path.exists(output_path):
                return output_path
            else:
                print(f"Audio file not found after download for {video_id}")
                return None

        except Exception as e:
            print(f"Error downloading audio for {video_id}: {e}")
            return None

    def transcribe_video(self, video_id: str) -> Optional[dict]:
        """
        Transcribe YouTube video using Whisper

        Args:
            video_id: YouTube video ID

        Returns:
            dict: {
                'text': str,           # Full transcript text
                'segments': list,      # Timestamped segments
                'language': str,       # Detected language
                'is_generated': bool,  # Always True for Whisper
                'duration': float      # Total duration in seconds
            }
        """
        # Load model if needed
        self._load_model()

        # Download audio
        print(f"Downloading audio for video {video_id}...")
        audio_path = self._download_audio(video_id)

        if not audio_path:
            return None

        try:
            # Transcribe with Whisper
            print(f"Transcribing with Whisper {self.model_size} model...")
            result = self.model.transcribe(
                audio_path,
                language="en",  # Force English for consistency
                verbose=False,
                task="transcribe"
            )

            # Format segments to match youtube-transcript-api structure
            segments = []
            for segment in result.get('segments', []):
                segments.append({
                    'start': segment['start'],
                    'duration': segment['end'] - segment['start'],
                    'text': segment['text'].strip()
                })

            # Calculate duration
            if segments:
                last_segment = segments[-1]
                duration = last_segment['start'] + last_segment['duration']
            else:
                duration = 0.0

            return {
                'text': result['text'],
                'segments': segments,
                'language': result.get('language', 'en'),
                'is_generated': True,  # Whisper is always "generated"
                'duration': duration
            }

        except Exception as e:
            print(f"Error transcribing video {video_id}: {e}")
            return None
        finally:
            # Cleanup audio file
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

    def cleanup(self):
        """Clean up temporary directory"""
        import shutil
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()


# Convenience function
def transcribe_youtube_with_whisper(video_id: str, model_size: str = "base") -> Optional[dict]:
    """Quick Whisper transcription"""
    transcriber = YouTubeWhisperTranscriber(model_size)
    result = transcriber.transcribe_video(video_id)
    transcriber.cleanup()
    return result


if __name__ == "__main__":
    # Test with a video that has no captions
    test_id = "example_video_id"  # Replace with actual test

    print("Testing Whisper fallback transcription...")
    result = transcribe_youtube_with_whisper(test_id, model_size="tiny")

    if result:
        print(f"Language: {result['language']}")
        print(f"Duration: {result['duration']:.2f} seconds")
        print(f"Segments: {len(result['segments'])}")
        print(f"Transcript preview: {result['text'][:500]}...")
    else:
        print("Transcription failed")
```

---

## STEP 3: Create Metadata Extractor

### File: `backend/scrapers/adapters/_youtube_metadata.py`

```python
"""
YouTube Metadata Extractor
Extract video metadata: title, channel, views, duration, publish date
"""

from typing import Optional
from datetime import datetime
import yt_dlp


class YouTubeMetadataExtractor:
    """
    Extract metadata from YouTube videos without downloading

    Uses yt-dlp for reliable metadata extraction
    """

    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }

    def extract_metadata(self, video_id: str) -> Optional[dict]:
        """
        Extract metadata for a YouTube video

        Args:
            video_id: YouTube video ID

        Returns:
            dict: {
                'video_id': str,
                'title': str,
                'channel_id': str,
                'channel_name': str,
                'channel_url': str,
                'duration': int,       # seconds
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'published_at': datetime,
                'description': str,
                'tags': list[str],
                'categories': list[str],
                'thumbnail_url': str
            }
        """
        url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Parse upload date
                upload_date_str = info.get('upload_date', '')
                if upload_date_str and len(upload_date_str) == 8:
                    # Format: YYYYMMDD
                    published_at = datetime.strptime(upload_date_str, '%Y%m%d')
                else:
                    published_at = datetime.utcnow()

                return {
                    'video_id': info.get('id', video_id),
                    'title': info.get('title', 'Unknown Title'),
                    'channel_id': info.get('channel_id', ''),
                    'channel_name': info.get('uploader', info.get('channel', 'Unknown Channel')),
                    'channel_url': info.get('channel_url', ''),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'comment_count': info.get('comment_count', 0),
                    'published_at': published_at,
                    'description': info.get('description', ''),
                    'tags': info.get('tags', []),
                    'categories': info.get('categories', []),
                    'thumbnail_url': info.get('thumbnail', '')
                }

        except Exception as e:
            print(f"Error extracting metadata for {video_id}: {e}")
            return None

    def extract_channel_videos(self, channel_url: str, limit: int = 20) -> list[dict]:
        """
        Extract video IDs from a YouTube channel

        Args:
            channel_url: YouTube channel URL
            limit: Maximum videos to extract

        Returns:
            list[dict]: List of video metadata dicts
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': limit,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url + '/videos', download=False)

                videos = []
                if 'entries' in info:
                    for entry in info['entries'][:limit]:
                        if entry and entry.get('id'):
                            videos.append({
                                'video_id': entry.get('id'),
                                'title': entry.get('title', 'Unknown'),
                                'duration': entry.get('duration', 0)
                            })

                return videos

        except Exception as e:
            print(f"Error extracting channel videos: {e}")
            return []


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from various YouTube URL formats

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID

    Args:
        url: YouTube URL

    Returns:
        str: Video ID or None
    """
    import re

    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'  # Just the ID
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


if __name__ == "__main__":
    # Test metadata extraction
    test_id = "XOmQqBX6Dn4"  # Replace with actual video ID

    extractor = YouTubeMetadataExtractor()
    metadata = extractor.extract_metadata(test_id)

    if metadata:
        print(f"Title: {metadata['title']}")
        print(f"Channel: {metadata['channel_name']}")
        print(f"Views: {metadata['view_count']:,}")
        print(f"Duration: {metadata['duration']} seconds")
        print(f"Published: {metadata['published_at']}")
        print(f"Tags: {', '.join(metadata['tags'][:5])}")
    else:
        print("Failed to extract metadata")
```

---

## STEP 4: Create YouTubeScraper Main Adapter

### File: `backend/scrapers/adapters/youtube.py`

```python
"""
YouTube Scraper Adapter
Implements BaseScraper interface with dual transcription strategy:
1. Primary: youtube-transcript-api (fast, free)
2. Fallback: Whisper (local, 100% success rate)
"""

import asyncio
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from ..base import (
    BaseScraper,
    UnifiedContent,
    AuthorModel,
    ContentModel,
    MetricsModel,
    AnalysisModel
)
from ._youtube_transcript import YouTubeTranscriptExtractor
from ._youtube_whisper import YouTubeWhisperTranscriber
from ._youtube_metadata import YouTubeMetadataExtractor, extract_video_id


class YouTubeScraper(BaseScraper):
    """
    YouTube platform adapter with dual transcription strategy

    Features:
    - Primary: Caption extraction (fast, no download)
    - Fallback: Whisper transcription (100% success rate)
    - Full metadata extraction (views, likes, duration)
    - Channel video listing
    - Rate limiting built-in (YouTube is lenient)
    """

    def __init__(self, whisper_model: str = "base"):
        """
        Initialize YouTube scraper

        Args:
            whisper_model: Whisper model size for fallback
                ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.transcript_extractor = YouTubeTranscriptExtractor()
        self.metadata_extractor = YouTubeMetadataExtractor()
        self.whisper_transcriber: Optional[YouTubeWhisperTranscriber] = None
        self.whisper_model_size = whisper_model
        self._whisper_loaded = False

        # Rate limiting (YouTube is lenient, but be respectful)
        self.requests_made = 0
        self.last_request_time = datetime.utcnow()
        self.min_interval_seconds = 1.0  # 1 second between requests

    def _load_whisper_if_needed(self):
        """Lazy load Whisper model only when needed"""
        if not self._whisper_loaded and self.whisper_transcriber is None:
            print(f"Initializing Whisper {self.whisper_model_size} model...")
            self.whisper_transcriber = YouTubeWhisperTranscriber(
                model_size=self.whisper_model_size
            )
            self._whisper_loaded = True

    async def _respect_rate_limit(self):
        """Ensure we don't hammer YouTube"""
        elapsed = (datetime.utcnow() - self.last_request_time).total_seconds()
        if elapsed < self.min_interval_seconds:
            await asyncio.sleep(self.min_interval_seconds - elapsed)
        self.last_request_time = datetime.utcnow()
        self.requests_made += 1

    async def health_check(self) -> dict:
        """
        Check YouTube scraper health status

        Returns:
            dict: Health metrics
        """
        return {
            "status": "healthy",
            "authenticated": True,  # YouTube doesn't require auth for transcripts
            "rate_limit_remaining": -1,  # No strict limit
            "session_age_seconds": 0,
            "last_activity_seconds": (datetime.utcnow() - self.last_request_time).total_seconds(),
            "error_count": 0,
            "requests_made": self.requests_made,
            "whisper_loaded": self._whisper_loaded,
            "whisper_model": self.whisper_model_size,
            "message": "YouTube scraper operational"
        }

    async def extract(self, target: str, limit: int = 20) -> list[dict]:
        """
        Extract video data from YouTube

        Args:
            target: YouTube video URL, video ID, or channel URL
            limit: Maximum number of videos (for channel extraction)

        Returns:
            list[dict]: Raw video data with transcripts and metadata
        """
        await self._respect_rate_limit()

        # Determine if target is a single video or channel
        video_id = extract_video_id(target)

        if video_id:
            # Single video extraction
            video_data = await self._extract_single_video(video_id)
            return [video_data] if video_data else []
        elif 'youtube.com' in target and ('@' in target or '/channel/' in target or '/c/' in target):
            # Channel extraction
            return await self._extract_channel_videos(target, limit)
        else:
            # Assume it's a video ID
            video_data = await self._extract_single_video(target)
            return [video_data] if video_data else []

    async def _extract_single_video(self, video_id: str) -> Optional[dict]:
        """
        Extract transcript and metadata for a single video

        Args:
            video_id: YouTube video ID

        Returns:
            dict: Combined video data or None
        """
        print(f"Extracting video {video_id}...")

        # Get metadata first (always available)
        metadata = self.metadata_extractor.extract_metadata(video_id)
        if not metadata:
            print(f"Failed to extract metadata for {video_id}")
            return None

        # Try primary transcript extraction (caption API)
        print(f"Attempting caption extraction for {video_id}...")
        transcript_data = self.transcript_extractor.extract_transcript(video_id)

        # If no captions, fall back to Whisper
        if not transcript_data:
            print(f"No captions available, falling back to Whisper for {video_id}...")
            self._load_whisper_if_needed()

            if self.whisper_transcriber:
                transcript_data = self.whisper_transcriber.transcribe_video(video_id)

            if not transcript_data:
                print(f"Both transcript methods failed for {video_id}")
                # Return metadata-only entry
                transcript_data = {
                    'text': '',
                    'segments': [],
                    'language': 'en',
                    'is_generated': True,
                    'duration': metadata.get('duration', 0)
                }

        # Combine metadata and transcript
        return {
            'video_id': video_id,
            'metadata': metadata,
            'transcript': transcript_data
        }

    async def _extract_channel_videos(self, channel_url: str, limit: int) -> list[dict]:
        """
        Extract multiple videos from a YouTube channel

        Args:
            channel_url: YouTube channel URL
            limit: Maximum videos to extract

        Returns:
            list[dict]: List of video data dicts
        """
        print(f"Extracting videos from channel: {channel_url}")

        # Get video list from channel
        video_list = self.metadata_extractor.extract_channel_videos(channel_url, limit)

        results = []
        for i, video_info in enumerate(video_list):
            print(f"Processing video {i+1}/{len(video_list)}: {video_info['title'][:50]}...")

            await self._respect_rate_limit()
            video_data = await self._extract_single_video(video_info['video_id'])

            if video_data:
                results.append(video_data)

        return results

    async def normalize(self, raw_data: dict) -> UnifiedContent:
        """
        Normalize YouTube data to UnifiedContent schema

        Args:
            raw_data: Single video data dict from extract()

        Returns:
            UnifiedContent: Normalized content for PostgreSQL
        """
        metadata = raw_data.get('metadata', {})
        transcript = raw_data.get('transcript', {})
        video_id = raw_data.get('video_id', 'unknown')

        # Build author model
        author = AuthorModel(
            id=metadata.get('channel_id', 'unknown'),
            username=metadata.get('channel_name', 'Unknown Channel'),
            display_name=metadata.get('channel_name', 'Unknown Channel'),
            followers_count=0,  # YouTube doesn't expose subscriber count easily
            verified=False,  # Would need additional API call
            profile_url=metadata.get('channel_url', f"https://youtube.com/channel/{metadata.get('channel_id', '')}")
        )

        # Build content model
        content_body = transcript.get('text', '')
        title = metadata.get('title', 'Untitled Video')

        content = ContentModel(
            title=title,
            body=content_body,
            word_count=len(content_body.split()),
            char_count=len(content_body),
            language=transcript.get('language', 'en')
        )

        # Build metrics model
        views = metadata.get('view_count', 0)
        likes = metadata.get('like_count', 0)
        comments = metadata.get('comment_count', 0)

        # YouTube engagement rate calculation
        total_engagement = likes + comments
        engagement_rate = (total_engagement / max(views, 1)) * 100 if views > 0 else 0.0

        metrics = MetricsModel(
            likes=likes,
            shares=0,  # YouTube doesn't expose share count
            comments=comments,
            views=views,
            engagement_rate=round(engagement_rate, 4)
        )

        # Empty analysis (to be filled by LLM later)
        analysis = AnalysisModel()

        # Build unified content
        unified = UnifiedContent(
            content_id=uuid4(),
            platform="youtube",
            source_url=f"https://www.youtube.com/watch?v={video_id}",
            author=author,
            content=content,
            metrics=metrics,
            analysis=analysis,
            embedding=[],  # To be filled by embedding service
            published_at=metadata.get('published_at', datetime.utcnow()),
            scraped_at=datetime.utcnow(),
            metadata={
                'video_id': video_id,
                'duration_seconds': metadata.get('duration', 0),
                'tags': metadata.get('tags', []),
                'categories': metadata.get('categories', []),
                'description': metadata.get('description', ''),
                'thumbnail_url': metadata.get('thumbnail_url', ''),
                'transcript_segments': transcript.get('segments', []),
                'transcript_is_generated': transcript.get('is_generated', True),
                'transcript_language': transcript.get('language', 'en')
            }
        )

        return unified

    async def search_videos(self, query: str, limit: int = 20) -> list[UnifiedContent]:
        """
        Search YouTube for videos matching query (FUTURE FEATURE)

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            list[UnifiedContent]: Normalized search results
        """
        # TODO: Implement YouTube search via yt-dlp
        raise NotImplementedError("YouTube search not yet implemented")

    async def close(self):
        """Clean up resources"""
        if self.whisper_transcriber:
            self.whisper_transcriber.cleanup()
            self.whisper_transcriber = None
            self._whisper_loaded = False
        print("YouTubeScraper resources cleaned up")

    def __del__(self):
        """Cleanup on deletion"""
        if self._whisper_loaded and self.whisper_transcriber:
            self.whisper_transcriber.cleanup()


# Convenience function for quick testing
async def test_youtube_scraper():
    """Test YouTubeScraper with a sample video"""
    scraper = YouTubeScraper(whisper_model="base")

    print("Checking health...")
    health = await scraper.health_check()
    print(f"Health: {health}")

    # Test with Dan Koe video (replace with actual video ID)
    test_video_id = "XOmQqBX6Dn4"

    print(f"\nScraping video: {test_video_id}")
    videos = await scraper.scrape(test_video_id, limit=1)

    if videos:
        video = videos[0]
        print(f"\n--- Video Analysis ---")
        print(f"Platform: {video.platform}")
        print(f"Title: {video.content.title}")
        print(f"Channel: {video.author.username}")
        print(f"Views: {video.metrics.views:,}")
        print(f"Likes: {video.metrics.likes:,}")
        print(f"Duration: {video.metadata.get('duration_seconds', 0)} seconds")
        print(f"Transcript length: {video.content.word_count} words")
        print(f"Transcript preview: {video.content.body[:300]}...")
        print(f"URL: {video.source_url}")
    else:
        print("Failed to scrape video")

    await scraper.close()
    return videos


if __name__ == "__main__":
    asyncio.run(test_youtube_scraper())
```

---

## STEP 5: Update Package Exports

### Update `backend/scrapers/adapters/__init__.py`:

```python
"""
Platform-specific scraper adapters
Each adapter implements the BaseScraper interface
"""

from .twitter import TwitterScraper
from .youtube import YouTubeScraper

__all__ = ["TwitterScraper", "YouTubeScraper"]
```

### Update `backend/scrapers/__init__.py`:

```python
"""
Unified Scraper - Platform Scrapers
Multi-platform content intelligence engine
"""

from .base import BaseScraper, UnifiedContent
from .adapters.twitter import TwitterScraper
from .adapters.youtube import YouTubeScraper

__all__ = ["BaseScraper", "UnifiedContent", "TwitterScraper", "YouTubeScraper"]
```

---

## ERROR HANDLING PATTERNS

### Transcript Extraction Errors

```python
# youtube-transcript-api specific errors
from youtube_transcript_api._errors import (
    TranscriptsDisabled,      # Video has transcripts disabled
    NoTranscriptFound,        # No transcript in requested language
    VideoUnavailable,         # Video deleted or private
    NoTranscriptAvailable     # No transcripts at all
)

# Handle gracefully
try:
    transcript = extractor.extract_transcript(video_id)
except TranscriptsDisabled:
    # Fall back to Whisper
    transcript = whisper_transcriber.transcribe_video(video_id)
except VideoUnavailable:
    # Log and skip this video
    print(f"Video {video_id} is unavailable (private/deleted)")
    return None
```

### Whisper Fallback Errors

```python
# Whisper-specific errors
try:
    result = whisper_model.transcribe(audio_path)
except RuntimeError as e:
    if "CUDA out of memory" in str(e):
        # Suggest smaller model
        print("GPU memory exceeded. Try 'tiny' or 'base' model.")
    raise
except FileNotFoundError:
    # FFmpeg not installed
    print("FFmpeg not found. Install with: brew install ffmpeg")
    raise
```

### yt-dlp Download Errors

```python
try:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url)
except yt_dlp.utils.DownloadError as e:
    if "Video unavailable" in str(e):
        return None
    elif "Sign in to confirm" in str(e):
        print("Video requires age verification")
        return None
    raise
```

---

## RATE LIMITING STRATEGY

YouTube is **lenient** compared to Twitter, but still be respectful:

```python
class YouTubeRateLimiter:
    """
    Rate limiting for YouTube API

    YouTube limits:
    - No strict API rate limits for transcript fetching
    - yt-dlp: Respect robots.txt
    - Whisper: CPU/GPU bound, not network bound

    Best practices:
    - 1 second minimum between requests
    - 60 requests per minute max
    - 1000 requests per hour max (self-imposed)
    """

    def __init__(self):
        self.requests_per_minute = 0
        self.requests_per_hour = 0
        self.last_minute_reset = datetime.utcnow()
        self.last_hour_reset = datetime.utcnow()
        self.min_interval = 1.0  # seconds

    async def wait_if_needed(self):
        now = datetime.utcnow()

        # Reset minute counter
        if (now - self.last_minute_reset).seconds >= 60:
            self.requests_per_minute = 0
            self.last_minute_reset = now

        # Reset hour counter
        if (now - self.last_hour_reset).seconds >= 3600:
            self.requests_per_hour = 0
            self.last_hour_reset = now

        # Check limits
        if self.requests_per_minute >= 60:
            wait_time = 60 - (now - self.last_minute_reset).seconds
            print(f"Minute rate limit reached, waiting {wait_time}s...")
            await asyncio.sleep(wait_time)

        if self.requests_per_hour >= 1000:
            wait_time = 3600 - (now - self.last_hour_reset).seconds
            print(f"Hour rate limit reached, waiting {wait_time}s...")
            await asyncio.sleep(wait_time)

        # Increment counters
        self.requests_per_minute += 1
        self.requests_per_hour += 1
```

---

## SUCCESS CRITERIA

### Functional Requirements
- [ ] Initialize YouTubeScraper without errors
- [ ] Extract transcript from video WITH captions (primary method)
- [ ] Extract transcript from video WITHOUT captions (Whisper fallback)
- [ ] Extract metadata: title, channel, views, duration, published_at
- [ ] Handle multiple YouTube URL formats
- [ ] List videos from a channel
- [ ] All data normalized to UnifiedContent schema
- [ ] Health check returns accurate status

### Integration Requirements
- [ ] YouTubeScraper implements BaseScraper ABC
- [ ] `health_check()` returns proper dict structure
- [ ] `extract()` returns list of raw video data
- [ ] `normalize()` returns UnifiedContent Pydantic model
- [ ] `scrape()` combines extract + normalize correctly

### Data Quality
- [ ] Video titles extracted accurately
- [ ] Transcripts complete (not truncated)
- [ ] Engagement metrics captured (views, likes, comments)
- [ ] Timestamps parsed correctly (ISO format)
- [ ] Channel info preserved
- [ ] Tags and categories captured
- [ ] Duration in seconds

### Testing Commands

```bash
# Install dependencies
cd backend
uv pip install youtube-transcript-api yt-dlp openai-whisper pydub ffmpeg-python

# Test basic import
python -c "from backend.scrapers.adapters.youtube import YouTubeScraper; print('Import OK')"

# Test video with captions (Dan Koe)
python -c "
import asyncio
from backend.scrapers.adapters.youtube import test_youtube_scraper
asyncio.run(test_youtube_scraper())
"

# Test transcript extraction only
python -c "
from backend.scrapers.adapters._youtube_transcript import extract_youtube_transcript
result = extract_youtube_transcript('XOmQqBX6Dn4')
if result:
    print(f'Words: {len(result[\"text\"].split())}')
    print(f'Preview: {result[\"text\"][:200]}')
else:
    print('No transcript')
"

# Test metadata extraction
python -c "
from backend.scrapers.adapters._youtube_metadata import YouTubeMetadataExtractor
extractor = YouTubeMetadataExtractor()
meta = extractor.extract_metadata('XOmQqBX6Dn4')
if meta:
    print(f'Title: {meta[\"title\"]}')
    print(f'Views: {meta[\"view_count\"]:,}')
"

# Test Whisper fallback (only if caption extraction fails)
python -c "
from backend.scrapers.adapters._youtube_whisper import transcribe_youtube_with_whisper
# Use a video known to have no captions
result = transcribe_youtube_with_whisper('VIDEO_ID_NO_CAPTIONS', model_size='tiny')
if result:
    print(f'Transcribed: {len(result[\"text\"])} characters')
"

# Health check
python -c "
import asyncio
from backend.scrapers.adapters.youtube import YouTubeScraper
async def check():
    s = YouTubeScraper()
    print(await s.health_check())
asyncio.run(check())
"
```

---

## CRITICAL WARNINGS

1. **ALWAYS TRY CAPTION API FIRST**: Whisper is CPU-intensive. Only use as fallback.

2. **WHISPER MODEL SIZE MATTERS**:
   - `tiny`: 1GB RAM, fastest, okay accuracy
   - `base`: 1GB RAM, good balance (RECOMMENDED)
   - `small`: 2GB RAM, better accuracy
   - Larger models require GPU for reasonable speed

3. **FFMPEG IS REQUIRED**: Whisper fallback will fail without FFmpeg installed.

4. **RESPECT YOUTUBE TOS**:
   - Don't scrape too aggressively
   - 1 second minimum between requests
   - Don't circumvent age/geo restrictions

5. **HANDLE UNAVAILABLE VIDEOS**: Videos can be:
   - Private
   - Deleted
   - Age-restricted
   - Geo-blocked

6. **TRANSCRIPT QUALITY VARIES**:
   - Manual captions: Best quality
   - Auto-generated: Good quality, may have errors
   - Whisper: Depends on audio quality

7. **CLEAN UP TEMP FILES**: Whisper downloads audio files. Always clean up.

---

## ESTIMATED EFFORT

| Task | Time |
|------|------|
| Create directory structure | 5 min |
| Write _youtube_transcript.py | 30 min |
| Write _youtube_whisper.py | 45 min |
| Write _youtube_metadata.py | 30 min |
| Write YouTubeScraper wrapper | 60 min |
| Update package exports | 10 min |
| Install dependencies | 15 min |
| Test caption extraction | 15 min |
| Test Whisper fallback | 20 min |
| Test metadata extraction | 15 min |
| Verify data quality | 15 min |

**Total: 2-3 hours**

---

## NEXT AGENT (Delta)

Once YouTubeScraper is operational:
- Agent Delta: Reddit Scraper (PRAW integration)
- Agent Epsilon: Web Scraper (Jina.ai + ScraperAPI)

---

## SUPPORT CONTACTS

- **Project Lead**: @iamcodio (GitHub)
- **Architecture Docs**: `/Users/kjd/01-projects/IAC-032-unified-scraper/CLAUDE.md`
- **Whisper Reference**: `/Users/kjd/yt-agent-app/youtube-ai-analyzer-prd.md`

---

**Remember**: YouTube is MORE forgiving than Twitter. No complex anti-detection needed. Focus on dual transcription strategy and clean data extraction.

Good luck, Agent Gamma.
