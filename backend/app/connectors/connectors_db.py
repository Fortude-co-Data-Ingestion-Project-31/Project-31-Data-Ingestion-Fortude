"""
Connector, Rule, and Output-Target persistence layer.

Stores configuration items in the same SQLite database used by the auth
module (users.db). Three tables are created if they do not already exist:

    connectors     - data source connectors
    rules          - transformation / filtering rules
    output_targets - destinations for ingested data

Each table has the same schema:
    id         INTEGER PRIMARY KEY AUTOINCREMENT
    name       TEXT UNIQUE NOT NULL
    created_at TEXT NOT NULL  (ISO-8601 timestamp)

Seed data is inserted on first run so the app starts with a useful set of
defaults.  Subsequent runs are safe - the INSERT OR IGNORE statements are
no-ops when the rows already exist.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "users.db"

# ---------------------------------------------------------------------------
# Seed data - inserted on first run only (INSERT OR IGNORE)
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
    conn.execute("PRAGMA foreign_keys = ON") #enable foreign key constraints
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {"id": row["id"], "name": row["name"], "created_at": row["created_at"]}


# ---------------------------------------------------------------------------
# SQLite Database Initialisation
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
                    name       TEXT    UNIQUE NOT NULL (length(trim(name)) > 0),
                    created_at TEXT    NOT NULL
                )
                """
            )

        # Pipelines table
        """
        - each pipeline references exactly one existing connector
        - connectors cannot be deleted while in use
        """
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pipelines (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT UNIQUE NOT NULL CHECK (length(trim(name)) > 0),
                connector_id INTEGER NOT NULL REFERENCES connectors(id) ON DELETE RESTRICT,
                created_at   TEXT NOT NULL
            )
            """
        )
        
        # Associations table for pipeline -> rules/outputs
        """
        - each pipeline may reference one or more rules and one or more output targets
        - deleting a pipeline automatically removes all associations
        - rules/outputs cannot be deleted while in use
        """
        for table, column, target in (
            ("pipeline_rules", "rule_id", "rules"),
            ("pipeline_outputs", "output_id", "output_targets"),
        ):
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    pipeline_id INTEGER NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
                    {column} INTEGER NOT NULL REFERENCES {target}(id) ON DELETE RESTRICT,
                    PRIMARY KEY (pipeline_id, {column})
                )
                """
            )

        # Ingestion history table
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

        # SharePoint delta state table
        # stores last known Microsoft Graph delta link (token to retrieve changes since last sync) for each SharePoint file
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sharepoint_delta_state (
                drive_id   TEXT PRIMARY KEY,
                delta_link TEXT NOT NULL
            )
            """
        )

        # SharePoint item state table
        # stores mapping for each SharePoint file to its output file
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sharepoint_item_state (
                drive_id        TEXT NOT NULL,
                item_id         TEXT NOT NULL,
                output_filename TEXT NOT NULL,
                PRIMARY KEY (drive_id, item_id)
            )
            """
        )

        conn.commit()

        # Insert seed data into database
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
# Generic CRUD helpers (used by connectors, rules, and output targets)
# ---------------------------------------------------------------------------

def _list_all(table: str) -> list[dict[str, Any]]:
    """Return all items from a table in the database as a list of dicts

    Output: rows in table with keys = id, name, created_at (list of dicts)
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT id, name, created_at FROM {table} ORDER BY id")
        return [_row_to_dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _add_item(table: str, name: str) -> dict[str, Any]:
    """Insert a new item into the specified table

    Output: inserted row (dict)
    Raises:
        ValueError: when a row with the same name already exists
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

        # handle duplicate name entry
        except sqlite3.IntegrityError:
            raise ValueError(f"'{name}' already exists in {table}.")
        
        row_id = cur.lastrowid
        cur.execute(f"SELECT id, name, created_at FROM {table} WHERE id = ?", (row_id,))
        return _row_to_dict(cur.fetchone())
    finally:
        conn.close()


