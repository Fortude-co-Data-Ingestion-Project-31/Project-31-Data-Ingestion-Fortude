import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from source_registration_table import SOURCES

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ingestion")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        _db = get_client()[MONGO_DB_NAME]
    return _db


async def init_mongo():
    db = get_db()

    # One event collection, shared across sources
    await db.document_events.create_index("event_id", unique=True)
    await db.document_events.create_index("source")
    await db.document_events.create_index("document_id")
    await db.document_events.create_index([("document_id", 1), ("occurred_at", 1)])

    # Per-source collections and their indexes
    for spec in SOURCES.values():
        col = db[spec.collection]

        # identity field is unique
        if isinstance(spec.identity, str):
            await col.create_index(spec.identity, unique=True)

        for field in spec.indexes:
            await col.create_index(field)

    print("[mongo] indexes ensured")


async def close_mongo():
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
