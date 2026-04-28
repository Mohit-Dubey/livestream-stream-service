from fastapi import APIRouter, Depends, BackgroundTasks, Query
from app.db.database import get_db
from app.core.auth import get_current_user_id
from app.schemas.stream import (
    StreamCreate, StreamUpdate, StreamResponse,
    StreamListResponse, MessageResponse, StreamStatus,
)
from app.services import stream_service
from app.services.event_publisher import publish_stream_event

router = APIRouter()


@router.post("/", response_model=StreamResponse, status_code=201)
async def create_stream(
    data: StreamCreate,
    background_tasks: BackgroundTasks,
    owner_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Create a new stream. Returns RTMP ingest URL and HLS/WebRTC playback URLs."""
    stream = await stream_service.create_stream(db, owner_id, data)
    background_tasks.add_task(
        publish_stream_event,
        "stream.created",
        {"stream_id": stream["id"], "owner_id": owner_id, "title": stream["title"]},
    )
    return stream


@router.get("/", response_model=StreamListResponse)
async def list_streams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: StreamStatus | None = None,
    db=Depends(get_db),
):
    """List all streams. Filter by status (created / live / ended)."""
    return await stream_service.list_streams(db, page, page_size, status)


@router.get("/my", response_model=StreamListResponse)
async def list_my_streams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    owner_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List streams owned by the authenticated user."""
    return await stream_service.list_streams(db, page, page_size, owner_id=owner_id)


@router.get("/{stream_id}", response_model=StreamResponse)
async def get_stream(stream_id: str, db=Depends(get_db)):
    """Get stream details including playback URLs."""
    return await stream_service.get_stream(db, stream_id)


@router.put("/{stream_id}", response_model=StreamResponse)
async def update_stream(
    stream_id: str,
    data: StreamUpdate,
    owner_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Update stream metadata (title, description, tags)."""
    return await stream_service.update_stream(db, stream_id, owner_id, data)


@router.post("/{stream_id}/start", response_model=StreamResponse)
async def start_stream(
    stream_id: str,
    background_tasks: BackgroundTasks,
    owner_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Mark stream as LIVE and activate on Ant Media Server."""
    stream = await stream_service.start_stream(db, stream_id, owner_id)
    background_tasks.add_task(
        publish_stream_event,
        "stream.went_live",
        {"stream_id": stream_id, "owner_id": owner_id, "title": stream["title"]},
    )
    return stream


@router.post("/{stream_id}/stop", response_model=StreamResponse)
async def stop_stream(
    stream_id: str,
    background_tasks: BackgroundTasks,
    owner_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Stop a live stream on Ant Media Server and mark as ENDED."""
    stream = await stream_service.stop_stream(db, stream_id, owner_id)
    background_tasks.add_task(
        publish_stream_event,
        "stream.ended",
        {"stream_id": stream_id, "owner_id": owner_id},
    )
    return stream


@router.delete("/{stream_id}", response_model=MessageResponse)
async def delete_stream(
    stream_id: str,
    owner_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Delete a stream (only allowed when not live)."""
    await stream_service.delete_stream(db, stream_id, owner_id)
    return {"message": "Stream deleted successfully"}


@router.get("/{stream_id}/stats")
async def get_stream_stats(stream_id: str, db=Depends(get_db)):
    """Get live viewer count and bitrate stats from Ant Media Server."""
    return await stream_service.get_stream_stats(db, stream_id)
