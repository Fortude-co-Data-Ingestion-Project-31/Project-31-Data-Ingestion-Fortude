"""Write document chunks and local embeddings to MongoDB Vector Search."""

import asyncio
import os
import threading
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ReplaceOne
from pymongo.operations import SearchIndexModel

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Collection inside the vector database; choose any collection name. MongoDB
# creates it on first write. This is not the Atlas project or cluster name.
VECTOR_COLLECTION = os.getenv("MONGO_VECTOR_COLLECTION", "vector_chunks")
VECTOR_INDEX = "vector_index"
# Atlas connection URI for the vector cluster. Find it in Atlas: cluster
# > Connect > Drivers, then copy the connection string. Keep credentials private.
MONGO_VECTOR_URI = os.getenv("MONGO_VECTOR_URI")
# Database inside that cluster. Find or create it in Atlas Data Explorer;
# this is not the Atlas project or cluster name.
MONGO_VECTOR_DB_NAME = os.getenv("MONGO_VECTOR_DB_NAME")
# Local sentence-transformers model used to generate embeddings; defaults to
# all-MiniLM-L6-v2. Set this to another installed/downloadable model if needed.
EMBEDDING_MODEL = os.getenv(
    "MONGO_VECTOR_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

_model = None
_model_lock = threading.Lock()
_vector_client: AsyncIOMotorClient | None = None
_vector_db: AsyncIOMotorDatabase | None = None


def get_vector_client() -> AsyncIOMotorClient:
    """Return the Mongo client dedicated to vector output."""
    global _vector_client
    if _vector_client is None:
        if not MONGO_VECTOR_URI:
            raise RuntimeError(
                "MongoDB vector output is not configured. Set "
                "MONGO_VECTOR_URI in backend/app/.env."
            )
        _vector_client = AsyncIOMotorClient(MONGO_VECTOR_URI)
    return _vector_client


def get_vector_db() -> AsyncIOMotorDatabase:
    """Return the database dedicated to vector output."""
    global _vector_db
    if _vector_db is None:
        if not MONGO_VECTOR_DB_NAME:
            raise RuntimeError(
                "MongoDB vector output is not configured. Set "
                "MONGO_VECTOR_DB_NAME in backend/app/.env."
            )
        _vector_db = get_vector_client()[MONGO_VECTOR_DB_NAME]
    return _vector_db


async def verify_vector_database() -> None:
    """Fail clearly unless the dedicated vector database is reachable."""
    get_vector_db()
    await get_vector_client().admin.command("ping")


async def close_vector_mongo() -> None:
    """Close and clear the dedicated vector database client."""
    global _vector_client, _vector_db
    if _vector_client is not None:
        _vector_client.close()
    _vector_client = None
    _vector_db = None


def _get_model():
    """Load the configured local sentence-transformers model on first use."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:
                    raise RuntimeError(
                        "MongoDB vector output requires sentence-transformers. "
                        "Install the project requirements before enabling it."
                    ) from exc
                _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _flatten_content(value) -> str:
    """Turn structured source content into readable text for embedding."""
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            text = _flatten_content(item)
            if text:
                parts.append(f"{key}: {text}")
        return " ".join(parts)
    if isinstance(value, (list, tuple)):
        return " ".join(_flatten_content(item) for item in value if item is not None)
    if isinstance(value, (str, int, float, bool)):
        return str(value).strip()
    return ""


def _document_chunks(document: dict) -> list[dict]:
    """Use canonical chunks or derive one text chunk from a source record."""
    chunks = document.get("chunks")
    if isinstance(chunks, list) and chunks:
        return [
            {
                **chunk,
                "content": str(chunk.get("content") or "").strip(),
            }
            for chunk in chunks
            if isinstance(chunk, dict) and str(chunk.get("content") or "").strip()
        ]

    fields = ("title", "summary", "description", "content", "comments")
    parts = [
        f"{field}: {text}"
        for field in fields
        if (text := _flatten_content(document.get(field)))
    ]
    text = "\n".join(parts)
    if not text:
        return []
    return [{"chunk_id": "0", "chunk_index": 0, "content": text}]


def _document_id(document: dict) -> str:
    for field in ("document_id", "ticket_key", "ticket_id", "file_name", "id"):
        value = document.get(field)
        if value is not None and str(value).strip():
            return str(value).strip()
    raise ValueError("MongoDB vector output requires a stable document identifier.")


def _embed_texts(texts: list[str]) -> tuple[list[list[float]], int]:
    model = _get_model()
    dimension = model.get_sentence_embedding_dimension()
    if not isinstance(dimension, int) or dimension <= 0:
        raise ValueError("The configured embedding model has no valid vector dimension.")
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.tolist(), dimension


async def _ensure_vector_index(collection, dimension: int) -> None:
    """Create the Atlas Vector Search index once, or reject incompatible dimensions."""
    indexes = await collection.list_search_indexes().to_list(length=None)
    existing = next(
        (index for index in indexes if index.get("name") == VECTOR_INDEX),
        None,
    )
    if existing:
        definition = existing.get("latestDefinition") or existing.get("definition") or {}
        fields = definition.get("fields", [])
        vector_field = next(
            (field for field in fields if field.get("path") == "embedding"),
            None,
        )
        if vector_field is None:
            raise ValueError(
                f"MongoDB vector index '{VECTOR_INDEX}' does not index the "
                "embedding field. Update the Atlas index definition before writing."
            )
        if vector_field.get("numDimensions") != dimension:
            raise ValueError(
                f"MongoDB vector index '{VECTOR_INDEX}' uses "
                f"{vector_field.get('numDimensions')} dimensions, but the "
                f"configured embedding model uses {dimension}. Recreate the "
                "Atlas index or select a model with a matching dimension."
            )
        return

    definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": dimension,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "source"},
            {"type": "filter", "path": "document_id"},
        ]
    }
    await collection.create_search_index(
        SearchIndexModel(definition=definition, name=VECTOR_INDEX)
    )


async def persist_vectors(source: str, documents: Iterable[dict]) -> dict:
    """Embed and upsert canonical document chunks independently of document storage."""
    await verify_vector_database()
    operations = []
    desired_chunks: dict[tuple[str, str], list[str]] = defaultdict(list)
    skipped = 0

    for document in documents:
        document_id = _document_id(document)
        document_source = str(document.get("source") or source)
        desired_chunks.setdefault((document_source, document_id), [])
        chunks = _document_chunks(document)
        if not chunks:
            skipped += 1
            continue

        for index, chunk in enumerate(chunks):
            chunk_id = str(chunk.get("chunk_id") or chunk.get("chunk_index") or index)
            record_id = f"{document_source}:{document_id}:{chunk_id}"
            desired_chunks[(document_source, document_id)].append(chunk_id)
            operations.append(
                {
                    "record_id": record_id,
                    "source": document_source,
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk.get("chunk_index", index),
                    "content": chunk["content"],
                    "title": document.get("title") or document.get("file_name"),
                    "source_url": document.get("source_url"),
                    "mapper": document.get("mapper"),
                    "rule_applied": document.get("rule_applied"),
                    "tags": document.get("tags", []),
                    "metadata": document.get("metadata", {}),
                    "kb_status": document.get("kb_status"),
                    "kb_category": document.get("kb_category"),
                    "page": chunk.get("page"),
                    "slide": chunk.get("slide"),
                    "sheet": chunk.get("sheet"),
                }
            )

    if not operations:
        if desired_chunks:
            collection = get_vector_db()[VECTOR_COLLECTION]
            for (document_source, document_id), chunk_ids in desired_chunks.items():
                await collection.delete_many(
                    {
                        "source": document_source,
                        "document_id": document_id,
                        "chunk_id": {"$nin": chunk_ids},
                    }
                )
        return {
            "source": source,
            "documents_indexed": 0,
            "chunks_indexed": 0,
            "skipped": skipped,
            "database": MONGO_VECTOR_DB_NAME,
            "collection": VECTOR_COLLECTION,
        }

    embeddings, dimension = await asyncio.to_thread(
        _embed_texts,
        [operation["content"] for operation in operations],
    )
    collection = get_vector_db()[VECTOR_COLLECTION]
    await collection.create_index([("source", 1), ("document_id", 1)])
    await _ensure_vector_index(collection, dimension)

    writes = []
    for operation, embedding in zip(operations, embeddings):
        record = {
            **operation,
            "_id": operation["record_id"],
            "embedding": embedding,
        }
        writes.append(
            ReplaceOne({"_id": operation["record_id"]}, record, upsert=True)
        )
    await collection.bulk_write(writes, ordered=False)

    for (document_source, document_id), chunk_ids in desired_chunks.items():
        await collection.delete_many(
            {
                "source": document_source,
                "document_id": document_id,
                "chunk_id": {"$nin": chunk_ids},
            }
        )

    return {
        "source": source,
        "documents_indexed": len(desired_chunks),
        "chunks_indexed": len(operations),
        "skipped": skipped,
        "database": MONGO_VECTOR_DB_NAME,
        "collection": VECTOR_COLLECTION,
    }


async def delete_vectors(source: str, document_ids: Iterable[str]) -> int:
    """Remove all vector chunks belonging to deleted source documents."""
    identifiers = [str(document_id) for document_id in document_ids]
    if not identifiers:
        return 0
    await verify_vector_database()
    result = await get_vector_db()[VECTOR_COLLECTION].delete_many(
        {"source": source, "document_id": {"$in": identifiers}}
    )
    return result.deleted_count


async def list_vectors(
    source: str | None = None, limit: int = 50, offset: int = 0
) -> dict:
    """Return stored vector chunk text and metadata without embedding arrays."""
    await verify_vector_database()
    collection = get_vector_db()[VECTOR_COLLECTION]
    query = {"source": source} if source else {}
    total = await collection.count_documents(query)
    cursor = (
        collection.find(query, {"embedding": 0})
        .sort([("source", 1), ("document_id", 1), ("chunk_index", 1)])
        .skip(offset)
        .limit(limit)
    )
    documents = await cursor.to_list(length=limit)
    for document in documents:
        document.pop("_id", None)
        document.pop("embedding", None)
    return {
        "items": documents,
        "total": total,
        "limit": limit,
        "offset": offset,
        "database": MONGO_VECTOR_DB_NAME,
        "collection": VECTOR_COLLECTION,
    }
