import asyncio
import json

from fastapi import BackgroundTasks

from app import main
from app.connectors import config_db


def run_endpoint(request):
    return asyncio.run(main.ingest_local_folder(request, BackgroundTasks()))


def test_manual_sharepoint_selection_uses_shared_sync_and_history(monkeypatch):
    calls = []
    history = []
    monkeypatch.setattr(
        main, "run_sharepoint_ingestion",
        lambda rule: calls.append(rule)
        or {"status": "success", "processed": 2, "rule": rule},
    )
    monkeypatch.setattr(main, "add_history_entry", lambda **kwargs: history.append(kwargs))

    result = run_endpoint(main.IngestionRequest(
        connector="SharePoint", rule="Knowledge Base Rules",
        mapper="Document Mapper", outputs="Kafka",
    ))

    assert calls == ["Knowledge Base Rules"]
    assert result["processed"] == 2
    assert history == [{
        "connector": "SharePoint", "mapper": "Document Mapper",
        "rules": "Knowledge Base Rules", "outputs": "Kafka",
        "status": "completed", "processed": 2,
    }]


def test_non_sharepoint_connector_keeps_local_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "INPUT_FOLDER", tmp_path / "input")
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path / "output")
    monkeypatch.setattr(main, "read_local_text_files", lambda folder: [])
    monkeypatch.setattr(main, "add_history_entry", lambda **kwargs: None)
    monkeypatch.setattr(
        main, "run_sharepoint_ingestion",
        lambda rule: (_ for _ in ()).throw(AssertionError("SharePoint should not run")),
    )

    result = run_endpoint(main.IngestionRequest(connector="Local Files"))

    assert result["processed"] == 0


def configure_sync_mocks(monkeypatch, delta_result, mappings=None, old_delta="old-delta"):
    saved = []
    monkeypatch.setattr(main, "get_sharepoint_drive_id", lambda: "drive-id")
    monkeypatch.setattr(main, "get_sharepoint_delta_link", lambda drive_id: old_delta)
    monkeypatch.setattr(main, "get_sharepoint_item_mappings", lambda drive_id: mappings or {})
    monkeypatch.setattr(main, "read_sharepoint_delta", lambda delta=None: delta_result)
    monkeypatch.setattr(
        main, "save_sharepoint_sync_state",
        lambda *args: saved.append(args),
    )

    async def fake_persist(source, documents):
        return {"source": source, "inserted": len(documents)}

    monkeypatch.setattr(main, "persist", fake_persist)
    return saved


