import uuid
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.schemas.stream import StreamCreate, StreamUpdate, StreamStatus
from app.services import ant_media_client as ams

logger = logging.getLogger(__name__)
COLLECTION = "streams"


async def create_stream(db: AsyncIOMotorDatabase, owner_id: str, data: StreamCreate) -> dict:
    stream_id = str(uuid.uuid4())
    stream_key = str(uuid.uuid4()).replace("-", "")[:24]

    # Register broadcast on Ant Media Server
    try:
        await ams.create_broadcast(stream_id, data.title)
    except Exception as exc:
        logger.warning(f"AMS create_broadcast failed: {exc}")

    doc = {
        "_id": stream_id,
        "title": data.title,
        "description": data.description,
        "category": data.category,
        "tags": data.tags,
        "status": StreamStatus.CREATED,
        "stream_key": stream_key,
        "rtmp_url": ams.build_rtmp_ingest_url(stream_key),
        "hls_url": ams.build_hls_url(stream_id),
        "webrtc_url": ams.build_webrtc_url(stream_id),
        "viewer_count": 0,
        "owner_id": owner_id,
        "created_at": datetime.utcnow(),
        "started_at": None,
        "ended_at": None,
    }
    await db[COLLECTION].insert_one(doc)
    return _serialize(doc)


async def get_stream(db: AsyncIOMotorDatabase, stream_id: str) -> dict:
    doc = await db[COLLECTION].find_one({"_id": stream_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found")
    return _serialize(doc)


async def list_streams(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    page_size: int = 20,
    status_filter: StreamStatus | None = None,
    owner_id: str | None = None,
) -> dict:
    query = {}
    if status_filter:
        query["status"] = status_filter
    if owner_id:
        query["owner_id"] = owner_id

    total = await db[COLLECTION].count_documents(query)
    cursor = db[COLLECTION].find(query).skip((page - 1) * page_size).limit(page_size)
    docs = await cursor.to_list(length=page_size)
    return {
        "streams": [_serialize(d) for d in docs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def start_stream(db: AsyncIOMotorDatabase, stream_id: str, owner_id: str) -> dict:
    doc = await _get_owned_stream(db, stream_id, owner_id)
    if doc["status"] == StreamStatus.LIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stream already live")
    if doc["status"] == StreamStatus.ENDED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stream has ended")

    try:
        await ams.start_broadcast(stream_id)
    except Exception as exc:
        logger.warning(f"AMS start_broadcast failed: {exc}")

    await db[COLLECTION].update_one(
        {"_id": stream_id},
        {"$set": {"status": StreamStatus.LIVE, "started_at": datetime.utcnow()}},
    )
    return await get_stream(db, stream_id)


async def stop_stream(db: AsyncIOMotorDatabase, stream_id: str, owner_id: str) -> dict:
    await _get_owned_stream(db, stream_id, owner_id)

    try:
        await ams.stop_broadcast(stream_id)
    except Exception as exc:
        logger.warning(f"AMS stop_broadcast failed: {exc}")

    await db[COLLECTION].update_one(
        {"_id": stream_id},
        {"$set": {"status": StreamStatus.ENDED, "ended_at": datetime.utcnow()}},
    )
    return await get_stream(db, stream_id)


async def update_stream(
    db: AsyncIOMotorDatabase, stream_id: str, owner_id: str, data: StreamUpdate
) -> dict:
    await _get_owned_stream(db, stream_id, owner_id)
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return await get_stream(db, stream_id)
    await db[COLLECTION].update_one({"_id": stream_id}, {"$set": updates})
    return await get_stream(db, stream_id)


async def delete_stream(db: AsyncIOMotorDatabase, stream_id: str, owner_id: str) -> None:
    doc = await _get_owned_stream(db, stream_id, owner_id)
    if doc["status"] == StreamStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a live stream. Stop it first.",
        )
    await db[COLLECTION].delete_one({"_id": stream_id})


async def get_stream_stats(db: AsyncIOMotorDatabase, stream_id: str) -> dict:
    doc = await get_stream(db, stream_id)
    ams_stats = {}
    if doc["status"] == StreamStatus.LIVE:
        try:
            ams_stats = await ams.get_broadcast_statistics(stream_id)
        except Exception as exc:
            logger.warning(f"AMS stats fetch failed: {exc}")
    return {"stream": doc, "ams_stats": ams_stats}


# ── helpers ──────────────────────────────────────────────────────────────────

async def _get_owned_stream(db: AsyncIOMotorDatabase, stream_id: str, owner_id: str) -> dict:
    doc = await db[COLLECTION].find_one({"_id": stream_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found")
    if doc["owner_id"] != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your stream")
    return _serialize(doc)


def _serialize(doc: dict) -> dict:
    doc["id"] = doc.pop("_id")
    return doc
