import yt_dlp
import os
import json
import asyncio
import subprocess
from typing import Dict, Any
from backend.models.video import VideoMetadata
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
        return True
    except FileNotFoundError:
        return False

HAS_FFMPEG = check_ffmpeg()
if not HAS_FFMPEG:
    print("WARNING: FFmpeg not found. Audio transcription will be disabled.")

# Using Groq for transcription (Whisper-large-v3)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class VideoService:
    @staticmethod
    async def get_video_info(url: str) -> VideoMetadata:
        print(f"Extracting info for {url}...")
        loop = asyncio.get_event_loop()
        def _get_info():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',
                'noplaylist': True,  # Don't try to fetch playlist info
                'extract_flat': False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        try:
            info = await asyncio.wait_for(loop.run_in_executor(None, _get_info), timeout=20)
        except Exception as e:
            print(f"Error/Timeout extracting info for {url}: {e}")
            # Return minimal metadata instead of failing
            return VideoMetadata(
                video_id=url.split('=')[-1] if '=' in url else "unknown",
                platform='youtube' if 'youtube' in url else 'instagram',
                url=url,
                title="Video (Metadata fetch failed)",
                creator="Unknown",
                engagement_rate=0.0
            )
        
        print(f"Info extracted for {url}")
        
        platform = 'youtube' if 'youtube.com' in url or 'youtu.be' in url else 'instagram'
        
        # Extract metadata
        views = info.get('view_count', 0)
        likes = info.get('like_count', 0)
        comments = info.get('comment_count', 0)
        
        # Engagement Rate = (likes + comments) / views * 100
        engagement_rate = 0.0
        if views and views > 0:
            engagement_rate = ((likes or 0) + (comments or 0)) / views * 100

        return VideoMetadata(
            video_id=info.get('id', 'unknown'),
            platform=platform,
            url=url,
            title=info.get('title'),
            creator=info.get('uploader') or info.get('channel'),
            follower_count=info.get('channel_follower_count', 0),
            views=views,
            likes=likes,
            comments=comments,
            hashtags=info.get('tags', []),
            upload_date=info.get('upload_date'),
            duration=info.get('duration'),
            engagement_rate=round(engagement_rate, 2),
            thumbnail_url=info.get('thumbnail')
        )

    @staticmethod
    async def get_transcript(url: str, video_id: str) -> str:
        print(f"Starting transcript extraction for {url}...")
        loop = asyncio.get_event_loop()
        
        # 1. Try to get native subtitles first (much faster)
        def _get_subtitles():
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en.*', 'en'],
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    # Check for manual subtitles or automatic ones
                    subtitles = info.get('subtitles') or info.get('automatic_captions')
                    if subtitles:
                        # Try to find an English subtitle entry
                        en_subs = None
                        for lang in subtitles.keys():
                            if lang.startswith('en'):
                                en_subs = subtitles[lang]
                                break
                        
                        if en_subs:
                            # Find the json or vtt format
                            for sub in en_subs:
                                if sub.get('ext') == 'json' or sub.get('ext') == 'vtt':
                                    # We can't easily download and parse here without more code
                                    # But we can at least try to use yt-dlp to download it
                                    pass
                except:
                    pass
            return None

        # Actually, the most reliable way to get captions with yt-dlp without audio download
        # is to use the --get-subs option, but that's for CLI.
        # Let's try a different approach: download only the transcript if available.
        
        # 2. Try downloading transcript with yt-dlp
        transcript_file = f"transcript_{video_id}"
        ydl_opts_subs = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'outtmpl': transcript_file,
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            def _download_subs():
                with yt_dlp.YoutubeDL(ydl_opts_subs) as ydl:
                    ydl.download([url])
            
            await asyncio.wait_for(loop.run_in_executor(None, _download_subs), timeout=45)
            
            # Check if any subtitle file was created (.en.vtt or .en.ttml etc)
            for ext in ['.en.vtt', '.en.ttml', '.en.srv1', '.en.srv2', '.en.srv3']:
                possible_file = transcript_file + ext
                if os.path.exists(possible_file):
                    with open(possible_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple VTT parsing (remove timestamps and tags)
                    import re
                    # Remove WEBVTT header and metadata
                    content = re.sub(r'^WEBVTT.*?(\n\n|\r\n\r\n)', '', content, flags=re.DOTALL)
                    # Remove timestamps
                    content = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}.*?\n', '', content)
                    # Remove HTML-like tags
                    content = re.sub(r'<[^>]*>', '', content)
                    # Remove empty lines and join
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    
                    # Cleanup
                    if os.path.exists(possible_file):
                        os.remove(possible_file)
                    
                    if lines:
                        return " ".join(lines)
        except Exception as e:
            print(f"Subtitles extraction failed, falling back to audio: {e}")

        # 3. Fallback: Download audio and use Groq Whisper
        if not HAS_FFMPEG:
            return "Transcript not available (FFmpeg not installed on server). Please provide manual transcript."

        audio_path = f"temp_audio_{video_id}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': f"temp_audio_{video_id}",
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            await loop.run_in_executor(None, _download)
            
            # Transcribe with Groq Whisper
            def _transcribe():
                with open(audio_path, "rb") as audio_file:
                    return client.audio.transcriptions.create(
                        file=(audio_path, audio_file.read()),
                        model="whisper-large-v3",
                        response_format="text",
                    )
            
            transcription = await loop.run_in_executor(None, _transcribe)
            
            # Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return transcription
        except Exception as e:
            print(f"Error transcribing {url}: {str(e)}")
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
            return "Transcript not available."
