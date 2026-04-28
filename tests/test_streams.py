import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import get_current_user_id

MOCK_STREAM = {
    "id": "abc123",
    "title": "My Test Stream",
    "description": "Test description",
    "category": "gaming",
    "tags": ["test"],
    "status": "created",
    "stream_key": "sk_testkey123",
    "rtmp_url": "rtmp://example.com:1935/live/sk_testkey123",
    "hls_url": "http://example.com:5080/live/streams/abc123.m3u8",
    "webrtc_url": "wss://example.com:5443/live/websocket?streamId=abc123&token=",
    "viewer_count": 0,
    "owner_id": "user-001",
    "created_at": "2024-01-01T00:00:00",
    "started_at": None,
    "ended_at": None,
}


async def mock_auth_user():
    return "user-001"


def get_client():
    app.dependency_overrides[get_current_user_id] = mock_auth_user
    return TestClient(app)


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@patch("app.api.v1.streams.stream_service.create_stream", new_callable=AsyncMock, return_value=MOCK_STREAM)
@patch("app.api.v1.streams.publish_stream_event", new_callable=AsyncMock)
def test_create_stream(mock_pub, mock_create):
    client = get_client()
    resp = client.post(
        "/api/v1/streams/",
        json={"title": "My Test Stream", "description": "Test description", "tags": ["test"]},
        headers={"Authorization": "Bearer faketoken"},
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "My Test Stream"
    assert "rtmp_url" in resp.json()
    assert "hls_url" in resp.json()


@patch("app.api.v1.streams.stream_service.list_streams", new_callable=AsyncMock)
def test_list_streams(mock_list):
    mock_list.return_value = {"streams": [MOCK_STREAM], "total": 1, "page": 1, "page_size": 20}
    client = TestClient(app)
    resp = client.get("/api/v1/streams/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert len(resp.json()["streams"]) == 1


@patch("app.api.v1.streams.stream_service.get_stream", new_callable=AsyncMock, return_value=MOCK_STREAM)
def test_get_stream(mock_get):
    client = TestClient(app)
    resp = client.get("/api/v1/streams/abc123")
    assert resp.status_code == 200
    assert resp.json()["id"] == "abc123"


@patch("app.api.v1.streams.stream_service.start_stream", new_callable=AsyncMock)
@patch("app.api.v1.streams.publish_stream_event", new_callable=AsyncMock)
def test_start_stream(mock_pub, mock_start):
    mock_start.return_value = {**MOCK_STREAM, "status": "live"}
    client = get_client()
    resp = client.post(
        "/api/v1/streams/abc123/start",
        headers={"Authorization": "Bearer faketoken"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"


@patch("app.api.v1.streams.stream_service.stop_stream", new_callable=AsyncMock)
@patch("app.api.v1.streams.publish_stream_event", new_callable=AsyncMock)
def test_stop_stream(mock_pub, mock_stop):
    mock_stop.return_value = {**MOCK_STREAM, "status": "ended"}
    client = get_client()
    resp = client.post(
        "/api/v1/streams/abc123/stop",
        headers={"Authorization": "Bearer faketoken"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ended"
