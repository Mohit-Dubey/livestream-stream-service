"""
Run once on first startup to create MongoDB indexes.
Usage: python -m app.db.init_db
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def create_indexes():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB]
    collection = db["streams"]

    await collection.create_index("owner_id")
    await collection.create_index("status")
    await collection.create_index([("owner_id", 1), ("status", 1)])
    await collection.create_index("created_at")

    print(f"Indexes created on {settings.MONGO_DB}.streams")
    client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
