# YouTube AI Video Analyzer - Product Requirements Document

## Executive Summary

The YouTube AI Video Analyzer is a Python-based tool that automatically downloads, transcribes, and analyzes YouTube videos to extract key insights, methodologies, and actionable information. It processes videos at accelerated speeds and produces structured markdown reports focusing on core concepts while filtering out filler content.

## Problem Statement

Modern learners waste significant time watching lengthy YouTube videos filled with repetitive content, tangential discussions, and filler material. Current Chrome-based transcription plugins only provide basic auto-generated transcripts without intelligent analysis or insight extraction. There's a need for a tool that can:

- Process videos at accelerated speeds (2-3x)
- Extract core concepts and methodologies
- Filter out redundant information
- Provide structured, actionable summaries
- Support modern AI-assisted learning workflows

## Solution Overview

A desktop application that combines audio extraction, AI transcription, and intelligent content analysis to transform lengthy YouTube videos into concise, structured knowledge documents.

## Technical Architecture

### Core Components

1. **Audio Extraction Layer**
   - YouTube-DL for direct video/audio download
   - PyDub for audio speed manipulation
   - Alternative: OBS integration for live capture

2. **Transcription Engine**
   - OpenAI Whisper for accurate speech-to-text
   - Support for multiple model sizes (base, small, medium)
   - Handles accelerated audio without quality loss

3. **AI Analysis Pipeline**
   - Claude 3.5 Sonnet for comprehensive analysis
   - GPT-4 as fallback option
   - Structured prompt engineering for consistent output

4. **Output Generation**
   - Markdown formatting with clear sections
   - Hierarchical information structure
   - Collapsible full transcript sections

### System Requirements

- **Operating Systems**: macOS, Ubuntu Linux, Windows 10+
- **Python Version**: 3.8 or higher
- **RAM**: Minimum 8GB (16GB recommended for larger Whisper models)
- **Storage**: 2GB for models + video cache
- **GPU**: Optional but recommended for faster Whisper processing

## Installation Instructions

### Prerequisites

1. **Install Python 3.8+**
   ```bash
   # macOS
   brew install python@3.9

   # Ubuntu
   sudo apt update
   sudo apt install python3.9 python3-pip

   # Windows
   # Download from python.org
   ```

2. **Install FFmpeg** (required for audio processing)
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu
   sudo apt install ffmpeg

   # Windows
   # Download from ffmpeg.org and add to PATH
   ```

### Package Installation

```bash
# Create virtual environment
python -m venv youtube_analyzer_env
source youtube_analyzer_env/bin/activate  # On Windows: youtube_analyzer_env\Scripts\activate

# Install required packages
pip install yt-dlp==2023.11.16
pip install openai-whisper==20231117
pip install anthropic==0.8.0
pip install openai==1.6.1
pip install pydub==0.25.1
pip install sounddevice==0.4.6
pip install rich==13.7.0
pip install numpy==1.24.3
pip install scipy==1.11.4
```

### API Key Configuration

```bash
# Option 1: Environment variables (recommended)
export ANTHROPIC_API_KEY="sk-ant-..."  # Get from console.anthropic.com
export OPENAI_API_KEY="sk-..."         # Get from platform.openai.com

# Option 2: Create .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

## Usage Guide

### Basic Usage

1. **Start the application**
   ```bash
   python youtube_ai_analyzer.py
   ```

2. **Analyze a YouTube video**
   - Select option 1
   - Paste YouTube URL (e.g., `https://youtube.com/watch?v=...`)
   - Choose playback speed (1.0-3.0x, default 2.0x)
   - Wait for processing
   - Find output in `youtube_analyses/` directory

3. **OBS Capture Mode** (Alternative)
   - Set up OBS with browser source
   - Configure audio routing to virtual cable
   - Select option 2 in the app
   - Choose the virtual audio device
   - Press Enter to start/stop recording

### Output Structure

Generated markdown files include:

```markdown
# 📹 Video Analysis: [Video Title]

**URL:** [YouTube URL]
**Duration:** [MM:SS]
**Analyzed:** [Timestamp]

## 🎯 Core Thesis
The main argument in 2-3 sentences

## 🌳 Narrative Structure
How the video progresses from start to finish

## 🌿 Key Branches
- Branch 1: [Topic] - [Significance]
- Branch 2: [Topic] - [Significance]

## 💡 Original Methodologies/Philosophies
- Unique approaches and frameworks

## 🔑 Key Actionable Insights
1. Specific implementable actions
2. Expected outcomes

## 📊 Notable Data/Examples
Important statistics and case studies

## 🚀 Implementation Roadmap
Suggested order of applying ideas

## ❌ What Was Discarded
Types of filtered content (filler, repetition)

## 📝 Full Transcript
<details>
<summary>Click to expand</summary>
[Complete transcript]
</details>
```

## Core Source Code

