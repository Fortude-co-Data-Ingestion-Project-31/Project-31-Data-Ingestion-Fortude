from datetime import datetime, timezone
from pathlib import Path


def map_local_file_to_canonical(raw_file):
    file_name = raw_file.get("file_name")
    modified_at = raw_file.get("modified_at")
    if isinstance(modified_at, (int, float)):
        modified_at = datetime.fromtimestamp(modified_at, timezone.utc).isoformat()

    canonical_document = {
        "source": raw_file.get("source", "local_folder"),
        "document_id": file_name,
        "title": Path(file_name).stem,
        "file_name": file_name,
        "file_type": raw_file.get("file_type"),
        "file_size": raw_file.get("file_size"),
        "modified_at": modified_at,
        "author": raw_file.get("author"),
        "tags": [],
        "source_url": raw_file.get("source_url"),
        "version": raw_file.get("version"),
        "view_count": None,
        "content": raw_file.get("content"),
    }

    return canonical_document


def map_local_files_to_canonical(raw_files):
    canonical_documents = []

    for raw_file in raw_files:
        canonical_document = map_local_file_to_canonical(raw_file)
        canonical_documents.append(canonical_document)

    return canonical_documents
