import json
from db import get_connection, init_schema, insert_content
from search import (
    keyword_search,
    list_all_content,
    get_content_stats,
    get_similar_content,
    get_top_performers,
)
import pytest


@pytest.fixture
def populated_db(sample_content, sample_content_2):
    """DB with two content items (no vss - keyword/list tests only)."""
    conn = get_connection(":memory:")
    init_schema(conn)
    insert_content(conn, sample_content)
    insert_content(conn, sample_content_2)
    yield conn
    conn.close()


def test_keyword_search_finds_content(populated_db):
    results = keyword_search(populated_db, "cloud migration")
    assert len(results) >= 1
    assert results[0]["title"] == "The Complete Guide to Cloud Migration"


def test_keyword_search_no_results(populated_db):
    results = keyword_search(populated_db, "xyznonexistent")
    assert len(results) == 0


def test_keyword_search_with_filter(populated_db):
    results = keyword_search(populated_db, "guide", filters={"persona": "cto"})
    assert len(results) == 1
    assert results[0]["persona"] == "cto"


def test_keyword_search_with_content_type_filter(populated_db):
    results = keyword_search(populated_db, "guide", filters={"content_type": "whitepaper"})
    assert len(results) == 0


def test_list_all_content(populated_db):
    result = list_all_content(populated_db)
    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["has_more"] is False


def test_list_all_content_with_filters(populated_db):
    result = list_all_content(populated_db, filters={"persona": "developer"})
    assert result["total"] == 1
    assert result["items"][0]["persona"] == "developer"


def test_list_all_content_pagination(populated_db):
    result = list_all_content(populated_db, limit=1, offset=0)
    assert len(result["items"]) == 1
    assert result["total"] == 2
    assert result["has_more"] is True


def test_get_content_stats(populated_db):
    stats = get_content_stats(populated_db)
    assert stats["by_content_type"]["blog"] == 2
    assert stats["by_persona"]["cto"] == 1
    assert stats["by_persona"]["developer"] == 1


def test_get_top_performers(populated_db):
    results = get_top_performers(populated_db, limit=1)
    assert len(results) == 1
    assert results[0]["performance_score"] == 87
