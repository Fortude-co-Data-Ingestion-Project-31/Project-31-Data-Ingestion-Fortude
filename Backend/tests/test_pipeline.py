import sqlite3

import pytest

from backend.app.connectors import connectors_db


# setup temp SQLite db for each test
@pytest.fixture
def database(monkeypatch, tmp_path):
    monkeypatch.setattr(connectors_db, "DB_PATH", tmp_path / "config.db")
    connectors_db.init_config_db()
    return connectors_db.DB_PATH


# pipeline schema tests
def test_pipeline_create_table(database):
    """test pipeline table creation"""
    conn = sqlite3.connect(database)

    try:
        row = conn.execute(
            """SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'pipelines'"""
        ).fetchone()
        assert row is not None
    finally:
        conn.close()


@pytest.mark.parametrize("name", ["", "    "])
def test_pipeline_name_not_empty(database, name):
    """test pipeline name validity (cannot be empty or whitespace)"""
    conn = sqlite3.connect(database)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO pipelines (name, connector_id, created_at, updated_at) VALUES (?, ?, ?, ?)""",
                (name, 1, "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00"),
            )
            conn.commit()
    finally:
        conn.close()


def test_pipeline_name_not_unique(database):
    """test preventing duplicate pipeline names"""
    conn = sqlite3.connect(database)

    try:
        conn.execute(
            """INSERT INTO pipelines (name, connector_id, created_at, updated_at) VALUES (?, ?, ?, ?)""",
            ("Pipeline 2", 1, "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO pipelines (name, connector_id, created_at, updated_at) VALUES (?, ?, ?, ?)""",
                (
                    "Pipeline 2",
                    1,
                    "2024-01-01T00:00:00+00:00",
                    "2024-01-01T00:00:00+00:00",
                ),
            )
    finally:
        conn.close()


def test_pipeline_connector_must_exist(database):
    """test preventing insertion of a pipeline with a non-existent connector_id"""
    conn = sqlite3.connect(database)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO pipelines (name, connector_id, created_at, updated_at) VALUES (?, ?, ?, ?)""",
                (
                    "Pipeline 3",
                    32,
                    "2024-01-01T00:00:00+00:00",
                    "2024-01-01T00:00:00+00:00",
                ),
            )
    finally:
        conn.close()


def test_pipeline_delete_successful(database):
    """test deleting a pipeline that is not in use, removing rule/output associations"""
    conn = sqlite3.connect(database)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        cursor = conn.execute(
            """INSERT INTO pipelines (name, connector_id, created_at, updated_at) VALUES (?, ?, ?, ?)""",
            ("Pipeline 4", 1, "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00"),
        )

        pipeline_id = cursor.lastrowid
        conn.execute(
            """INSERT INTO pipeline_rules (pipeline_id, rule_id) VALUES (?, ?)""",
            (pipeline_id, 1),
        )

        conn.execute(
            """INSERT INTO pipeline_outputs (pipeline_id, output_id) VALUES (?, ?)""",
            (pipeline_id, 1),
        )

        conn.commit()

        conn.execute(
            """DELETE FROM pipelines WHERE id = ?""",
            (pipeline_id,),
        )

        conn.commit()

        row = conn.execute(
            """SELECT * FROM pipelines WHERE id = ?""",
            (pipeline_id,),
        ).fetchone()

        assert row is None

        rule_association = conn.execute(
            """SELECT * FROM pipeline_rules WHERE pipeline_id = ?""",
            (pipeline_id,),
        ).fetchone()

        assert rule_association is None

        output_association = conn.execute(
            """SELECT * FROM pipeline_outputs WHERE pipeline_id = ?""",
            (pipeline_id,),
        ).fetchone()

        assert output_association is None

    finally:
        conn.close()


def test_delete_connector_while_in_use(database):
    """test deleting a connector that is in use by a pipeline, should raise an error and prevent the action"""
    conn = sqlite3.connect(database)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        conn.execute(
            """INSERT INTO pipelines (name, connector_id, created_at, updated_at) VALUES (?, ?, ?, ?)""",
            ("Pipeline 5", 1, "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00"),
        )

        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """DELETE FROM connectors WHERE id = ?""",
                (1,),
            )
            conn.commit()

        row = conn.execute(
            """SELECT id FROM connectors WHERE id = ?""",
            (1,),
        ).fetchone()

        assert row is not None

    finally:
        conn.close()


def test_pipeline_has_updated_at(database):
    """test that updated_at field exists in pipeline tables"""
    conn = sqlite3.connect(database)

    try:
        columns = conn.execute("""PRAGMA table_info(pipelines)""").fetchall()

        column_names = [col[1] for col in columns]

        assert "updated_at" in column_names

    finally:
        conn.close()
