"""
Connector, Rule, and Output-Target persistence layer.

Stores configuration items in the same SQLite database used by the auth
module (users.db).  Three tables are created if they do not already exist:

    connectors     – data source connectors
    rules          – transformation / filtering rules
    output_targets – destinations for ingested data

Each table has the same schema:
    id         INTEGER PRIMARY KEY AUTOINCREMENT
    name       TEXT UNIQUE NOT NULL
    created_at TEXT NOT NULL  (ISO-8601 timestamp)

Seed data is inserted on first run so the app starts with a useful set of
defaults.  Subsequent runs are safe — the INSERT OR IGNORE statements are
no-ops when the rows already exist.
"""

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "users.db"

# ---------------------------------------------------------------------------
# Seed data — inserted on first run only (INSERT OR IGNORE)
# ---------------------------------------------------------------------------

_SEED: dict[str, list[str]] = {
    "connectors": ["Infor Sales", "Jira Support", "SharePoint KB"],
    "rules": ["Infor Sales Rules", "L3 Ticket Rules", "Knowledge Base Rules"],
    "output_targets": ["PostgreSQL", "MongoDB", "Kafka", "Vector Database"],
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {"id": row["id"], "name": row["name"], "created_at": row["created_at"]}


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_config_db() -> None:
    """Create config tables and insert seed data if not already present."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        for table in ("connectors", "rules", "output_targets"):
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    name       TEXT    UNIQUE NOT NULL,
                    created_at TEXT    NOT NULL
                )
                """
            )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                connector   TEXT    NOT NULL,
                mapper      TEXT    NOT NULL,
                rules       TEXT    NOT NULL,
                outputs     TEXT    NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'completed',
                processed   INTEGER NOT NULL DEFAULT 0,
                message     TEXT,
                started_at  TEXT    NOT NULL
            )
            """
        )

        conn.commit()

        # Insert seeds — silently skipped if rows already exist.
        for table, names in _SEED.items():
            for name in names:
                cur.execute(
                    f"INSERT OR IGNORE INTO {table} (name, created_at) VALUES (?, ?)",
                    (name, _now_iso()),
                )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Generic CRUD helpers (used by each category)
# ---------------------------------------------------------------------------

def _list_all(table: str) -> list[dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT id, name, created_at FROM {table} ORDER BY id")
        return [_row_to_dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _add_item(table: str, name: str) -> dict[str, Any]:
    """Insert a new item and return its full record.

    Raises:
        ValueError: when a row with the same name already exists.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        try:
            cur.execute(
                f"INSERT INTO {table} (name, created_at) VALUES (?, ?)",
                (name.strip(), _now_iso()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"'{name}' already exists in {table}.")
        row_id = cur.lastrowid
        cur.execute(f"SELECT id, name, created_at FROM {table} WHERE id = ?", (row_id,))
        return _row_to_dict(cur.fetchone())
    finally:
        conn.close()


def _delete_item(table: str, item_id: int) -> bool:
    """Delete an item by primary key.

    Returns:
        True  – row was found and deleted.
        False – no row with that id.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API — Connectors
# ---------------------------------------------------------------------------

def list_connectors() -> list[dict[str, Any]]:
    return _list_all("connectors")


def add_connector(name: str) -> dict[str, Any]:
    return _add_item("connectors", name)


def delete_connector(item_id: int) -> bool:
    return _delete_item("connectors", item_id)


# ---------------------------------------------------------------------------
# Public API — Rules
# ---------------------------------------------------------------------------

def list_rules() -> list[dict[str, Any]]:
    return _list_all("rules")


def add_rule(name: str) -> dict[str, Any]:
    return _add_item("rules", name)


def delete_rule(item_id: int) -> bool:
    return _delete_item("rules", item_id)


# ---------------------------------------------------------------------------
# Public API — Output Targets
# ---------------------------------------------------------------------------

def list_outputs() -> list[dict[str, Any]]:
    return _list_all("output_targets")


def add_output(name: str) -> dict[str, Any]:
    return _add_item("output_targets", name)


def delete_output(item_id: int) -> bool:
    return _delete_item("output_targets", item_id)


# ---------------------------------------------------------------------------
# Public API — Ingestion History
# ---------------------------------------------------------------------------

def add_history_entry(
    connector: str,
    mapper: str,
    rules: str,
    outputs: str,
    status: str = "completed",
    processed: int = 0,
    message: str | None = None,
) -> dict[str, Any]:
    """Insert a new ingestion history record and return it."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        started_at = _now_iso()
        cur.execute(
            """
            INSERT INTO ingestion_history
                (connector, mapper, rules, outputs, status, processed, message, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (connector, mapper, rules, outputs, status, processed, message, started_at),
        )
        conn.commit()
        row_id = cur.lastrowid
        cur.execute("SELECT * FROM ingestion_history WHERE id = ?", (row_id,))
        row = cur.fetchone()
        return dict(row)
    finally:
        conn.close()


def list_history(limit: int = 100) -> list[dict[str, Any]]:
    """Return the most recent ingestion history entries, newest first."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM ingestion_history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def delete_history_entry(entry_id: int) -> bool:
    """Delete a history entry by id. Returns True if deleted."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ingestion_history WHERE id = ?", (entry_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
