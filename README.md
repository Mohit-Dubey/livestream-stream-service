# Stream Service

Microservice responsible for managing live stream lifecycle and integrating with **Ant Media Server Enterprise** for real RTMP/HLS/WebRTC streaming. Part of the **Live Streaming Platform** built for SEZG583 — Scalable Services assignment.

---

## Overview

| Property | Value |
|----------|-------|
| Language | Python 3.11 |
| Framework | FastAPI |
| Database | MongoDB |
| Messaging | RabbitMQ (publishes stream events) |
| External | Ant Media Server Enterprise (REST API v2) |
| Port | 8001 |

---

## API Endpoints

### Streams
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/streams/` | Create a new stream | ✅ |
| GET | `/api/v1/streams/` | List all streams | ❌ |
| GET | `/api/v1/streams/my` | List my streams | ✅ |
| GET | `/api/v1/streams/{stream_id}` | Get stream details | ❌ |
| PUT | `/api/v1/streams/{stream_id}` | Update stream metadata | ✅ |
| DELETE | `/api/v1/streams/{stream_id}` | Delete a stream | ✅ |
| POST | `/api/v1/streams/{stream_id}/start` | Start streaming (go live) | ✅ |
| POST | `/api/v1/streams/{stream_id}/stop` | Stop streaming | ✅ |
| GET | `/api/v1/streams/{stream_id}/stats` | Get live viewer stats | ❌ |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

---

## Stream Lifecycle

```
CREATE → status: created   (broadcast registered on Ant Media)
   ↓
START  → status: live      (RTMP ingest activated, OBS can connect)
   ↓
STOP   → status: ended     (broadcast terminated on Ant Media)
```

Once a stream is `live`, push video using OBS or any RTMP encoder:
- **RTMP Server:** `rtmp://<ANT_MEDIA_IP>:1935/live`
- **Stream Key:** returned in the create response

---

## Project Structure

```
stream-service/
├── app/
│   ├── main.py                      # FastAPI app entry point
│   ├── api/v1/
│   │   └── streams.py               # All stream endpoints
│   ├── core/
│   │   ├── config.py                # Settings via pydantic-settings
│   │   └── auth.py                  # JWT validation via User Service
│   ├── db/
│   │   ├── database.py              # Motor async MongoDB client
│   │   └── init_db.py               # MongoDB index creation
│   ├── schemas/
│   │   └── stream.py                # Pydantic schemas + StreamStatus enum
│   └── services/
│       ├── stream_service.py        # Business logic
│       ├── ant_media_client.py      # Ant Media Server REST API v2 client
│       └── event_publisher.py       # RabbitMQ event publisher
├── tests/
│   ├── conftest.py                  # Test fixtures
│   └── test_streams.py              # Stream endpoint tests
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Running Locally

### With Docker Compose (recommended)

From the root `livestream/` folder:

```bash
docker compose up --build
```

Stream Service will be available at:
- API: http://localhost:8001
- Swagger UI: http://localhost:8001/docs

### Without Docker (development)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Ant Media and MongoDB details

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

---

## Running Tests

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m pytest tests/ -v
```

Tests use mocked MongoDB and Ant Media — no external services required.

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DB` | MongoDB database name | `streamdb` |
| `RABBITMQ_URL` | RabbitMQ connection string | `amqp://guest:guest@localhost:5672/` |
| `ANT_MEDIA_URL` | Ant Media Server base URL | `http://52.66.16.210:5080` |
| `ANT_MEDIA_APP` | Ant Media application name | `live` |
| `ANT_MEDIA_USER` | Ant Media admin username | `admin` |
| `ANT_MEDIA_PASSWORD` | Ant Media admin password | — |
| `USER_SERVICE_URL` | User Service base URL for JWT validation | `http://user-service:8000` |

---

## Ant Media Server Integration

This service integrates with **Ant Media Server Enterprise** via REST API v2.

### What happens on each API call

| Our API | Ant Media API call |
|---------|-------------------|
| `POST /streams/` | `POST /broadcasts/create` |
| `POST /streams/{id}/start` | `PUT /broadcasts/{id}` → status: broadcasting |
| `POST /streams/{id}/stop` | `DELETE /broadcasts/{id}` |
| `GET /streams/{id}/stats` | `GET /broadcasts/{id}/broadcastStatistics` |

### Streaming with OBS
1. Open OBS → Settings → Stream
2. Service: Custom
3. Server: `rtmp://<ANT_MEDIA_IP>:1935/live`
4. Stream Key: value from create stream response
5. Click Start Streaming

---

## Inter-Service Communication

### Sync (REST)
Calls `GET /api/v1/users/validate` on User Service to verify JWT tokens. This keeps JWT secret management in User Service only.

### Async (RabbitMQ)
Publishes to `stream_events` fanout exchange on:
- `stream.created` — new stream created
- `stream.went_live` — stream started
- `stream.ended` — stream stopped

---

## Docker

```bash
# Build
docker build -t stream-service:latest .

# Run
docker run -p 8001:8001 --env-file .env stream-service:latest
```

---

## Related Repositories

- [livestream-user-service](https://github.com/Mohit-Dubey/livestream-user-service) — User registration, authentication, JWT