def test_sharepoint_persists_only_accepted_documents_when_mongodb_selected(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    delta = {
        "delta_link": "new-delta",
        "changes": [
            {
                "item_id": "accepted-id", "deleted": False, "supported": True,
                "record": {
                    "source": "sharepoint", "item_id": "accepted-id",
                    "file_name": "guide.txt",
                    "content": "guide",
                },
            },
            {
                "item_id": "rejected-id", "deleted": False, "supported": True,
                "record": {
                    "source": "sharepoint", "item_id": "rejected-id",
                    "file_name": "secret.txt",
                    "content": "password: exposed",
                },
            },
        ],
    }
    configure_sync_mocks(monkeypatch, delta)
    persisted = []
    events = []

    async def capture_persist(source, documents):
        events.append("persist")
        persisted.append((source, documents))

    monkeypatch.setattr(main, "persist", capture_persist)
    monkeypatch.setattr(
        main,
        "save_sharepoint_sync_state",
        lambda *args: events.append("save"),
    )

    monkeypatch.setattr(main, "add_history_entry", lambda **kwargs: None)
    result = run_endpoint(main.IngestionRequest(
        connector="SharePoint",
        rule="Knowledge Base Rules",
        outputs="MongoDB",
    ))

    spec = main.SOURCES["sharepoint"]
    assert spec.collection == "sharepoint_documents"
    assert spec.identity == "document_id"
    assert result["processed"] == 2
    assert len(persisted) == 1
    assert persisted[0][0] == "sharepoint"
    assert [document["document_id"] for document in persisted[0][1]] == ["accepted-id"]
    assert persisted[0][1][0]["chunks"]
    assert persisted[0][1][0]["kb_status"] == "active"
    assert persisted[0][1][0]["kb_category"] == "how-to"
    assert "knowledge" in persisted[0][1][0]["tags"]
    assert events == ["persist", "save"]


def test_sharepoint_does_not_contact_mongodb_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    delta = {
        "delta_link": "new-delta",
        "changes": [{
            "item_id": "new-id", "deleted": False, "supported": True,
            "record": {
                "source": "sharepoint", "file_name": "guide.txt", "content": "guide",
            },
        }],
    }
    configure_sync_mocks(monkeypatch, delta)
    monkeypatch.setattr(main, "add_history_entry", lambda **kwargs: None)

    async def unexpected_persist(source, documents):
        raise AssertionError("MongoDB should not be contacted")

    monkeypatch.setattr(main, "persist", unexpected_persist)

    result = run_endpoint(main.IngestionRequest(connector="SharePoint"))

    assert result == {"status": "success", "processed": 1, "rule": "Default Rule"}
    assert (tmp_path / "guide.json").exists()


def test_sharepoint_mongodb_failure_does_not_advance_delta(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    delta = {
        "delta_link": "must-not-save",
        "changes": [{
            "item_id": "new-id", "deleted": False, "supported": True,
            "record": {
                "source": "sharepoint", "file_name": "guide.txt", "content": "guide",
            },
        }],
    }
    saved = configure_sync_mocks(monkeypatch, delta)

    async def failed_persist(source, documents):
        raise RuntimeError("Mongo unavailable")

    monkeypatch.setattr(main, "persist", failed_persist)

    try:
        run_endpoint(main.IngestionRequest(connector="SharePoint", outputs="MongoDB"))
    except RuntimeError as exc:
        assert str(exc) == "Mongo unavailable"
    else:
        raise AssertionError("Expected Mongo output failure")

    assert saved == []


def test_selected_mongodb_saves_state_when_no_documents_are_accepted(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    delta = {
        "delta_link": "new-delta",
        "changes": [{
            "item_id": "rejected-id", "deleted": False, "supported": True,
            "record": {
                "source": "sharepoint", "file_name": "secret.txt",
                "content": "password: exposed",
            },
        }],
    }
    saved = configure_sync_mocks(monkeypatch, delta)
    monkeypatch.setattr(main, "add_history_entry", lambda **kwargs: None)

    async def unexpected_persist(source, documents):
        raise AssertionError("Rejected documents must not reach MongoDB")

    monkeypatch.setattr(main, "persist", unexpected_persist)

    result = run_endpoint(main.IngestionRequest(
        connector="SharePoint",
        rule="Knowledge Base Rules",
        outputs="MongoDB",
    ))

    assert result["processed"] == 1
    assert (tmp_path / "secret.json").exists()
    assert saved == [
        ("drive-id", "new-delta", {"rejected-id": "secret.json"}, set())
    ]


def test_sync_processes_new_file_and_advances_state(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    delta = {
        "delta_link": "new-delta",
        "changes": [{
            "item_id": "new-id", "deleted": False,
            "supported": True,
            "record": {"source": "sharepoint", "file_name": "guide.txt", "content": "new"},
        }],
    }
    saved = configure_sync_mocks(monkeypatch, delta)

    result = main.run_sharepoint_ingestion("Knowledge Base Rules")

    assert result["processed"] == 1
    assert json.loads((tmp_path / "guide.json").read_text())["content"] == "new"
    assert saved == [("drive-id", "new-delta", {"new-id": "guide.json"}, set())]


def test_sync_handles_delete_and_rename_by_item_id(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    (tmp_path / "deleted.json").write_text("old")
    (tmp_path / "old-name.json").write_text("old")
    delta = {
        "delta_link": "next",
        "changes": [
            {"item_id": "deleted-id", "deleted": True, "supported": False,
             "record": None},
            {"item_id": "rename-id", "deleted": False, "supported": True,
             "record": {"source": "sharepoint", "item_id": "rename-id",
                        "file_name": "new-name.txt", "content": "updated"}},
        ],
    }
    saved = configure_sync_mocks(
        monkeypatch, delta,
        {"deleted-id": "deleted.json", "rename-id": "old-name.json"},
    )

    main.run_sharepoint_ingestion("Default Rule")

    assert not (tmp_path / "deleted.json").exists()
    assert not (tmp_path / "old-name.json").exists()
    assert (tmp_path / "new-name.json").exists()
    assert json.loads((tmp_path / "new-name.json").read_text())["document_id"] == "rename-id"
    assert saved[0][2] == {"rename-id": "new-name.json"}
    assert saved[0][3] == {"deleted-id"}


def test_supported_renamed_to_unsupported_removes_output(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    (tmp_path / "guide.json").write_text("old")
    delta = {
        "delta_link": "next",
        "changes": [{"item_id": "item-id", "deleted": False, "supported": False,
                     "record": None}],
    }
    saved = configure_sync_mocks(monkeypatch, delta, {"item-id": "guide.json"})

    main.run_sharepoint_ingestion("Default Rule")

    assert not (tmp_path / "guide.json").exists()
    assert saved[0][3] == {"item-id"}


def test_delta_state_not_advanced_when_processing_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    delta = {
        "delta_link": "must-not-save",
        "changes": [{"item_id": "id", "deleted": False, "supported": True,
                     "record": {"file_name": "bad.txt"}}],
    }
    saved = configure_sync_mocks(monkeypatch, delta)
    monkeypatch.setattr(
        main, "map_local_files_to_canonical",
        lambda records: (_ for _ in ()).throw(RuntimeError("mapping failed")),
    )

    try:
        main.run_sharepoint_ingestion("Default Rule")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected processing failure")

    assert saved == []


def test_invalid_delta_cursor_is_cleared_and_fresh_sync_runs(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    monkeypatch.setattr(main, "get_sharepoint_drive_id", lambda: "drive-id")
    monkeypatch.setattr(main, "get_sharepoint_delta_link", lambda drive_id: "expired")
    monkeypatch.setattr(main, "get_sharepoint_item_mappings", lambda drive_id: {})
    cleared = []
    saved = []
    monkeypatch.setattr(main, "clear_sharepoint_delta_link", lambda drive_id: cleared.append(drive_id))

    def fake_delta(delta=None):
        if delta == "expired":
            raise main.SharePointDeltaStateError("expired")
        return {"delta_link": "fresh", "changes": []}

    monkeypatch.setattr(main, "read_sharepoint_delta", fake_delta)
    monkeypatch.setattr(main, "save_sharepoint_sync_state", lambda *args: saved.append(args))

    main.run_sharepoint_ingestion("Default Rule")

    assert cleared == ["drive-id"]
    assert saved == [("drive-id", "fresh", {}, set())]


def test_sharepoint_tables_extend_existing_config_and_history_db(monkeypatch, tmp_path):
    monkeypatch.setattr(config_db, "DB_PATH", tmp_path / "config.db")
    config_db.init_config_db()

    assert any(item["name"] == "SharePoint" for item in config_db.list_connectors())
    entry = config_db.add_history_entry(
        connector="SharePoint", mapper="Document Mapper", rules="Default Rule",
        outputs="Kafka", processed=1,
    )
    config_db.save_sharepoint_sync_state(
        "drive-id", "delta-link", {"item-id": "guide.json"}, set()
    )

    assert entry["processed"] == 1
    assert config_db.get_sharepoint_delta_link("drive-id") == "delta-link"
    assert config_db.get_sharepoint_item_mappings("drive-id") == {"item-id": "guide.json"}


def test_polling_waits_calls_mongodb_sync_and_retries(monkeypatch):
    calls = []

    async def fake_sleep(seconds):
        calls.append(("sleep", seconds))
        if len([call for call in calls if call[0] == "sleep"]) == 3:
            raise asyncio.CancelledError

    async def fake_mongodb_sync(rule):
        calls.append(("run", rule))
        if len([call for call in calls if call[0] == "run"]) == 1:
            raise RuntimeError("temporary failure")

    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(main, "_run_sharepoint_mongodb_ingestion", fake_mongodb_sync)

    try:
        asyncio.run(main.poll_sharepoint_ingestion())
    except asyncio.CancelledError:
        pass

    assert calls == [
        ("sleep", main.POLL_INTERVAL_SECONDS), ("run", "Knowledge Base Rules"),
        ("sleep", main.POLL_INTERVAL_SECONDS), ("run", "Knowledge Base Rules"),
        ("sleep", main.POLL_INTERVAL_SECONDS),
    ]


def test_automatic_mongodb_sync_persists_accepted_before_state(
    monkeypatch, tmp_path
):
    events = []
    persisted = []
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    delta = {
        "delta_link": "new-delta",
        "changes": [
            {
                "item_id": "accepted-id", "deleted": False, "supported": True,
                "record": {
                    "source": "sharepoint", "item_id": "accepted-id",
                    "file_name": "guide.txt", "content": "guide",
                },
            },
            {
                "item_id": "rejected-id", "deleted": False, "supported": True,
                "record": {
                    "source": "sharepoint", "item_id": "rejected-id",
                    "file_name": "secret.txt", "content": "password: exposed",
                },
            },
        ],
    }
    configure_sync_mocks(monkeypatch, delta)

    async def fake_persist(source, persisted_documents):
        events.append("persist")
        persisted.append((source, persisted_documents))

    monkeypatch.setattr(main, "persist", fake_persist)
    monkeypatch.setattr(
        main, "save_sharepoint_sync_state", lambda *args: events.append("save")
    )

    actual = asyncio.run(
        main._run_sharepoint_mongodb_ingestion("Knowledge Base Rules")
    )

    assert actual == {
        "status": "success", "processed": 2, "rule": "Knowledge Base Rules"
    }
    assert events == ["persist", "save"]
    assert persisted[0][0] == "sharepoint"
    assert [document["document_id"] for document in persisted[0][1]] == [
        "accepted-id"
    ]


def test_automatic_mongodb_sync_failure_does_not_save_state(monkeypatch):
    documents = [{"document_id": "accepted-id", "kb_status": "active"}]
    sync_state = ("drive-id", "must-not-save", {}, set())
    saved = []

    async def fake_to_thread(function, *args):
        if function is main._process_sharepoint_ingestion:
            return ({"status": "success", "processed": 1, "rule": args[0]},
                    documents, sync_state)
        saved.append(args)

    async def failed_persist(source, persisted_documents):
        raise RuntimeError("Mongo unavailable")

    monkeypatch.setattr(main.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(main, "persist", failed_persist)

    try:
        asyncio.run(main._run_sharepoint_mongodb_ingestion("Knowledge Base Rules"))
    except RuntimeError as exc:
        assert str(exc) == "Mongo unavailable"
    else:
        raise AssertionError("Expected Mongo output failure")

    assert saved == []
