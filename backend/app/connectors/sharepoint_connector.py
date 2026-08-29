"""Read supported documents from a SharePoint document library via Graph."""

import os
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import requests
from docx import Document
from dotenv import load_dotenv
from pypdf import PdfReader


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
SUPPORTED_FILE_TYPES = {".txt", ".docx", ".pdf"}


def _required_setting(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_access_token(session, tenant_id, client_id, client_secret):
    response = session.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _get_json(session, url, headers):
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def _get_all_items(session, url, headers):
    items = []
    while url:
        page = _get_json(session, url, headers)
        items.extend(page.get("value", []))
        url = page.get("@odata.nextLink")
    return items


def _extract_content(file_name, file_bytes):
    file_type = Path(file_name).suffix.lower()

    if file_type == ".txt":
        return file_bytes.decode("utf-8-sig")
    if file_type == ".docx":
        document = Document(BytesIO(file_bytes))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    if file_type == ".pdf":
        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    raise ValueError(f"Unsupported file type: {file_type}")


def _author_from_item(item):
    identity = item.get("lastModifiedBy") or item.get("createdBy") or {}
    person = identity.get("user") or identity.get("application") or {}
    return person.get("displayName") or person.get("email") or person.get("id")


def read_sharepoint_files(session=None):
    """Return supported files from the configured library root as raw records."""
    load_dotenv()
    session = session or requests.Session()

    tenant_id = _required_setting("TENANT_ID")
    client_id = _required_setting("CLIENT_ID")
    client_secret = _required_setting("CLIENT_SECRET")
    host = _required_setting("SHAREPOINT_HOST").strip().rstrip("/")
    site_path = _required_setting("SHAREPOINT_SITE_PATH").strip().strip("/")
    library_name = _required_setting("SHAREPOINT_LIBRARY").strip()

    token = _get_access_token(session, tenant_id, client_id, client_secret)
    headers = {"Authorization": f"Bearer {token}"}

    encoded_site_path = quote(site_path, safe="/")
    site = _get_json(
        session,
        f"{GRAPH_BASE_URL}/sites/{host}:/{encoded_site_path}",
        headers,
    )
    drives = _get_all_items(
        session, f"{GRAPH_BASE_URL}/sites/{site['id']}/drives", headers
    )
    drive = next(
        (item for item in drives if item.get("name", "").casefold() == library_name.casefold()),
        None,
    )
    if drive is None:
        raise RuntimeError(f"SharePoint document library not found: {library_name}")

    items = _get_all_items(
        session, f"{GRAPH_BASE_URL}/drives/{drive['id']}/root/children", headers
    )
    raw_file_records = []

    for item in items:
        file_name = item.get("name", "")
        file_type = Path(file_name).suffix.lower()
        if "file" not in item or file_type not in SUPPORTED_FILE_TYPES:
            continue

        download_response = session.get(
            f"{GRAPH_BASE_URL}/drives/{drive['id']}/items/{item['id']}/content",
            headers=headers,
            timeout=60,
        )
        download_response.raise_for_status()
        raw_file_records.append(
            {
                "source": "sharepoint",
                "file_name": file_name,
                "file_type": file_type,
                "file_size": item.get("size"),
                "modified_at": item.get("lastModifiedDateTime"),
                "content": _extract_content(file_name, download_response.content),
                "source_url": item.get("webUrl"),
                "author": _author_from_item(item),
                "version": item.get("eTag") or item.get("cTag"),
            }
        )

    return raw_file_records
