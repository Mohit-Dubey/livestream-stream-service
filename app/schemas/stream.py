from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class StreamStatus(str, Enum):
    CREATED = "created"
    LIVE = "live"
    ENDED = "ended"
    ERROR = "error"


class StreamCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = []


class StreamUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None


class StreamResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    category: Optional[str]
    tags: list[str]
    status: StreamStatus
    stream_key: str
    rtmp_url: Optional[str]
    hls_url: Optional[str]
    webrtc_url: Optional[str]
    viewer_count: int
    owner_id: str
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]


class StreamListResponse(BaseModel):
    streams: list[StreamResponse]
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    message: str