```python
#!/usr/bin/env python3
"""
YouTube AI Video Analyzer
Watches videos at high speed, extracts transcripts, and creates structured markdown notes
focusing on key concepts, methodologies, and narrative structure.
"""

import os
import sys
import time
import json
import queue
import threading
import subprocess
from datetime import datetime
from pathlib import Path

import yt_dlp
import whisper
import numpy as np
import sounddevice as sd
from pydub import AudioSegment
import anthropic
import openai
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class YouTubeAIAnalyzer:
    def __init__(self, anthropic_key=None, openai_key=None):
        self.anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize AI clients
        if self.anthropic_key:
            self.claude = anthropic.Anthropic(api_key=self.anthropic_key)
        if self.openai_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_key)
            
        # Load Whisper model
        console.print("[yellow]Loading Whisper model...[/yellow]")
        self.whisper_model = whisper.load_model("base")
        
        # Output directory
        self.output_dir = Path("youtube_analyses")
        self.output_dir.mkdir(exist_ok=True)
        
    def download_audio(self, youtube_url, speed=2.0):
        """Download audio from YouTube and optionally speed it up"""
        console.print(f"[cyan]Downloading audio from: {youtube_url}[/cyan]")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': 'temp_audio.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_title = info.get('title', 'Unknown')
            video_id = info.get('id', 'unknown')
            duration = info.get('duration', 0)
            
        # Speed up audio if requested
        if speed > 1.0:
            console.print(f"[yellow]Speeding up audio by {speed}x...[/yellow]")
            audio = AudioSegment.from_wav("temp_audio.wav")
            
            # Speed up without changing pitch too much
            speeded = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed)
            }).set_frame_rate(audio.frame_rate)
            
            speeded.export("temp_audio_fast.wav", format="wav")
            os.rename("temp_audio_fast.wav", "temp_audio.wav")
            
        return {
            'title': video_title,
            'id': video_id,
            'duration': duration,
            'url': youtube_url
        }
        
    def transcribe_audio(self, audio_path="temp_audio.wav"):
        """Transcribe audio using Whisper"""
        console.print("[cyan]Transcribing audio with Whisper...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Transcribing...", total=None)
            
            result = self.whisper_model.transcribe(
                audio_path,
                language="en",
                verbose=False
            )
            
            progress.update(task, completed=True)
            
        return result
        
    def extract_key_insights(self, transcript, video_info):
        """Use Claude to extract structured insights"""
        console.print("[cyan]Analyzing content with AI...[/cyan]")
        
        prompt = f"""Analyze this video transcript and create a structured summary focusing on extracting the core value while discarding filler content.

Video Title: {video_info['title']}
Duration: {video_info['duration'] // 60} minutes

TRANSCRIPT:
{transcript}

Please provide a comprehensive analysis in the following structure:

## 🎯 Core Thesis
(The main argument or central idea in 2-3 sentences)

## 🌳 Narrative Structure
(The main narrative trunk - how the video progresses from start to finish, major sections)

## 🌿 Key Branches
(Important sub-topics that branch off from the main narrative - list 3-5 major ones)
- Branch 1: [Topic] - [Why it matters]
- Branch 2: [Topic] - [Why it matters]
etc.

## 💡 Original Methodologies/Philosophies
(Any unique approaches, frameworks, or thinking patterns presented)
- Methodology 1: [Name/Description] - [How it works]
- Methodology 2: [Name/Description] - [How it works]

## 🔑 Key Actionable Insights
(Specific things you can implement or act upon)
1. [Specific action] - [Expected outcome]
2. [Specific action] - [Expected outcome]
etc.

## 📊 Notable Data/Examples
(Important statistics, case studies, or examples worth remembering)

## 🚀 Implementation Roadmap
(If applicable, suggested order of implementing the ideas)

## ❌ What Was Discarded
(Brief note on what type of content was filtered out as "leaves" - filler, repetition, etc.)

Focus on extracting maximum value in minimum reading time. Be concise but comprehensive."""

        try:
            if self.claude:
                response = self.claude.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4000
                )
                return response.choices[0].message.content
            else:
                return self.basic_extraction(transcript)
        except Exception as e:
            console.print(f"[red]AI analysis failed: {e}[/red]")
            return self.basic_extraction(transcript)
            
    def basic_extraction(self, transcript):
        """Fallback basic extraction without AI"""
        return f"""## Video Summary

### Transcript
{transcript}

### Note
AI analysis was not available. Above is the raw transcript.
To enable AI analysis, set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.
"""

    def create_markdown_report(self, video_info, transcript_data, analysis):
        """Create a comprehensive markdown report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        report = f"""# 📹 Video Analysis: {video_info['title']}

**URL:** {video_info['url']}  
**Video ID:** {video_info['id']}  
**Duration:** {video_info['duration'] // 60}:{video_info['duration'] % 60:02d}  
**Analyzed:** {timestamp}  

---

{analysis}

---

## 📝 Full Transcript

<details>
<summary>Click to expand full transcript</summary>

{transcript_data['text']}

</details>

---

*Generated by YouTube AI Analyzer*
"""
        
        # Save to file
        safe_title = "".join(c for c in video_info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{video_info['id']}_{safe_title[:50]}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
            
        return filepath
        
    def analyze_youtube_video(self, youtube_url, speed=2.0):
        """Main pipeline to analyze a YouTube video"""
        try:
            # Download audio
            video_info = self.download_audio(youtube_url, speed)
            
            # Transcribe
            transcript_data = self.transcribe_audio()
            
            # Extract insights
            analysis = self.extract_key_insights(transcript_data['text'], video_info)
            
            # Create report
            report_path = self.create_markdown_report(video_info, transcript_data, analysis)
            
            # Cleanup
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")
                
            console.print(f"\n[green]✅ Analysis complete![/green]")
            console.print(f"[green]📄 Report saved to: {report_path}[/green]")
            
            return report_path
            
        except Exception as e:
            console.print(f"[red]Error analyzing video: {e}[/red]")
            raise

def main():
    console.print("[bold cyan]YouTube AI Video Analyzer[/bold cyan]")
    console.print("Extract key insights from YouTube videos at high speed\n")
    
    analyzer = YouTubeAIAnalyzer()
    
    while True:
        console.print("\n[yellow]Options:[/yellow]")
        console.print("1. Analyze YouTube URL")
        console.print("2. Exit")
        
        choice = input("\nSelect option (1-2): ")
        
        if choice == "1":
            url = input("Enter YouTube URL: ")
            speed = float(input("Playback speed (1.0-3.0, default 2.0): ") or "2.0")
            
            try:
                analyzer.analyze_youtube_video(url, speed)
            except Exception as e:
                console.print(f"[red]Failed: {e}[/red]")
                
        elif choice == "2":
            console.print("[green]Goodbye![/green]")
            break
            
        else:
            console.print("[red]Invalid option[/red]")

if __name__ == "__main__":
    main()
```

