import asyncio

import pytest

from app.outputs.MongoDB import mongo_db_vector_output as vector_output


class FakeCollection:
    def __init__(self):
        self.records = {}
        self.indexes = []

    async def create_index(self, fields):
        self.indexes.append(fields)

    async def bulk_write(self, operations, ordered):
        assert ordered is False
        for operation in operations:
            record_id = operation._filter["_id"]
            self.records[record_id] = {
                **operation._doc,
                "_id": record_id,
            }

    async def delete_many(self, query):
        if "$in" in query.get("document_id", {}):
            source = query["source"]
            document_ids = set(query["document_id"]["$in"])
            removed = [
                record_id
                for record_id, record in self.records.items()
                if record["source"] == source
                and record["document_id"] in document_ids
            ]
            for record_id in removed:
                del self.records[record_id]
            return type("DeleteResult", (), {"deleted_count": len(removed)})()

        source = query["source"]
        document_id = query["document_id"]
        retained = set(query["chunk_id"]["$nin"])
        self.records = {
            record_id: record
            for record_id, record in self.records.items()
            if record["source"] != source
            or record["document_id"] != document_id
            or record["chunk_id"] in retained
        }


def test_persists_chunks_and_removes_stale_chunks(monkeypatch):
    collection = FakeCollection()
    async def verify_connection():
        return None

    monkeypatch.setattr(vector_output, "verify_vector_database", verify_connection)
    monkeypatch.setattr(
        vector_output,
        "get_vector_db",
        lambda: {vector_output.VECTOR_COLLECTION: collection},
    )
    async def ensure_search_index(collection, dimension):
        assert collection.indexes[-1] == [("source", 1), ("document_id", 1)]

    monkeypatch.setattr(vector_output, "_ensure_vector_index", ensure_search_index)

    def embed(texts):
        return [[float(index), 1.0] for index, _ in enumerate(texts)], 2

    monkeypatch.setattr(vector_output, "_embed_texts", embed)
    doc = {
        "source": "sharepoint",
        "document_id": "guide-1",
        "title": "Guide",
        "mapper": "Custom JSON Mapper",
        "rule_applied": "Knowledge Base Rules",
        "tags": ["knowledge"],
        "metadata": {"source": "knowledge-rule"},
        "chunks": [
            {"chunk_id": "guide-1_0", "chunk_index": 0, "content": "First section"},
            {"chunk_id": "guide-1_1", "chunk_index": 1, "content": "Second section"},
        ],
    }

    first = asyncio.run(vector_output.persist_vectors("sharepoint", [doc]))
    assert first == {
        "source": "sharepoint",
        "documents_indexed": 1,
        "chunks_indexed": 2,
        "skipped": 0,
        "database": vector_output.MONGO_VECTOR_DB_NAME,
        "collection": vector_output.VECTOR_COLLECTION,
    }
    assert len(collection.records) == 2
    assert collection.records["sharepoint:guide-1:guide-1_0"]["embedding"] == [0.0, 1.0]
    stored = collection.records["sharepoint:guide-1:guide-1_0"]
    assert stored["mapper"] == "Custom JSON Mapper"
    assert stored["rule_applied"] == "Knowledge Base Rules"
    assert stored["tags"] == ["knowledge"]
    assert stored["metadata"] == {"source": "knowledge-rule"}
    assert collection.indexes == [[("source", 1), ("document_id", 1)]]

    updated = {
        **doc,
        "chunks": [
            {"chunk_id": "guide-1_0", "chunk_index": 0, "content": "Updated section"},
        ],
    }
    asyncio.run(vector_output.persist_vectors("sharepoint", [updated]))
    assert list(collection.records) == ["sharepoint:guide-1:guide-1_0"]
    assert collection.records["sharepoint:guide-1:guide-1_0"]["content"] == "Updated section"


def test_derives_text_from_structured_records():
    chunks = vector_output._document_chunks(
        {
            "document_id": "order-1",
            "item_code": "ITEM",
            "content": {"quantity": 3, "description": "Widget"},
        }
    )

    assert chunks == [
        {
            "chunk_id": "0",
            "chunk_index": 0,
            "content": "content: quantity: 3 description: Widget",
        }
    ]


