from io import BytesIO

from docx import Document

from backend.app.connectors.sharepoint_connector import read_sharepoint_files


class FakeResponse:
    def __init__(self, json_data=None, content=b""):
        self._json_data = json_data
        self.content = content

    def json(self):
        return self._json_data

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, docx_bytes):
        self.docx_bytes = docx_bytes

    def post(self, url, data, timeout):
        assert data["scope"] == "https://graph.microsoft.com/.default"
        assert data["grant_type"] == "client_credentials"
        return FakeResponse({"access_token": "token"})

    def get(self, url, headers, timeout):
        assert headers == {"Authorization": "Bearer token"}
        if "/sites/example.sharepoint.com:/sites/team" in url:
            return FakeResponse({"id": "site-id"})
        if url.endswith("/sites/site-id/drives"):
            return FakeResponse({"value": [{"id": "drive-id", "name": "Documents"}]})
        if url.endswith("/drives/drive-id/root/children"):
            return FakeResponse(
                {
                    "value": [
                        {
                            "id": "txt-id",
                            "name": "notes.txt",
                            "file": {},
                            "size": 5,
                            "lastModifiedDateTime": "2026-08-24T01:02:03Z",
                            "webUrl": "https://example/notes.txt",
                            "lastModifiedBy": {"user": {"displayName": "A User"}},
                            "eTag": '"version-1"',
                        },
                        {"id": "docx-id", "name": "report.docx", "file": {}},
                        {"id": "ignored-id", "name": "image.png", "file": {}},
                        {"id": "folder-id", "name": "Folder", "folder": {}},
                    ]
                }
            )
        if url.endswith("/items/txt-id/content"):
            return FakeResponse(content=b"hello")
        if url.endswith("/items/docx-id/content"):
            return FakeResponse(content=self.docx_bytes)
        raise AssertionError(f"Unexpected URL: {url}")


def test_read_sharepoint_files(monkeypatch):
    settings = {
        "TENANT_ID": "tenant",
        "CLIENT_ID": "client",
        "CLIENT_SECRET": "secret",
        "SHAREPOINT_HOST": "example.sharepoint.com",
        "SHAREPOINT_SITE_PATH": "/sites/team/",
        "SHAREPOINT_LIBRARY": "documents",
    }
    for name, value in settings.items():
        monkeypatch.setenv(name, value)

    buffer = BytesIO()
    document = Document()
    document.add_paragraph("Document text")
    document.save(buffer)

    records = read_sharepoint_files(session=FakeSession(buffer.getvalue()))

    assert [record["file_name"] for record in records] == ["notes.txt", "report.docx"]
    assert records[0] == {
        "source": "sharepoint",
        "file_name": "notes.txt",
        "file_type": ".txt",
        "file_size": 5,
        "modified_at": "2026-08-24T01:02:03Z",
        "content": "hello",
        "source_url": "https://example/notes.txt",
        "author": "A User",
        "version": '"version-1"',
    }
    assert records[1]["content"] == "Document text"