## Configuration Options

### Whisper Model Selection

Modify the model size based on your needs:

```python
# In __init__ method
self.whisper_model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
```

- **tiny**: Fastest, least accurate (1GB)
- **base**: Good balance (1GB)
- **small**: Better accuracy (2GB)
- **medium**: High accuracy (5GB)
- **large**: Best accuracy (10GB)

### Speed Settings

Default is 2.0x, but can be adjusted:
- **1.5x**: For dense technical content
- **2.0x**: Optimal for most content
- **2.5x**: For slow speakers
- **3.0x**: Maximum recommended speed

### AI Model Selection

Configure in environment or code:
```python
# Priority: Claude > GPT-4 > Fallback
# Claude typically provides better structured analysis
# GPT-4 works well as alternative
```

## Advanced Features

### Batch Processing

Add this method to process multiple videos:

```python
def batch_analyze(self, urls_file, speed=2.0):
    """Process multiple YouTube URLs from a file"""
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    results = []
    for i, url in enumerate(urls, 1):
        console.print(f"\n[cyan]Processing video {i}/{len(urls)}[/cyan]")
        try:
            result = self.analyze_youtube_video(url, speed)
            results.append((url, result))
        except Exception as e:
            console.print(f"[red]Failed to process {url}: {e}[/red]")
            results.append((url, None))
    
    return results
```

### Custom Analysis Templates

Create specialized prompts for different content types:

```python
CODING_TUTORIAL_PROMPT = """
Focus on:
- Code patterns and best practices
- Technologies and libraries used
- Step-by-step implementation guide
- Common pitfalls mentioned
"""

PHILOSOPHY_LECTURE_PROMPT = """
Focus on:
- Core philosophical arguments
- Historical context
- Practical applications
- Critiques and counterarguments
"""
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Ensure FFmpeg is installed and in PATH
   - Test with: `ffmpeg -version`

2. **Whisper model download fails**
   - Check internet connection
   - Manually download models to `~/.cache/whisper/`

3. **API key errors**
   - Verify keys are correctly set
   - Check API rate limits

4. **Memory issues with large videos**
   - Use smaller Whisper models
   - Process in chunks for very long videos

### Performance Optimization

1. **GPU Acceleration**
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Concurrent Processing**
   - Use threading for download/transcription pipeline
   - Implement queue system for batch processing

## Future Enhancements

1. **Web Interface**
   - Flask/FastAPI web UI
   - Real-time progress updates
   - Search and filter saved analyses

2. **Additional Integrations**
   - Notion export
   - Obsidian vault integration
   - Email summaries

3. **Enhanced Analysis**
   - Sentiment analysis
   - Speaker diarization
   - Visual content description (for presentations)

## Security Considerations

1. **API Key Management**
   - Never commit keys to version control
   - Use environment variables or secure key management
   - Rotate keys regularly

2. **Content Validation**
   - Verify YouTube URLs before processing
   - Implement rate limiting for API calls
   - Sanitize file names for output

## License and Attribution

This tool is provided as-is for educational and personal use. Ensure compliance with:
- YouTube's Terms of Service
- OpenAI, Anthropic usage policies
- Content creator rights

---

*Last Updated: June 2025*