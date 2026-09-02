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


class SharePointDeltaStateError(RuntimeError):
    """Raised when Graph no longer accepts a saved delta cursor."""


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


def _resolve_drive(session):
    load_dotenv()
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

    root = _get_json(
        session, f"{GRAPH_BASE_URL}/drives/{drive['id']}/root", headers
    )
    return drive["id"], root["id"], headers


def get_sharepoint_drive_id(session=None):
    """Resolve and return the configured SharePoint document-library drive ID."""
    session = session or requests.Session()
    drive_id, _, _ = _resolve_drive(session)
    return drive_id


def _download_file_record(session, drive_id, headers, item):
    file_name = item.get("name", "")
    file_type = Path(file_name).suffix.lower()
    download_response = session.get(
        f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{item['id']}/content",
        headers=headers,
        timeout=60,
    )
    download_response.raise_for_status()
    return {
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


def read_sharepoint_delta(delta_url=None, session=None):
    """Return direct-root changes and the final cursor for the configured drive."""
    session = session or requests.Session()
    drive_id, root_id, headers = _resolve_drive(session)
    url = delta_url or f"{GRAPH_BASE_URL}/drives/{drive_id}/root/delta"
    latest_by_id = {}
    final_delta_link = None

    while url:
        response = session.get(url, headers=headers, timeout=30)
        if response.status_code in (404, 410) and delta_url:
            raise SharePointDeltaStateError("Saved SharePoint delta cursor is invalid.")
        response.raise_for_status()
        page = response.json()
        for item in page.get("value", []):
            item_id = item.get("id")
            if item_id:
                latest_by_id[item_id] = item
        url = page.get("@odata.nextLink")
        if not url:
            final_delta_link = page.get("@odata.deltaLink")

    if not final_delta_link:
        raise RuntimeError("Microsoft Graph delta response did not include @odata.deltaLink.")

    changes = []
    for item_id, item in latest_by_id.items():
        deleted = "deleted" in item
        file_name = item.get("name", "")
        file_type = Path(file_name).suffix.lower()
        is_direct_root_file = (
            "file" in item
            and (item.get("parentReference") or {}).get("id") == root_id
        )
        supported = is_direct_root_file and file_type in SUPPORTED_FILE_TYPES
        change = {
            "item_id": item_id,
            "deleted": deleted,
            "supported": supported,
            "record": None,
        }
        if supported and not deleted:
            change["record"] = _download_file_record(
                session, drive_id, headers, item
            )
        changes.append(change)

    return {
        "changes": changes,
        "delta_link": final_delta_link,
    }
