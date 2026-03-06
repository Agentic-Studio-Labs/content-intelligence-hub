import uuid
from db import get_connection, init_schema, insert_content
from generated import (
    save_generated_content,
    get_generated_by_id,
    list_generated_content,
    keyword_search_generated,
    get_generated_stats,
)
import pytest


@pytest.fixture
def gen_db(sample_content):
    conn = get_connection(":memory:")
    init_schema(conn)
    insert_content(conn, sample_content)
    yield conn
    conn.close()


def test_save_and_get_generated(gen_db, sample_content):
    gen_id = save_generated_content(
        gen_db,
        source_content_id=sample_content["id"],
        source_title=sample_content["title"],
        format="linkedin",
        tone="professional",
        body="Exciting insights about cloud migration...",
        quality_score=0.85,
        prompts={"general": "repurpose this", "format": "linkedin style"},
    )
    assert gen_id is not None
    result = get_generated_by_id(gen_db, gen_id)
    assert result["format"] == "linkedin"
    assert result["tone"] == "professional"
    assert result["quality_score"] == 0.85


def test_list_generated(gen_db, sample_content):
    for fmt in ["linkedin", "email", "twitter"]:
        save_generated_content(
            gen_db,
            source_content_id=sample_content["id"],
            source_title=sample_content["title"],
            format=fmt,
            tone="professional",
            body=f"Generated {fmt} content about cloud...",
        )
    result = list_generated_content(gen_db)
    assert result["total"] == 3
    assert len(result["items"]) == 3


def test_list_generated_with_format_filter(gen_db, sample_content):
    for fmt in ["linkedin", "email"]:
        save_generated_content(
            gen_db,
            source_content_id=sample_content["id"],
            source_title=sample_content["title"],
            format=fmt,
            tone="professional",
            body=f"Generated {fmt} content...",
        )
    result = list_generated_content(gen_db, filters={"format": "linkedin"})
    assert result["total"] == 1
    assert result["items"][0]["format"] == "linkedin"


def test_keyword_search_generated(gen_db, sample_content):
    save_generated_content(
        gen_db,
        source_content_id=sample_content["id"],
        source_title=sample_content["title"],
        format="linkedin",
        tone="professional",
        body="Cloud migration is transforming enterprises worldwide.",
    )
    results = keyword_search_generated(gen_db, "cloud migration")
    assert len(results) >= 1


def test_get_generated_stats(gen_db, sample_content):
    for fmt, tone in [("linkedin", "professional"), ("email", "casual"), ("email", "professional")]:
        save_generated_content(
            gen_db,
            source_content_id=sample_content["id"],
            source_title=sample_content["title"],
            format=fmt,
            tone=tone,
            body=f"Content in {fmt} {tone}...",
        )
    stats = get_generated_stats(gen_db)
    assert stats["by_format"]["email"] == 2
    assert stats["by_format"]["linkedin"] == 1
    assert stats["by_tone"]["professional"] == 2
