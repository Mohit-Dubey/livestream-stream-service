"""
Ant Media Server Enterprise REST API v2 client.
Docs: https://antmedia.io/rest/#/
"""
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

BASE = f"{settings.ANT_MEDIA_URL}/{settings.ANT_MEDIA_APP}/rest/v2"
AUTH = (settings.ANT_MEDIA_USER, settings.ANT_MEDIA_PASSWORD)
TIMEOUT = 10.0


async def _request(method: str, path: str, **kwargs):
    url = f"{BASE}{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.request(method, url, auth=AUTH, **kwargs)
        resp.raise_for_status()
        return resp.json()


async def create_broadcast(stream_id: str, stream_name: str) -> dict:
    """Create a new broadcast on Ant Media Server."""
    payload = {
        "streamId": stream_id,
        "name": stream_name,
        "type": "liveStream",
        "status": "created",
    }
    return await _request("POST", "/broadcasts/create", json=payload)


async def start_broadcast(stream_id: str) -> dict:
    """Mark a broadcast as active (triggered by RTMP publish start)."""
    return await _request("PUT", f"/broadcasts/{stream_id}", json={"status": "broadcasting"})


async def stop_broadcast(stream_id: str) -> dict:
    """Stop/finish a broadcast."""
    return await _request("DELETE", f"/broadcasts/{stream_id}")


async def get_broadcast(stream_id: str) -> dict:
    """Fetch broadcast details including viewer count and status."""
    return await _request("GET", f"/broadcasts/{stream_id}")


async def get_broadcast_statistics(stream_id: str) -> dict:
    """Get viewer stats and bitrate info for a live broadcast."""
    return await _request("GET", f"/broadcasts/{stream_id}/broadcastStatistics")


def build_rtmp_ingest_url(stream_key: str) -> str:
    return f"rtmp://{settings.ANT_MEDIA_URL.split('//')[1].split(':')[0]}:1935/{settings.ANT_MEDIA_APP}/{stream_key}"


def build_hls_url(stream_id: str) -> str:
    return f"{settings.ANT_MEDIA_URL}/{settings.ANT_MEDIA_APP}/streams/{stream_id}.m3u8"


def build_webrtc_url(stream_id: str) -> str:
    ant_host = settings.ANT_MEDIA_URL.replace("http://", "").replace("https://", "").split(":")[0]
    return f"wss://{ant_host}:5443/{settings.ANT_MEDIA_APP}/websocket?streamId={stream_id}&token="
