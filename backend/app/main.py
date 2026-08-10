import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from local_file_mapper import map_local_files_to_canonical
from local_folder_connector import read_local_text_files


BASE_FOLDER = Path(__file__).resolve().parents[2]
INPUT_FOLDER = BASE_FOLDER / "local_data" / "input"
OUTPUT_FOLDER = BASE_FOLDER / "local_data" / "output"

app = FastAPI()


class IngestionRequest(BaseModel):
    connector: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.post("/api/ingest/local-folder")
def ingest_local_folder(request: IngestionRequest):
    if request.connector != "SharePoint KB":
        raise HTTPException(
            status_code=400,
            detail=f"Connector '{request.connector}' is not implemented by this endpoint.",
        )

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

    return {"status": "success", "processed": len(canonical_documents)}
