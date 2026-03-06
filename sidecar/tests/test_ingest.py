import os
import json
import tempfile
from pathlib import Path
from sources.base import ContentSource, RawContent
from sources.local_files import LocalFileSource
from ingest import ingest_file, ingest_directory
from db import get_connection, init_schema
from unittest.mock import MagicMock
import pytest


def test_raw_content_creation():
    rc = RawContent(
        path="/tmp/test.md",
        title="Test",
        body="Hello world",
        content_type="blog",
        metadata={},
    )
    assert rc.title == "Test"
    assert rc.body == "Hello world"


def test_local_file_source_markdown(tmp_path):
    md_file = tmp_path / "test-post.md"
    md_file.write_text("# My Blog Post\n\nThis is the body of my blog post about cloud migration.")
    source = LocalFileSource()
    result = source.extract(str(md_file))
    assert result is not None
    assert result.title == "My Blog Post"
    assert "cloud migration" in result.body


def test_local_file_source_plain_text(tmp_path):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Some plain text content about DevOps practices.")
    source = LocalFileSource()
    result = source.extract(str(txt_file))
    assert result is not None
    assert "DevOps" in result.body


def test_local_file_source_unsupported(tmp_path):
    img = tmp_path / "photo.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0")
    source = LocalFileSource()
    result = source.extract(str(img))
    assert result is None


def test_ingest_file_into_db(tmp_path):
    md_file = tmp_path / "cloud-guide.md"
    md_file.write_text("# Cloud Guide\n\nCloud migration strategies for enterprises.")
    conn = get_connection(":memory:")
    init_schema(conn)
    mock_embed = MagicMock()
    mock_embed.embed_text.return_value = [0.1] * 384

    result = ingest_file(conn, str(md_file), mock_embed)
    assert result is not None
    assert result["title"] == "Cloud Guide"

    row = conn.execute("SELECT * FROM marketing_content WHERE source_path = ?", (str(md_file),)).fetchone()
    assert row is not None


def test_ingest_directory(tmp_path):
    (tmp_path / "post1.md").write_text("# Post One\n\nFirst post content.")
    (tmp_path / "post2.md").write_text("# Post Two\n\nSecond post content.")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")

    conn = get_connection(":memory:")
    init_schema(conn)
    mock_embed = MagicMock()
    mock_embed.embed_text.return_value = [0.1] * 384

    results = ingest_directory(conn, str(tmp_path), mock_embed)
    assert len(results) == 2
    total = conn.execute("SELECT COUNT(*) FROM marketing_content").fetchone()[0]
    assert total == 2
