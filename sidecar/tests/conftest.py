import pytest
import sqlite3
import json


@pytest.fixture
def db():
    """In-memory SQLite database (no extensions - use db_with_vss for vector tests)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    yield conn
    conn.close()


@pytest.fixture
def sample_content():
    """Sample marketing content record."""
    return {
        "id": "test-uuid-0001",
        "title": "The Complete Guide to Cloud Migration",
        "body": "Cloud migration has become essential for modern enterprises. "
        "This guide covers strategy, planning, execution, and optimization. "
        "Key topics include lift-and-shift, re-platforming, and cloud-native approaches.",
        "summary": "A comprehensive roadmap for CTOs planning cloud migration.",
        "content_type": "blog",
        "persona": "cto",
        "funnel_stage": "consideration",
        "channel": "website",
        "topics": json.dumps(["cloud_migration", "digital_transformation"]),
        "performance_score": 87,
        "url": "https://example.com/blog/cloud-migration",
        "created_at": "2025-02-15T10:00:00Z",
    }


@pytest.fixture
def sample_content_2():
    """Second sample content for testing search/comparison."""
    return {
        "id": "test-uuid-0002",
        "title": "DevOps Best Practices for Engineering Teams",
        "body": "DevOps transforms how engineering teams deliver software. "
        "CI/CD pipelines, infrastructure as code, and monitoring are foundational. "
        "This article covers practical implementation strategies.",
        "summary": "Practical DevOps implementation guide for engineering leaders.",
        "content_type": "blog",
        "persona": "developer",
        "funnel_stage": "awareness",
        "channel": "website",
        "topics": json.dumps(["devops", "engineering"]),
        "performance_score": 72,
        "url": "https://example.com/blog/devops-practices",
        "created_at": "2025-03-01T14:00:00Z",
    }


@pytest.fixture
def mock_embedding():
    """Fixed 384-dim embedding for testing."""
    return [0.1] * 384


@pytest.fixture
def mock_embedding_2():
    """Different 384-dim embedding for testing similarity."""
    return [0.2] * 384
