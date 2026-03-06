import sqlite3

from db import get_connection, init_schema, insert_content, get_content_by_id


def test_get_connection_memory():
    conn = get_connection(":memory:")
    assert isinstance(conn, sqlite3.Connection)
    result = conn.execute("PRAGMA journal_mode").fetchone()
    assert result[0] == "wal" or result[0] == "memory"
    conn.close()


def test_init_schema_creates_tables():
    conn = get_connection(":memory:")
    init_schema(conn)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t[0] for t in tables]
    assert "marketing_content" in table_names
    assert "generated_content" in table_names
    conn.close()


def test_init_schema_creates_fts():
    conn = get_connection(":memory:")
    init_schema(conn)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'"
    ).fetchall()
    table_names = [t[0] for t in tables]
    assert any("content_fts" in name for name in table_names)
    conn.close()


def test_insert_and_get_content(db, sample_content):
    from db import init_schema, insert_content, get_content_by_id

    init_schema(db)
    insert_content(db, sample_content)
    result = get_content_by_id(db, sample_content["id"])
    assert result is not None
    assert result["title"] == sample_content["title"]
    assert result["content_type"] == "blog"
    assert result["persona"] == "cto"


def test_insert_content_updates_fts(db, sample_content):
    from db import init_schema, insert_content

    init_schema(db)
    insert_content(db, sample_content)
    rows = db.execute(
        "SELECT rowid FROM content_fts WHERE content_fts MATCH 'cloud migration'"
    ).fetchall()
    assert len(rows) == 1
