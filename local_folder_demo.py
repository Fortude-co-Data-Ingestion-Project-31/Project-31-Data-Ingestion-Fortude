import json
from pathlib import Path

from local_file_mapper import map_local_files_to_canonical
from local_folder_connector import read_local_text_files


BASE_FOLDER = Path(__file__).parent
INPUT_FOLDER = BASE_FOLDER / "local_data" / "input"
OUTPUT_FOLDER = BASE_FOLDER / "local_data" / "output"


def run_demo():
    INPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    raw_files = read_local_text_files(INPUT_FOLDER)
    canonical_documents = map_local_files_to_canonical(raw_files)

    for document in canonical_documents:
        output_name = Path(document["file_name"]).with_suffix(".json").name
        output_path = OUTPUT_FOLDER / output_name
        output_path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"Processed {len(canonical_documents)} text file(s).")
    print(f"Output folder: {OUTPUT_FOLDER}")


if __name__ == "__main__":
    run_demo()
