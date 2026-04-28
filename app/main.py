from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1 import streams
from app.db.database import close_connection
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_connection()


app = FastAPI(
    title="Stream Service",
    description="Manages live streams and integrates with Ant Media Server Enterprise",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(streams.router, prefix="/api/v1/streams", tags=["Streams"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "stream-service"}
