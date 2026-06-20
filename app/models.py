from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoInfo(BaseModel):
    video_id: str
    title: str
    duration: int
    thumbnail: str
    uploader: str
    uploader_id: str
    view_count: int
    upload_date: str
    webpage_url: str
    description: Optional[str] = None
    tags: List[str] = []
    categories: List[str] = []


class AudioStream(BaseModel):
    url: str
    format: str
    quality: str
    filesize: Optional[int] = None
    ext: str
    acodec: str
    abr: Optional[int] = None


class SearchResult(BaseModel):
    video_id: str
    title: str
    duration: int
    thumbnail: str
    uploader: str
    view_count: int
    upload_date: str
    url: str


class PlaylistInfo(BaseModel):
    playlist_id: str
    title: str
    uploader: str
    uploader_id: str
    thumbnail: str
    view_count: int
    video_count: int
    entries: List[SearchResult]


class LyricsResponse(BaseModel):
    lyrics: Optional[str]
    source: str


class TrendingResponse(BaseModel):
    category: str
    results: List[SearchResult]


class RelatedResponse(BaseModel):
    video_id: str
    related: List[SearchResult]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    cache_status: str
    extractor_version: str


class APIKeyResponse(BaseModel):
    api_key: str
    created_at: datetime
    requests_made: int
    requests_limit: int
    active: bool


class StatsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    cache_hits: int
    cache_misses: int
    active_api_keys: int
    uptime_seconds: float


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int