def test_skips_records_without_text_or_model_load(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(
        vector_output,
        "get_vector_db",
        lambda: {vector_output.VECTOR_COLLECTION: collection},
    )
    async def verify_connection():
        return None

    monkeypatch.setattr(vector_output, "verify_vector_database", verify_connection)

    def unexpected_embed(texts):
        raise AssertionError("No text should be embedded")

    monkeypatch.setattr(vector_output, "_embed_texts", unexpected_embed)
    result = asyncio.run(
        vector_output.persist_vectors(
            "jira",
            [{"ticket_key": "SUP-1", "description": "  "}],
        )
    )

    assert result == {
        "source": "jira",
        "documents_indexed": 0,
        "chunks_indexed": 0,
        "skipped": 1,
        "database": vector_output.MONGO_VECTOR_DB_NAME,
        "collection": vector_output.VECTOR_COLLECTION,
    }


def test_rejects_existing_search_index_with_wrong_dimensions():
    class Cursor:
        async def to_list(self, length):
            return [{
                "name": vector_output.VECTOR_INDEX,
                "definition": {
                    "fields": [{
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": 3,
                    }],
                },
            }]

    class IndexedCollection:
        def list_search_indexes(self):
            return Cursor()

    with pytest.raises(ValueError, match="uses 3 dimensions"):
        asyncio.run(vector_output._ensure_vector_index(IndexedCollection(), 2))


def test_deletes_all_chunks_for_removed_documents(monkeypatch):
    collection = FakeCollection()
    collection.records = {
        "sharepoint:guide-1:0": {
            "source": "sharepoint",
            "document_id": "guide-1",
            "chunk_id": "0",
        },
        "sharepoint:guide-2:0": {
            "source": "sharepoint",
            "document_id": "guide-2",
            "chunk_id": "0",
        },
    }
    monkeypatch.setattr(
        vector_output,
        "get_vector_db",
        lambda: {vector_output.VECTOR_COLLECTION: collection},
    )
    async def verify_connection():
        return None

    monkeypatch.setattr(vector_output, "verify_vector_database", verify_connection)

    deleted = asyncio.run(
        vector_output.delete_vectors("sharepoint", {"guide-1"})
    )

    assert deleted == 1
    assert list(collection.records) == ["sharepoint:guide-2:0"]


def test_lists_chunk_metadata_without_embedding_arrays(monkeypatch):
    class Cursor:
        def __init__(self):
            self.records = [{
                "_id": "sharepoint:guide-1:guide-1_0",
                "record_id": "sharepoint:guide-1:guide-1_0",
                "source": "sharepoint",
                "document_id": "guide-1",
                "chunk_index": 0,
                "content": "First section",
                "embedding": [0.1, 0.2],
            }]

        def sort(self, fields):
            assert fields == [
                ("source", 1), ("document_id", 1), ("chunk_index", 1)
            ]
            return self

        def skip(self, offset):
            assert offset == 5
            return self

        def limit(self, limit):
            assert limit == 10
            return self

        async def to_list(self, length):
            return self.records[:length]

    class Collection:
        async def count_documents(self, query):
            assert query == {"source": "sharepoint"}
            return 1

        def find(self, query, projection):
            assert query == {"source": "sharepoint"}
            assert projection == {"embedding": 0}
            return Cursor()

    monkeypatch.setattr(
        vector_output,
        "get_vector_db",
        lambda: {vector_output.VECTOR_COLLECTION: Collection()},
    )
    async def verify_connection():
        return None

    monkeypatch.setattr(vector_output, "verify_vector_database", verify_connection)
    result = asyncio.run(
        vector_output.list_vectors(source="sharepoint", limit=10, offset=5)
    )

    assert result["total"] == 1
    assert result["limit"] == 10
    assert result["offset"] == 5
    assert result["database"] == vector_output.MONGO_VECTOR_DB_NAME
    assert result["collection"] == vector_output.VECTOR_COLLECTION
    assert result["items"] == [{
        "record_id": "sharepoint:guide-1:guide-1_0",
        "source": "sharepoint",
        "document_id": "guide-1",
        "chunk_index": 0,
        "content": "First section",
    }]


def test_requires_separate_vector_database_configuration(monkeypatch):
    monkeypatch.setattr(vector_output, "_vector_db", None)
    monkeypatch.setattr(vector_output, "MONGO_VECTOR_DB_NAME", None)

    with pytest.raises(RuntimeError, match="MONGO_VECTOR_DB_NAME"):
        vector_output.get_vector_db()

    monkeypatch.setattr(vector_output, "_vector_client", None)
    monkeypatch.setattr(vector_output, "MONGO_VECTOR_DB_NAME", "atlas_vectors")
    monkeypatch.setattr(vector_output, "MONGO_VECTOR_URI", None)

    with pytest.raises(RuntimeError, match="MONGO_VECTOR_URI"):
        vector_output.get_vector_client()


def test_vector_storage_uses_dedicated_mongodb_client_and_database(monkeypatch):
    connections = []

    class FakeClient:
        def __init__(self, uri):
            connections.append(uri)
            self.closed = False

        def __getitem__(self, database_name):
            return {"database": database_name}

        def close(self):
            self.closed = True

    monkeypatch.setattr(vector_output, "_vector_client", None)
    monkeypatch.setattr(vector_output, "_vector_db", None)
    monkeypatch.setattr(vector_output, "MONGO_VECTOR_URI", "mongodb+srv://vector")
    monkeypatch.setattr(vector_output, "MONGO_VECTOR_DB_NAME", "vectors")
    monkeypatch.setattr(vector_output, "AsyncIOMotorClient", FakeClient)

    database = vector_output.get_vector_db()
    client = vector_output.get_vector_client()

    assert connections == ["mongodb+srv://vector"]
    assert database == {"database": "vectors"}
    assert client is vector_output._vector_client
    asyncio.run(vector_output.close_vector_mongo())
    assert client.closed
    assert vector_output._vector_client is None
    assert vector_output._vector_db is None
