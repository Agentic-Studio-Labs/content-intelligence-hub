import json
import sqlite3
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from db import init_schema


@pytest.fixture
def client():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    init_schema(conn)

    with patch("api.EmbeddingModel") as mock_embed_cls, patch("api._init_vss"):
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = [0.1] * 384
        mock_embed_cls.return_value = mock_embed

        import api

        api._conn = conn
        api._embedding_model = None

        from api import app

        with TestClient(app) as c:
            yield c

        api._conn = None
        api._embedding_model = None
    conn.close()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_content_empty(client):
    response = client.get("/api/content")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_search_content(client):
    response = client.post("/api/content/search", json={"query": "cloud migration"})
    assert response.status_code == 200
    assert "items" in response.json()


def test_get_content_not_found(client):
    response = client.get("/api/content/nonexistent-id")
    assert response.status_code == 404


def test_get_content_stats(client):
    response = client.get("/api/content/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


def test_list_generated_empty(client):
    response = client.get("/api/generated")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_settings_get(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "anthropic_api_key_set" in data
    assert "watched_folders" in data


def test_watched_folders_hydrated_from_db_on_startup(tmp_path, monkeypatch):
    """app_settings row is merged into in-process settings when the app starts."""
    from config import settings

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "watched_folders", [])
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    init_schema(conn)
    conn.execute(
        "INSERT OR REPLACE INTO app_settings (key, value) VALUES ('watched_folders', ?)",
        (json.dumps([str(watch_dir)]),),
    )
    conn.commit()

    with patch("api.EmbeddingModel") as mock_embed_cls, patch("api._init_vss"):
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = [0.1] * 384
        mock_embed_cls.return_value = mock_embed

        import api

        api._conn = conn
        api._embedding_model = None

        from api import app

        with TestClient(app) as c:
            response = c.get("/api/settings")
            assert response.status_code == 200
            folders = response.json()["watched_folders"]
            assert str(watch_dir) in folders

        api._conn = None
        api._embedding_model = None
    conn.close()