def _delete_item(table: str, item_id: int) -> bool:
    """Delete an item using its primary key (item_id)

    Output: (bool)
        True  -> item was found and deleted
        False -> no item with that item_id
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
# Public API - Connectors
# ---------------------------------------------------------------------------

def list_connectors() -> list[dict[str, Any]]:
    """Return all connectors in the database as a list of dicts"""
    return _list_all("connectors")


def add_connector(name: str) -> dict[str, Any]:
    """Add a new connector to the database and return it as a dict"""
    return _add_item("connectors", name)


def delete_connector(item_id: int) -> bool:
    """Delete a connector by id, return True if deleted and False if not found"""
    return _delete_item("connectors", item_id)


# ---------------------------------------------------------------------------
# Public API - Rules
# ---------------------------------------------------------------------------

def list_rules() -> list[dict[str, Any]]:
    """Return all rules in the database as a list of dicts"""
    return _list_all("rules")


def add_rule(name: str) -> dict[str, Any]:
    """Add a new rule to the database and return it as a dict"""
    return _add_item("rules", name)


def delete_rule(item_id: int) -> bool:
    """Delete a rule by id, return True if deleted and False if not found"""
    return _delete_item("rules", item_id)


# ---------------------------------------------------------------------------
# Public API - Output Targets
# ---------------------------------------------------------------------------

def list_outputs() -> list[dict[str, Any]]:
    """Return all output targets in the database as a list of dicts"""
    return _list_all("output_targets")


def add_output(name: str) -> dict[str, Any]:
    """Add a new output target to the database and return it as a dict"""
    return _add_item("output_targets", name)


def delete_output(item_id: int) -> bool:
    """Delete an output target by id, return True if deleted and False if not found"""
    return _delete_item("output_targets", item_id)


# ---------------------------------------------------------------------------
# Public API - Ingestion History
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
    """Creates a new ingestion history record describing a completed pipeline ingestion run

    Input:
        connector: name of connector used
        mapper:    name of mapper used
        rules:     comma-separated list of rules applied
        outputs:   comma-separated list of outputs written to
        status:    completion status of ingestion -> 'completed' (default) or 'failed'
        processed: number of items processed   -> 0 (default) or positive integer
        message:   optional message / error info

    Output: inserted record (dict)
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        started_at = _now_iso() #record time entry was created
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
    """Return the most recent (default = last 100) ingestion history entries, newest first as a list of dicts"""
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
    """Delete an ingestion history entry by id, return True if deleted and False if not found"""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ingestion_history WHERE id = ?", (entry_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API - SharePoint delta synchronization state
# This is used to track the SharePoint synchronisation between runs to avoid
# reprocessing unchanged files
# ---------------------------------------------------------------------------

def get_sharepoint_delta_link(drive_id: str) -> str | None:
    """Identifies the last completed SharePoint synchronisation state for a given drive
    
    Input:   unique identifier for the SharePoint drive (str)
    Output: (str)
        last known delta link -> if drive found
        None                  -> no drive with that drive_id
    """
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT delta_link FROM sharepoint_delta_state WHERE drive_id = ?",
            (drive_id,),
        ).fetchone()
        return row["delta_link"] if row else None
    finally:
        conn.close()


def clear_sharepoint_delta_link(drive_id: str) -> None:
    """Deletes the last known SharePoint synchronisation state for a given drive
    
    Input:  unique identifier for the SharePoint drive (str)
    Output: None
    """
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM sharepoint_delta_state WHERE drive_id = ?", (drive_id,))
        conn.commit()
    finally:
        conn.close()


def get_sharepoint_item_mappings(drive_id: str) -> dict[str, str]:
    """Retrieves the item and output file mappings for a given drive
    
    Input:  unique identifier for the SharePoint drive (str)
    Output: mapping of items and output filenames (list of dicts)
    """
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT item_id, output_filename FROM sharepoint_item_state WHERE drive_id = ?",
            (drive_id,),
        ).fetchall()
        return {row["item_id"]: row["output_filename"] for row in rows}
    finally:
        conn.close()


def save_sharepoint_sync_state(
    drive_id: str,
    delta_link: str,
    mapping_upserts: dict[str, str],
    mapping_deletes: set[str],
) -> None:
    """
    Save the completed SharePoint synchronisation state for a given drive, including the last known delta link and the item/output file mappings.
    Input:
        drive_id:        unique identifier of SharePoint drive to be synced (str)
        delta_link:      last known delta link for the drive (str)
        mapping_upserts: item_id <-> output_filename mappings to add or update (list of dicts)
        mapping_deletes: item_ids to delete from the mapping (set of str)

    Output: None
    """
    conn = _get_conn()
    try:
        # remove old mappings no longer present in the SharePoint drive from local database
        for item_id in mapping_deletes:
            conn.execute(
                "DELETE FROM sharepoint_item_state WHERE drive_id = ? AND item_id = ?",
                (drive_id, item_id),
            )

        # update existing mappings or insert new mappings
        # upsert = insert if it doesn't exist, update if it does
        for item_id, output_filename in mapping_upserts.items():
            conn.execute(
                """
                INSERT INTO sharepoint_item_state (drive_id, item_id, output_filename)
                VALUES (?, ?, ?)
                ON CONFLICT(drive_id, item_id)
                DO UPDATE SET output_filename = excluded.output_filename
                """,
                (drive_id, item_id, output_filename),
            )
        
        # save/overwrite new delta link for the drive
        conn.execute(
            """
            INSERT INTO sharepoint_delta_state (drive_id, delta_link)
            VALUES (?, ?)
            ON CONFLICT(drive_id) DO UPDATE SET delta_link = excluded.delta_link
            """,
            (drive_id, delta_link),
        )
        conn.commit()
    finally:
        conn.close()
