from pathlib import Path


def read_local_text_files(input_folder):
    """Read .txt files from `input_folder` and return a list of file records.

    Each record contains file metadata and the UTF-8 decoded content.
    """
    raw_file_records = []

    for file_path in sorted(Path(input_folder).iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() != ".txt":
            continue

        file_details = file_path.stat()
        raw_file_record = {
            "file_name": file_path.name,
            "file_type": file_path.suffix.lower(),
            "file_size": file_details.st_size,
            "modified_at": file_details.st_mtime,
            "content": file_path.read_text(encoding="utf-8"),
        }
        raw_file_records.append(raw_file_record)

    return raw_file_records
