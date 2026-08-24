import asyncio
import json

from backend.app import main


def test_manual_ingestion_uses_shared_function(monkeypatch):
    calls = []

    def fake_run(rule):
        calls.append(rule)
        return {"status": "success", "processed": 2, "rule": rule}

    monkeypatch.setattr(main, "run_sharepoint_ingestion", fake_run)

    result = main.ingest_local_folder(
        main.IngestionRequest(connector="SharePoint KB", rule="Knowledge Base Rules")
    )

    assert calls == ["Knowledge Base Rules"]
    assert result == {
        "status": "success",
        "processed": 2,
        "rule": "Knowledge Base Rules",
    }


def test_shared_ingestion_writes_mapped_documents(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_FOLDER", tmp_path)
    monkeypatch.setattr(main, "read_sharepoint_files", lambda: [{"raw": True}])
    monkeypatch.setattr(
        main,
        "map_local_files_to_canonical",
        lambda raw_files: [{"file_name": "guide.txt", "tags": []}],
    )
    monkeypatch.setattr(
        main,
        "apply_selected_rules",
        lambda document, rule: {**document, "rule_applied": rule},
    )

    result = main.run_sharepoint_ingestion("Knowledge Base Rules")

    assert result["processed"] == 1
    written = json.loads((tmp_path / "guide.json").read_text(encoding="utf-8"))
    assert written["rule_applied"] == "Knowledge Base Rules"


def test_polling_waits_then_logs_failure_and_retries(monkeypatch):
    calls = []

    async def fake_sleep(seconds):
        calls.append(("sleep", seconds))
        if len([call for call in calls if call[0] == "sleep"]) == 3:
            raise asyncio.CancelledError

    async def fake_to_thread(function, rule):
        calls.append(("run", rule))
        if len([call for call in calls if call[0] == "run"]) == 1:
            raise RuntimeError("temporary failure")

    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(main.asyncio, "to_thread", fake_to_thread)

    try:
        asyncio.run(main.poll_sharepoint_ingestion())
    except asyncio.CancelledError:
        pass

    assert calls == [
        ("sleep", 300),
        ("run", "Knowledge Base Rules"),
        ("sleep", 300),
        ("run", "Knowledge Base Rules"),
        ("sleep", 300),
    ]
