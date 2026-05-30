from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class VideoMetadata(BaseModel):
    video_id: str
    platform: str  # 'youtube' or 'instagram'
    url: str
    title: Optional[str] = None
    creator: Optional[str] = None
    follower_count: Optional[int] = 0
    views: Optional[int] = 0
    likes: Optional[int] = 0
    comments: Optional[int] = 0
    hashtags: List[str] = []
    upload_date: Optional[str] = None
    duration: Optional[float] = 0.0
    engagement_rate: Optional[float] = 0.0
    thumbnail_url: Optional[str] = None

class VideoProcessingRequest(BaseModel):
    video_a_url: Optional[str] = None
    video_b_url: Optional[str] = None
    video_a_transcript: Optional[str] = None
    video_b_transcript: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: str
