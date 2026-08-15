"""
Main FastAPI application for the demo project.

This module wires up HTTP endpoints used by the frontend and by local
ingestion utilities. It intentionally keeps logic small and delegates
authentication and storage responsibilities to `backend.app.auth`.

Endpoints include:
- local ingestion: `/api/ingest/local-folder`
- authentication: `/api/auth/*` for register/login/mfa

The file also demonstrates a simple startup hook that initializes the
SQLite-backed auth DB.
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from local_file_mapper import map_local_files_to_canonical
from local_folder_connector import read_local_text_files
from backend.app.rules.rule_handlers import apply_selected_rules
from backend.app import auth
import sqlite3


BASE_FOLDER = Path(__file__).resolve().parents[2]
INPUT_FOLDER = BASE_FOLDER / "local_data" / "input"
OUTPUT_FOLDER = BASE_FOLDER / "local_data" / "output"

app = FastAPI()

# Configure CORS and general app behavior. The demo frontend runs on a
# separate Vite dev server so these origins are allowed for local dev.




class IngestionRequest(BaseModel):
    connector: str
    rule: str | None = None

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


@app.on_event("startup")
def startup_event():
    try:
        auth.init_db()
    except Exception:
        # If DB init fails, allow app to continue but log nothing here
        pass


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.post("/api/ingest/local-folder")
def ingest_local_folder(request: IngestionRequest):
    """
    Ingest local text files into canonical JSON documents.

    This endpoint is a small demo that reads text files from the
    configured `local_data/input` folder, maps them to canonical
    document structures, applies a selected rule, and writes the JSON
    output to `local_data/output`.
    """
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
        document = apply_selected_rules(document, request.rule or "Default Rule")
        output_name = Path(document["file_name"]).with_suffix(".json").name
        output_path = OUTPUT_FOLDER / output_name
        output_path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return {
        "status": "success",
        "processed": len(canonical_documents),
        "rule": request.rule or "Default Rule",
    }


@app.post("/api/auth/register")
def register(payload: dict):
    """
    Register a new user account.

    Expects `username` and `password` in the JSON payload. On success
    returns an initial token so the client can auto-login.
    """
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        auth.register_user(username, password)
        token = auth.create_token(username)
        return {"status": "ok", "username": username, "token": token}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login")
def login(payload: dict):
    """
    Authenticate a user's credentials.

    If the user has MFA enabled the endpoint returns a short-lived
    `tmp_token` which the client must exchange by completing MFA. If
    MFA is not enabled (or the user is an admin) a session token is
    returned directly.
    """
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")

    if auth.verify_user(username, password):
        if not auth.is_admin(username):
            # Require MFA only if user has it enabled
            if auth.is_mfa_enabled(username):
                tmp = auth.create_token_with_type(username, ttl=300, token_type="mfa")
                return {"mfa_required": True, "tmp_token": tmp}
            # MFA not enabled for this user: issue session token directly
            token = auth.create_token_with_type(username, ttl=3600, token_type="session")
            return {"authenticated": True, "username": username, "token": token}
        token = auth.create_token_with_type(username, ttl=3600, token_type="session")
        return {"authenticated": True, "username": username, "token": token}
    raise HTTPException(status_code=401, detail="invalid credentials")


@app.post("/api/auth/verify")
def verify_token(payload: dict):
    """
    Verify a session token and return the associated username.

    Used by the frontend to confirm the current token is valid.
    """
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    username = auth.verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return {"username": username}


@app.post("/api/auth/mfa/setup")
def mfa_setup(payload: dict):
    """
    Begin MFA setup for a logged-in user.

    The client provides a valid session `token`. The server generates
    a new base32 secret, stores it for the user and returns an
    `otpauth_url` which the UI can display as a QR code for scanning by
    an authenticator app.
    """
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    username = auth.verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="invalid or expired token")

    secret = auth.generate_mfa_secret()
    auth.set_mfa_secret(username, secret)
    issuer = "Fortude"
    otpauth = auth.generate_otpauth_url(secret, username, issuer)
    return {"secret": secret, "otpauth_url": otpauth}


@app.post("/api/auth/mfa/verify")
def mfa_verify(payload: dict):
    """
    Complete MFA setup by verifying the TOTP code from the user's app.

    Requires the session `token` used to start setup and the `code`.
    On success the user's `mfa_enabled` flag is turned on.
    """
    token = payload.get("token")
    code = payload.get("code")
    if not token or not code:
        raise HTTPException(status_code=400, detail="token and code required")
    username = auth.verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="invalid or expired token")

    secret = auth.get_mfa_secret(username)
    if not secret:
        raise HTTPException(status_code=400, detail="mfa not setup")

    if not auth.verify_totp(secret, str(code)):
        raise HTTPException(status_code=401, detail="invalid mfa code")

    auth.enable_mfa(username)
    return {"status": "ok"}


@app.post("/api/auth/mfa/login")
def mfa_login(payload: dict):
    """
    Verify a user-provided TOTP code during login.

    The client provides the `tmp_token` obtained from `/api/auth/login`
    and the TOTP `code`. If the code is valid we delete the temporary
    token and issue a session token.
    """
    tmp_token = payload.get("tmp_token")
    code = payload.get("code")
    if not tmp_token or not code:
        raise HTTPException(status_code=400, detail="tmp_token and code required")

    username = auth.verify_token_with_type(tmp_token, expected_type="mfa")
    if not username:
        raise HTTPException(status_code=401, detail="invalid or expired mfa token")

    secret = auth.get_mfa_secret(username)
    if not secret:
        raise HTTPException(status_code=400, detail="mfa not setup")

    if not auth.verify_totp(secret, str(code)):
        raise HTTPException(status_code=401, detail="invalid mfa code")

    auth.delete_token(tmp_token)
    token = auth.create_token_with_type(username, ttl=3600, token_type="session")
    return {"authenticated": True, "username": username, "token": token}



@app.post("/api/auth/change")
def change_user(payload: dict):
    """
    Update a user's username and/or password.

    The endpoint requires a valid session `token` and the user's
    current password (`old_password`) to prevent unauthorized changes.
    """
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    username = auth.verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    # Require the user's current password to verify identity
    old_password = payload.get("old_password")
    if not old_password:
        raise HTTPException(status_code=400, detail="old_password required")

    # verify old password
    if not auth.verify_user(username, old_password):
        raise HTTPException(status_code=401, detail="invalid current password")

    new_username = payload.get("new_username")
    new_password = payload.get("new_password")

    if not new_username and not new_password:
        raise HTTPException(status_code=400, detail="new_username or new_password required")

    try:
        auth.update_user(username, new_username=new_username, new_password=new_password)
        return {"status": "ok", "username": new_username or username}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
