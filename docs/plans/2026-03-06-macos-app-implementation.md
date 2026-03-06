# Content Intelligence Hub - macOS App Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a native macOS desktop app (Electron + React + Python sidecar) that ports the Content Intelligence Hub from Streamlit, with local-first architecture (SQLite, local embeddings, Anthropic API).

**Architecture:** Electron main process spawns a Python FastAPI sidecar on localhost:8420. React frontend communicates via REST. SQLite + sqlite-vss for storage/vector search, FTS5 for keyword search, sentence-transformers (all-MiniLM-L6-v2, 384-dim) for local embeddings, Anthropic Claude for LLM features via LangGraph agents.

**Tech Stack:** Electron, electron-vite, React 18, TypeScript, TailwindCSS, shadcn/ui, @tanstack/react-table, Python 3.12+, FastAPI, LangGraph, langchain-anthropic, sentence-transformers, SQLite, sqlite-vss, FTS5

---

## Porting Reference

Source: `/Users/jm/Projects/Content-Intelligence-Hub-Demo/src/`

| Source File | Target File | Key Changes |
|---|---|---|
| `search.py` | `sidecar/search.py` | PostgreSQL → SQLite + FTS5 + sqlite-vss, hybrid merge in Python |
| `generated.py` | `sidecar/generated.py` | PostgreSQL → SQLite |
| `embeddings.py` | `sidecar/embeddings.py` | Voyage AI (512d) → sentence-transformers (384d, local) |
| `agents/repurpose_agent.py` | `sidecar/agents/repurpose_agent.py` | Same LangGraph structure |
| `agents/tools.py` | `sidecar/agents/tools.py` | ChatOpenAI → ChatAnthropic |
| `agents/query_agent.py` | `sidecar/agents/query_agent.py` | ChatOpenAI → ChatAnthropic |
| `agents/state.py` | `sidecar/agents/state.py` | Unchanged |
| `db.py` | `sidecar/db.py` | psycopg → sqlite3 + sqlite-vss |
| `config.py` | `sidecar/config.py` | Pydantic Settings, local paths |
| `app.py` (Streamlit) | `src/views/*.tsx` (React) | Complete rewrite |

### Key Schema Changes (PostgreSQL → SQLite)

- `UUID` → `TEXT` (uuid4 strings)
- `vector(512)` → sqlite-vss virtual table (384-dim)
- `tsvector GENERATED` → FTS5 virtual table + triggers
- `TEXT[]` → `TEXT` (JSON array)
- `JSONB` → `TEXT` (JSON string)
- `TIMESTAMPTZ` → `TEXT` (ISO 8601)
- No `gen_random_uuid()` — generate in Python

---

## Tasks

### Task 1: Python Sidecar Scaffolding

**Files:**
- Create: `sidecar/pyproject.toml`
- Create: `sidecar/__init__.py`
- Create: `sidecar/agents/__init__.py`
- Create: `sidecar/providers/__init__.py`
- Create: `sidecar/sources/__init__.py`
- Create: `sidecar/tests/__init__.py`
- Create: `sidecar/tests/conftest.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "content-intelligence-hub-sidecar"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "langgraph>=0.2.0",
    "langchain-core>=0.3.0",
    "langchain-anthropic>=0.3.0",
    "anthropic>=0.40.0",
    "sentence-transformers>=3.4.0",
    "onnxruntime>=1.20.0",
    "sqlite-vss>=0.1.2",
    "watchdog>=6.0.0",
    "pymupdf>=1.25.0",
    "python-docx>=1.1.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Create directory structure and __init__.py files**

Create empty `__init__.py` in: `sidecar/`, `sidecar/agents/`, `sidecar/providers/`, `sidecar/sources/`, `sidecar/tests/`.

**Step 3: Create conftest.py with shared fixtures**

```python
# sidecar/tests/conftest.py
import pytest
import sqlite3
import json


@pytest.fixture
def db():
    """In-memory SQLite database (no extensions — use db_with_vss for vector tests)."""
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
```

**Step 4: Create venv and install deps**

Run:
```bash
cd sidecar && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

**Step 5: Verify pytest discovers tests**

Run: `cd sidecar && source .venv/bin/activate && python -m pytest --collect-only`
Expected: "no tests ran" (0 collected), no import errors.

**Step 6: Commit**

```bash
git add sidecar/
git commit -m "feat: scaffold Python sidecar project with deps and test fixtures"
```

---

### Task 2: Config Module

**Files:**
- Create: `sidecar/config.py`
- Create: `sidecar/tests/test_config.py`

**Step 1: Write the failing test**

```python
# sidecar/tests/test_config.py
from config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.port == 8420
    assert settings.embedding_model == "all-MiniLM-L6-v2"
    assert settings.embedding_dimensions == 384
    assert settings.llm_model == "claude-sonnet-4-6"
    assert settings.llm_temperature == 0.7
    assert settings.search_limit == 10
    assert settings.hybrid_alpha == 0.5
    assert "ContentIntelligenceHub" in str(settings.data_dir)
    assert settings.db_path.name == "content.db"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("CIH_PORT", "9999")
    monkeypatch.setenv("CIH_ANTHROPIC_API_KEY", "sk-test-key")
    settings = Settings()
    assert settings.port == 9999
    assert settings.anthropic_api_key == "sk-test-key"


def test_data_dir_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("CIH_DATA_DIR", str(tmp_path / "test_data"))
    settings = Settings()
    settings.ensure_dirs()
    assert settings.data_dir.exists()
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config'`

**Step 3: Write minimal implementation**

```python
# sidecar/config.py
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "CIH_"}

    # Server
    port: int = 8420

    # Paths
    data_dir: Path = Path.home() / "Library" / "Application Support" / "ContentIntelligenceHub"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.7

    # Search
    search_limit: int = 10
    hybrid_alpha: float = 0.5

    # Watched folders
    watched_folders: list[str] = []

    @property
    def db_path(self) -> Path:
        return self.data_dir / "content.db"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_config.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add sidecar/config.py sidecar/tests/test_config.py
git commit -m "feat: add config module with pydantic settings"
```

---

### Task 3: Database Module + Schema

**Files:**
- Create: `sidecar/db.py`
- Create: `sidecar/tests/test_db.py`

**Step 1: Write the failing test**

```python
# sidecar/tests/test_db.py
import sqlite3
import json
from db import get_connection, init_schema, insert_content, get_content_by_id


def test_get_connection_memory():
    conn = get_connection(":memory:")
    assert isinstance(conn, sqlite3.Connection)
    # Verify WAL mode
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
    # FTS5 creates several internal tables; check the main one
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
    # FTS5 search should find it
    rows = db.execute(
        "SELECT rowid FROM content_fts WHERE content_fts MATCH 'cloud migration'"
    ).fetchall()
    assert len(rows) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'db'`

**Step 3: Write minimal implementation**

```python
# sidecar/db.py
import sqlite3
import json
from pathlib import Path


def get_connection(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS marketing_content (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            summary TEXT DEFAULT '',
            content_type TEXT DEFAULT '',
            persona TEXT DEFAULT 'general',
            funnel_stage TEXT DEFAULT 'awareness',
            channel TEXT DEFAULT '',
            topics TEXT DEFAULT '[]',
            performance_score REAL DEFAULT 50,
            url TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            source_path TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS generated_content (
            id TEXT PRIMARY KEY,
            source_content_id TEXT NOT NULL REFERENCES marketing_content(id),
            source_title TEXT NOT NULL,
            format TEXT NOT NULL,
            tone TEXT NOT NULL,
            body TEXT NOT NULL,
            quality_score REAL,
            prompts TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_content_type ON marketing_content(content_type);
        CREATE INDEX IF NOT EXISTS idx_content_persona ON marketing_content(persona);
        CREATE INDEX IF NOT EXISTS idx_content_funnel ON marketing_content(funnel_stage);
        CREATE INDEX IF NOT EXISTS idx_gen_source ON generated_content(source_content_id);
        CREATE INDEX IF NOT EXISTS idx_gen_format ON generated_content(format);

        CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(
            title, summary, body,
            content='marketing_content',
            content_rowid='rowid'
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS generated_fts USING fts5(
            body,
            content='generated_content',
            content_rowid='rowid'
        );

        -- Triggers to keep FTS5 in sync with marketing_content
        CREATE TRIGGER IF NOT EXISTS content_ai AFTER INSERT ON marketing_content BEGIN
            INSERT INTO content_fts(rowid, title, summary, body)
            VALUES (new.rowid, new.title, new.summary, new.body);
        END;

        CREATE TRIGGER IF NOT EXISTS content_ad AFTER DELETE ON marketing_content BEGIN
            INSERT INTO content_fts(content_fts, rowid, title, summary, body)
            VALUES ('delete', old.rowid, old.title, old.summary, old.body);
        END;

        CREATE TRIGGER IF NOT EXISTS content_au AFTER UPDATE ON marketing_content BEGIN
            INSERT INTO content_fts(content_fts, rowid, title, summary, body)
            VALUES ('delete', old.rowid, old.title, old.summary, old.body);
            INSERT INTO content_fts(rowid, title, summary, body)
            VALUES (new.rowid, new.title, new.summary, new.body);
        END;

        -- Triggers for generated_content FTS
        CREATE TRIGGER IF NOT EXISTS gen_ai AFTER INSERT ON generated_content BEGIN
            INSERT INTO generated_fts(rowid, body) VALUES (new.rowid, new.body);
        END;

        CREATE TRIGGER IF NOT EXISTS gen_ad AFTER DELETE ON generated_content BEGIN
            INSERT INTO generated_fts(generated_fts, rowid, body)
            VALUES ('delete', old.rowid, old.body);
        END;

        CREATE TRIGGER IF NOT EXISTS gen_au AFTER UPDATE ON generated_content BEGIN
            INSERT INTO generated_fts(generated_fts, rowid, body)
            VALUES ('delete', old.rowid, old.body);
            INSERT INTO generated_fts(rowid, body) VALUES (new.rowid, new.body);
        END;

        -- Settings table for app config
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)


def insert_content(conn: sqlite3.Connection, content: dict) -> str:
    conn.execute(
        """INSERT OR REPLACE INTO marketing_content
        (id, title, body, summary, content_type, persona, funnel_stage,
         channel, topics, performance_score, url, created_at, source_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            content["id"],
            content["title"],
            content["body"],
            content.get("summary", ""),
            content.get("content_type", ""),
            content.get("persona", "general"),
            content.get("funnel_stage", "awareness"),
            content.get("channel", ""),
            content.get("topics", "[]"),
            content.get("performance_score", 50),
            content.get("url", ""),
            content.get("created_at", ""),
            content.get("source_path", ""),
        ),
    )
    conn.commit()
    return content["id"]


def get_content_by_id(conn: sqlite3.Connection, content_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM marketing_content WHERE id = ?", (content_id,)
    ).fetchone()
    if row is None:
        return None
    return dict(row)
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_db.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add sidecar/db.py sidecar/tests/test_db.py
git commit -m "feat: add SQLite database module with FTS5 schema and triggers"
```

---

### Task 4: Embeddings Module

**Files:**
- Create: `sidecar/embeddings.py`
- Create: `sidecar/tests/test_embeddings.py`

**Step 1: Write the failing test**

```python
# sidecar/tests/test_embeddings.py
import numpy as np
from embeddings import EmbeddingModel


def test_embed_text_returns_correct_dimensions():
    model = EmbeddingModel()
    result = model.embed_text("hello world")
    assert isinstance(result, list)
    assert len(result) == 384


def test_embed_text_deterministic():
    model = EmbeddingModel()
    a = model.embed_text("cloud migration strategy")
    b = model.embed_text("cloud migration strategy")
    assert a == b


def test_embed_batch():
    model = EmbeddingModel()
    texts = ["hello world", "cloud migration", "devops practices"]
    results = model.embed_batch(texts)
    assert len(results) == 3
    assert all(len(r) == 384 for r in results)


def test_similar_texts_closer_than_dissimilar():
    model = EmbeddingModel()
    a = model.embed_text("cloud computing and migration strategies")
    b = model.embed_text("cloud infrastructure and migration planning")
    c = model.embed_text("chocolate cake recipe with frosting")
    # Cosine similarity: a-b should be higher than a-c
    sim_ab = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    sim_ac = np.dot(a, c) / (np.linalg.norm(a) * np.linalg.norm(c))
    assert sim_ab > sim_ac
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_embeddings.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'embeddings'`

**Step 3: Write minimal implementation**

```python
# sidecar/embeddings.py
from sentence_transformers import SentenceTransformer
from config import settings


class EmbeddingModel:
    _instance: "EmbeddingModel | None" = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "EmbeddingModel":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                settings.embedding_model,
                cache_folder=str(settings.models_dir),
            )
        return self._model

    def embed_text(self, text: str) -> list[float]:
        model = self._get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return embeddings.tolist()
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_embeddings.py -v`
Expected: 4 passed (first run will download the model ~90MB, subsequent runs use cache)

**Step 5: Commit**

```bash
git add sidecar/embeddings.py sidecar/tests/test_embeddings.py
git commit -m "feat: add local embedding module with sentence-transformers"
```

---

### Task 5: Search Module

**Files:**
- Create: `sidecar/search.py`
- Create: `sidecar/tests/test_search.py`

Port from: `/Users/jm/Projects/Content-Intelligence-Hub-Demo/src/search.py`

Key changes: PostgreSQL `ts_rank_cd` + `<=>` operator → SQLite FTS5 `bm25()` + sqlite-vss distance. Hybrid merge done in Python instead of single SQL query.

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_search.py
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
    """DB with two content items (no vss — keyword/list tests only)."""
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
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_search.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'search'`

**Step 3: Write minimal implementation**

```python
# sidecar/search.py
import sqlite3
import json
from config import settings


def _apply_filters(query: str, params: list, filters: dict | None) -> tuple[str, list]:
    """Append WHERE clauses for supported filters."""
    if not filters:
        return query, params
    clauses = []
    for key in ("content_type", "persona", "funnel_stage", "channel"):
        if key in filters and filters[key]:
            clauses.append(f"mc.{key} = ?")
            params.append(filters[key])
    if "performance_score_gte" in filters:
        clauses.append("mc.performance_score >= ?")
        params.append(filters["performance_score_gte"])
    if clauses:
        query += " AND " + " AND ".join(clauses)
    return query, params


def keyword_search(
    conn: sqlite3.Connection,
    query: str,
    filters: dict | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    """Full-text keyword search using FTS5 with BM25 ranking."""
    limit = limit or settings.search_limit
    # FTS5 MATCH query — escape special chars for safety
    fts_query = query.replace('"', '""')
    sql = """
        SELECT mc.*, bm25(content_fts) AS rank
        FROM content_fts
        JOIN marketing_content mc ON mc.rowid = content_fts.rowid
        WHERE content_fts MATCH ?
    """
    params: list = [f'"{fts_query}"']
    sql, params = _apply_filters(sql, params, filters)
    sql += " ORDER BY rank LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def hybrid_search(
    conn: sqlite3.Connection,
    query: str,
    query_embedding: list[float],
    filters: dict | None = None,
    alpha: float | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Hybrid search combining FTS5 keyword + sqlite-vss vector similarity.

    Merges results in Python: score = alpha * vector_sim + (1 - alpha) * keyword_score.
    """
    alpha = alpha if alpha is not None else settings.hybrid_alpha
    limit = limit or settings.search_limit
    fetch_k = limit * 3  # Fetch more from each source, then merge

    # 1. Keyword results (FTS5)
    keyword_results = keyword_search(conn, query, filters=filters, limit=fetch_k)
    keyword_scores: dict[str, float] = {}
    keyword_items: dict[str, dict] = {}
    if keyword_results:
        max_rank = max(abs(r["rank"]) for r in keyword_results) or 1.0
        for r in keyword_results:
            row = dict(r)
            row.pop("rank", None)
            keyword_scores[r["id"]] = abs(r["rank"]) / max_rank
            keyword_items[r["id"]] = row

    # 2. Vector results (sqlite-vss)
    vector_scores: dict[str, float] = {}
    vector_items: dict[str, dict] = {}
    try:
        vss_rows = conn.execute(
            "SELECT rowid, distance FROM vss_content WHERE vss_search(embedding, vss_search_params(?, ?))",
            [json.dumps(query_embedding), fetch_k],
        ).fetchall()
        if vss_rows:
            for vr in vss_rows:
                mc_row = conn.execute(
                    "SELECT * FROM marketing_content WHERE rowid = ?", (vr["rowid"],)
                ).fetchone()
                if mc_row:
                    item = dict(mc_row)
                    # Apply filters in Python for vector results
                    if filters and not _passes_filters(item, filters):
                        continue
                    sim = max(0.0, 1.0 - vr["distance"])
                    vector_scores[item["id"]] = sim
                    vector_items[item["id"]] = item
    except Exception:
        # vss table may not exist yet (no content embedded)
        pass

    # 3. Merge scores
    all_ids = set(keyword_scores.keys()) | set(vector_scores.keys())
    scored: list[tuple[str, float]] = []
    for cid in all_ids:
        ks = keyword_scores.get(cid, 0.0)
        vs = vector_scores.get(cid, 0.0)
        combined = alpha * vs + (1 - alpha) * ks
        scored.append((cid, combined))

    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for cid, score in scored[:limit]:
        item = keyword_items.get(cid) or vector_items.get(cid)
        if item:
            item["score"] = round(score, 4)
            results.append(item)
    return results


def _passes_filters(item: dict, filters: dict) -> bool:
    """Check if item passes filter criteria."""
    for key in ("content_type", "persona", "funnel_stage", "channel"):
        if key in filters and filters[key] and item.get(key) != filters[key]:
            return False
    if "performance_score_gte" in filters:
        if (item.get("performance_score") or 0) < filters["performance_score_gte"]:
            return False
    return True


def get_similar_content(
    conn: sqlite3.Connection,
    content_id: str,
    limit: int = 5,
) -> list[dict]:
    """Find similar content by vector distance, excluding the source item."""
    # Get source rowid
    source = conn.execute(
        "SELECT rowid FROM marketing_content WHERE id = ?", (content_id,)
    ).fetchone()
    if not source:
        return []
    source_rowid = source["rowid"]

    # Get source embedding from vss table
    try:
        vss_rows = conn.execute(
            "SELECT rowid, distance FROM vss_content WHERE vss_search("
            "embedding, vss_search_params("
            "(SELECT embedding FROM vss_content WHERE rowid = ?), ?))",
            [source_rowid, limit + 1],
        ).fetchall()
    except Exception:
        return []

    results = []
    for vr in vss_rows:
        if vr["rowid"] == source_rowid:
            continue
        row = conn.execute(
            "SELECT * FROM marketing_content WHERE rowid = ?", (vr["rowid"],)
        ).fetchone()
        if row:
            item = dict(row)
            item["distance"] = vr["distance"]
            results.append(item)
    return results[:limit]


def list_all_content(
    conn: sqlite3.Connection,
    filters: dict | None = None,
    limit: int | None = None,
    offset: int = 0,
    search_query: str | None = None,
) -> dict:
    """Paginated content listing with optional filters and keyword search."""
    limit = limit or settings.search_limit

    if search_query:
        items = keyword_search(conn, search_query, filters=filters, limit=limit, offset=offset)
        # Count total matches
        fts_query = search_query.replace('"', '""')
        count_sql = """
            SELECT COUNT(*) FROM content_fts
            JOIN marketing_content mc ON mc.rowid = content_fts.rowid
            WHERE content_fts MATCH ?
        """
        count_params: list = [f'"{fts_query}"']
        count_sql, count_params = _apply_filters(count_sql, count_params, filters)
        total = conn.execute(count_sql, count_params).fetchone()[0]
    else:
        sql = "SELECT mc.* FROM marketing_content mc WHERE 1=1"
        params: list = []
        sql, params = _apply_filters(sql, params, filters)
        count_sql_plain = sql.replace("SELECT mc.*", "SELECT COUNT(*)")
        total = conn.execute(count_sql_plain, params).fetchone()[0]
        sql += " ORDER BY mc.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(sql, params).fetchall()
        items = [dict(r) for r in rows]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


def get_content_stats(conn: sqlite3.Connection) -> dict:
    """Aggregate counts by content_type, persona, funnel_stage, channel."""
    stats = {}
    for col in ("content_type", "persona", "funnel_stage", "channel"):
        rows = conn.execute(
            f"SELECT {col}, COUNT(*) as cnt FROM marketing_content WHERE {col} != '' GROUP BY {col}"
        ).fetchall()
        stats[f"by_{col}"] = {r[0]: r[1] for r in rows}
    total = conn.execute("SELECT COUNT(*) FROM marketing_content").fetchone()[0]
    avg_perf = conn.execute(
        "SELECT COALESCE(AVG(performance_score), 0) FROM marketing_content"
    ).fetchone()[0]
    stats["total"] = total
    stats["avg_performance"] = round(avg_perf, 1)
    return stats


def get_top_performers(
    conn: sqlite3.Connection, limit: int = 10, min_score: float = 0
) -> list[dict]:
    """Get top performing content by performance_score."""
    rows = conn.execute(
        "SELECT * FROM marketing_content WHERE performance_score >= ? "
        "ORDER BY performance_score DESC LIMIT ?",
        (min_score, limit),
    ).fetchall()
    return [dict(r) for r in rows]
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_search.py -v`
Expected: 9 passed

**Step 5: Commit**

```bash
git add sidecar/search.py sidecar/tests/test_search.py
git commit -m "feat: add search module with FTS5 keyword search, hybrid search, filters"
```

---

### Task 6: Generated Content Module

**Files:**
- Create: `sidecar/generated.py`
- Create: `sidecar/tests/test_generated.py`

Port from: `/Users/jm/Projects/Content-Intelligence-Hub-Demo/src/generated.py`

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_generated.py
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
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_generated.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'generated'`

**Step 3: Write minimal implementation**

```python
# sidecar/generated.py
import sqlite3
import json
import uuid
from config import settings


def save_generated_content(
    conn: sqlite3.Connection,
    source_content_id: str,
    source_title: str,
    format: str,
    tone: str,
    body: str,
    quality_score: float | None = None,
    prompts: dict | None = None,
) -> str:
    gen_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO generated_content
        (id, source_content_id, source_title, format, tone, body, quality_score, prompts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            gen_id,
            source_content_id,
            source_title,
            format,
            tone,
            body,
            quality_score,
            json.dumps(prompts or {}),
        ),
    )
    conn.commit()
    return gen_id


def get_generated_by_id(conn: sqlite3.Connection, gen_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM generated_content WHERE id = ?", (gen_id,)
    ).fetchone()
    return dict(row) if row else None


def list_generated_content(
    conn: sqlite3.Connection,
    filters: dict | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> dict:
    limit = limit or settings.search_limit
    sql = "SELECT * FROM generated_content WHERE 1=1"
    params: list = []
    if filters:
        for key in ("format", "tone"):
            if key in filters and filters[key]:
                sql += f" AND {key} = ?"
                params.append(filters[key])
    count_sql = sql.replace("SELECT *", "SELECT COUNT(*)")
    total = conn.execute(count_sql, params).fetchone()[0]
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


def keyword_search_generated(
    conn: sqlite3.Connection,
    query: str,
    filters: dict | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    limit = limit or settings.search_limit
    fts_query = query.replace('"', '""')
    sql = """
        SELECT gc.*, bm25(generated_fts) AS rank
        FROM generated_fts
        JOIN generated_content gc ON gc.rowid = generated_fts.rowid
        WHERE generated_fts MATCH ?
    """
    params: list = [f'"{fts_query}"']
    if filters:
        for key in ("format", "tone"):
            if key in filters and filters[key]:
                sql += f" AND gc.{key} = ?"
                params.append(filters[key])
    sql += " ORDER BY rank LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_generated_stats(conn: sqlite3.Connection) -> dict:
    stats = {}
    for col in ("format", "tone"):
        rows = conn.execute(
            f"SELECT {col}, COUNT(*) as cnt FROM generated_content GROUP BY {col}"
        ).fetchall()
        stats[f"by_{col}"] = {r[0]: r[1] for r in rows}
    stats["total"] = conn.execute("SELECT COUNT(*) FROM generated_content").fetchone()[0]
    return stats
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_generated.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add sidecar/generated.py sidecar/tests/test_generated.py
git commit -m "feat: add generated content module with CRUD, search, stats"
```

---

### Task 7: LLM Provider Abstraction

**Files:**
- Create: `sidecar/providers/base.py`
- Create: `sidecar/providers/anthropic.py`
- Create: `sidecar/tests/test_providers.py`

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_providers.py
from providers.base import LLMProvider, Message
from providers.anthropic import AnthropicProvider
from unittest.mock import patch, MagicMock


def test_message_creation():
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"


def test_provider_interface():
    """LLMProvider defines the expected interface."""
    assert hasattr(LLMProvider, "complete")
    assert hasattr(LLMProvider, "stream")


def test_anthropic_provider_init():
    provider = AnthropicProvider(api_key="sk-test", model="claude-sonnet-4-6")
    assert provider.model == "claude-sonnet-4-6"


@patch("providers.anthropic.Anthropic")
def test_anthropic_complete(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Generated response")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="sk-test")
    result = provider.complete(
        messages=[Message(role="user", content="hello")],
        system="You are helpful.",
    )
    assert result == "Generated response"
    mock_client.messages.create.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_providers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'providers.base'`

**Step 3: Write minimal implementation**

```python
# sidecar/providers/base.py
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        ...

    @abstractmethod
    def stream(
        self,
        messages: list[Message],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        ...
```

```python
# sidecar/providers/anthropic.py
from anthropic import Anthropic
from providers.base import LLMProvider, Message


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def complete(
        self,
        messages: list[Message],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system
        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def stream(
        self,
        messages: list[Message],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system
        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_providers.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add sidecar/providers/base.py sidecar/providers/anthropic.py sidecar/tests/test_providers.py
git commit -m "feat: add LLM provider abstraction with Anthropic implementation"
```

---

### Task 8: Content Tools

**Files:**
- Create: `sidecar/agents/tools.py`
- Create: `sidecar/tests/test_tools.py`

Port from: `/Users/jm/Projects/Content-Intelligence-Hub-Demo/src/agents/tools.py`

Key change: All LLM calls go through the provider abstraction. Prompts adapted slightly for Claude (which responds better to XML-structured prompts).

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_tools.py
from unittest.mock import MagicMock
from agents.tools import (
    analyze_content,
    generate_linkedin_post,
    generate_email,
    generate_twitter_thread,
    generate_summary,
    assess_quality,
)


def _make_mock_provider(response_text: str) -> MagicMock:
    provider = MagicMock()
    provider.complete.return_value = response_text
    return provider


MOCK_ANALYSIS = """## Key Themes
Cloud migration strategy, digital transformation

## Target Audience
CTOs and engineering leaders

## Tone & Voice
Professional, authoritative

## Value Proposition
Comprehensive roadmap reduces migration risk

## Call to Action
Download the migration checklist

## Key Stats/Facts
85% of enterprises plan cloud migration by 2026"""


def test_analyze_content():
    provider = _make_mock_provider(MOCK_ANALYSIS)
    source = {"title": "Cloud Migration Guide", "body": "Cloud migration content...", "summary": "A guide."}
    result = analyze_content(provider, source)
    assert "themes" in result
    assert "audience" in result
    assert "tone" in result
    provider.complete.assert_called_once()


def test_generate_linkedin_post():
    provider = _make_mock_provider("Exciting news about cloud migration!\n\nKey insight here.\n\n#Cloud #Migration")
    source = {"title": "Cloud Guide", "body": "Content...", "summary": "Summary."}
    analysis = {"themes": "cloud", "audience": "CTOs", "tone": "professional"}
    result = generate_linkedin_post(provider, source, analysis, tone="professional")
    assert len(result) > 0
    provider.complete.assert_called_once()


def test_generate_email():
    provider = _make_mock_provider("Subject: Cloud Migration Insights\n\nDear Leader,\n\nBody here.")
    source = {"title": "Cloud Guide", "body": "Content...", "summary": "Summary."}
    analysis = {"themes": "cloud", "audience": "CTOs", "tone": "professional"}
    result = generate_email(provider, source, analysis, tone="professional")
    assert len(result) > 0


def test_generate_twitter_thread():
    provider = _make_mock_provider("1/5 Cloud migration is transforming...\n\n2/5 Key insight...")
    source = {"title": "Cloud Guide", "body": "Content...", "summary": "Summary."}
    analysis = {"themes": "cloud", "audience": "CTOs", "tone": "professional"}
    result = generate_twitter_thread(provider, source, analysis, tone="casual")
    assert len(result) > 0


def test_generate_summary():
    provider = _make_mock_provider("- Key insight about cloud migration\n- Second point\n- Third point")
    source = {"title": "Cloud Guide", "body": "Content...", "summary": "Summary."}
    analysis = {"themes": "cloud", "audience": "CTOs", "tone": "professional"}
    result = generate_summary(provider, source, analysis, tone="professional")
    assert len(result) > 0


def test_assess_quality_good_content():
    score = assess_quality(
        generated_content="This is a well-written LinkedIn post about cloud migration. "
        "It covers key themes and includes a clear call to action. " * 5,
        format_type="linkedin",
    )
    assert 0.0 <= score <= 1.0
    assert score >= 0.5  # Decent length, has CTA


def test_assess_quality_too_short():
    score = assess_quality(generated_content="Short.", format_type="linkedin")
    assert score < 0.5


def test_assess_quality_no_cta():
    score = assess_quality(
        generated_content="This is a LinkedIn post about cloud migration. " * 5,
        format_type="linkedin",
    )
    # No CTA penalty
    assert score < 1.0
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_tools.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.tools'`

**Step 3: Write minimal implementation**

```python
# sidecar/agents/tools.py
import re
from providers.base import LLMProvider, Message


ANALYSIS_PROMPT = """Analyze the following marketing content and extract structured information.

<content>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</content>

Respond with these sections using ## headers:

## Key Themes
Main topics and themes (comma-separated)

## Target Audience
Who this content is for

## Tone & Voice
The writing style and tone

## Value Proposition
The core value being communicated

## Call to Action
The desired next step for the reader

## Key Stats/Facts
Any notable statistics or facts mentioned"""


LINKEDIN_PROMPT = """Create a LinkedIn post based on this source content.

<source>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</source>

<analysis>{analysis}</analysis>

<instructions>
Tone: {tone}
{custom_instructions}
</instructions>

Write a ~300 word LinkedIn post with:
1. An attention-grabbing hook (first line)
2. 2-3 paragraphs of insight
3. A key takeaway
4. A call to action
5. 3-5 relevant hashtags

Do NOT include a title or "LinkedIn Post:" prefix. Just write the post directly."""


EMAIL_PROMPT = """Create a marketing email based on this source content.

<source>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</source>

<analysis>{analysis}</analysis>

<instructions>
Tone: {tone}
{custom_instructions}
</instructions>

Write an email with:
- Subject line (under 50 characters)
- Preview text (first 50 characters that appear in inbox)
- Personalized opener
- Value proposition (2-3 sentences)
- Social proof or key stat
- Clear CTA
- Professional signature placeholder

Format as:
Subject: ...
Preview: ...

[email body]"""


TWITTER_PROMPT = """Create a Twitter/X thread based on this source content.

<source>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</source>

<analysis>{analysis}</analysis>

<instructions>
Tone: {tone}
{custom_instructions}
</instructions>

Write a 5-7 tweet thread. Number each tweet (1/N format). Each tweet MUST be under 280 characters.

Structure:
1. Hook tweet with main insight
2. Context/background
3-5. Key points with specifics
6. Summary + CTA
7. Engagement ask"""


SUMMARY_PROMPT = """Create an executive summary of this content.

<source>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</source>

<analysis>{analysis}</analysis>

<instructions>
Tone: {tone}
{custom_instructions}
</instructions>

Write 3-5 actionable bullet points covering:
- Most important insights
- Actionable items
- Key benefits or outcomes

Use "- " prefix for each bullet. Be concise and specific."""


def analyze_content(provider: LLMProvider, source_content: dict) -> dict:
    prompt = ANALYSIS_PROMPT.format(
        title=source_content.get("title", ""),
        summary=source_content.get("summary", ""),
        body=source_content.get("body", ""),
    )
    response = provider.complete(
        messages=[Message(role="user", content=prompt)],
        system="You are a marketing content analyst. Extract structured information accurately.",
        temperature=0.3,
    )
    return _parse_analysis(response)


def _parse_analysis(text: str) -> dict:
    sections = {
        "themes": "Key Themes",
        "audience": "Target Audience",
        "tone": "Tone & Voice",
        "value_prop": "Value Proposition",
        "cta": "Call to Action",
        "key_facts": "Key Stats/Facts",
    }
    result = {"raw_analysis": text}
    for key, header in sections.items():
        pattern = rf"##\s*{re.escape(header)}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        result[key] = match.group(1).strip() if match else ""
    return result


def generate_linkedin_post(
    provider: LLMProvider,
    source_content: dict,
    analysis: dict,
    tone: str = "professional",
    custom_instructions: str = "",
) -> str:
    prompt = LINKEDIN_PROMPT.format(
        title=source_content.get("title", ""),
        summary=source_content.get("summary", ""),
        body=source_content.get("body", ""),
        analysis=_format_analysis(analysis),
        tone=tone,
        custom_instructions=custom_instructions,
    )
    return provider.complete(
        messages=[Message(role="user", content=prompt)],
        system="You are an expert LinkedIn content creator.",
        temperature=0.7,
    )


def generate_email(
    provider: LLMProvider,
    source_content: dict,
    analysis: dict,
    tone: str = "professional",
    custom_instructions: str = "",
) -> str:
    prompt = EMAIL_PROMPT.format(
        title=source_content.get("title", ""),
        summary=source_content.get("summary", ""),
        body=source_content.get("body", ""),
        analysis=_format_analysis(analysis),
        tone=tone,
        custom_instructions=custom_instructions,
    )
    return provider.complete(
        messages=[Message(role="user", content=prompt)],
        system="You are an expert email marketing copywriter.",
        temperature=0.7,
    )


def generate_twitter_thread(
    provider: LLMProvider,
    source_content: dict,
    analysis: dict,
    tone: str = "professional",
    custom_instructions: str = "",
) -> str:
    prompt = TWITTER_PROMPT.format(
        title=source_content.get("title", ""),
        summary=source_content.get("summary", ""),
        body=source_content.get("body", ""),
        analysis=_format_analysis(analysis),
        tone=tone,
        custom_instructions=custom_instructions,
    )
    return provider.complete(
        messages=[Message(role="user", content=prompt)],
        system="You are an expert Twitter/X content creator.",
        temperature=0.7,
    )


def generate_summary(
    provider: LLMProvider,
    source_content: dict,
    analysis: dict,
    tone: str = "professional",
    custom_instructions: str = "",
) -> str:
    prompt = SUMMARY_PROMPT.format(
        title=source_content.get("title", ""),
        summary=source_content.get("summary", ""),
        body=source_content.get("body", ""),
        analysis=_format_analysis(analysis),
        tone=tone,
        custom_instructions=custom_instructions,
    )
    return provider.complete(
        messages=[Message(role="user", content=prompt)],
        system="You are an expert content strategist.",
        temperature=0.3,
    )


def _format_analysis(analysis: dict) -> str:
    parts = []
    for key in ("themes", "audience", "tone", "value_prop", "cta", "key_facts"):
        if analysis.get(key):
            parts.append(f"{key}: {analysis[key]}")
    return "\n".join(parts)


GENERATE_FN = {
    "linkedin": generate_linkedin_post,
    "email": generate_email,
    "twitter": generate_twitter_thread,
    "summary": generate_summary,
}


def assess_quality(
    generated_content: str,
    format_type: str,
    source_content: dict | None = None,
) -> float:
    """Rule-based quality scoring (0.0-1.0). No LLM call needed."""
    score = 1.0
    length = len(generated_content)

    # Length checks
    max_lengths = {"linkedin": 2000, "email": 3000, "twitter": 2000, "summary": 1000}
    max_len = max_lengths.get(format_type, 2000)
    if length > max_len:
        score -= 0.2
    if length < 100:
        score -= 0.5

    # CTA check (not required for summaries)
    if format_type != "summary":
        cta_patterns = r"(call to action|cta|learn more|check out|click|sign up|download|register|visit|get started|try|join)"
        if not re.search(cta_patterns, generated_content, re.IGNORECASE):
            score -= 0.1

    return max(0.0, min(1.0, score))
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_tools.py -v`
Expected: 9 passed

**Step 5: Commit**

```bash
git add sidecar/agents/tools.py sidecar/tests/test_tools.py
git commit -m "feat: add content tools - analyze, generate (linkedin/email/twitter/summary), assess quality"
```

---

### Task 9: Repurpose Agent (LangGraph)

**Files:**
- Create: `sidecar/agents/state.py`
- Create: `sidecar/agents/repurpose_agent.py`
- Create: `sidecar/tests/test_repurpose_agent.py`

Port from: `/Users/jm/Projects/Content-Intelligence-Hub-Demo/src/agents/repurpose_agent.py` and `state.py`

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_repurpose_agent.py
from unittest.mock import MagicMock, patch
from agents.state import RepurposeState
from agents.repurpose_agent import build_repurpose_graph, repurpose_content


def test_repurpose_state_has_required_fields():
    state = RepurposeState(
        messages=[],
        source_content_id="test-id",
        requested_formats=["linkedin"],
        tone="professional",
    )
    assert state["source_content_id"] == "test-id"
    assert state["requested_formats"] == ["linkedin"]


@patch("agents.repurpose_agent.get_content_by_id")
@patch("agents.repurpose_agent.get_similar_content")
def test_repurpose_content_end_to_end(mock_similar, mock_get_content):
    mock_get_content.return_value = {
        "id": "test-id",
        "title": "Cloud Guide",
        "body": "Cloud migration content here." * 10,
        "summary": "A guide to cloud.",
    }
    mock_similar.return_value = []

    mock_provider = MagicMock()
    mock_provider.complete.side_effect = [
        # analyze_content response
        "## Key Themes\ncloud\n## Target Audience\nCTOs\n## Tone & Voice\nprofessional\n## Value Proposition\nvalue\n## Call to Action\nlearn more\n## Key Stats/Facts\nnone",
        # generate_linkedin_post response
        "Great LinkedIn post about cloud. Learn more at our site. #Cloud",
    ]

    mock_conn = MagicMock()
    result = repurpose_content(
        conn=mock_conn,
        provider=mock_provider,
        content_id="test-id",
        formats=["linkedin"],
        tone="professional",
    )
    assert result["success"] is True
    assert "linkedin" in result["generated_content"]
    assert "linkedin" in result["quality_scores"]


@patch("agents.repurpose_agent.get_content_by_id")
def test_repurpose_content_not_found(mock_get_content):
    mock_get_content.return_value = None
    mock_conn = MagicMock()
    mock_provider = MagicMock()
    result = repurpose_content(
        conn=mock_conn,
        provider=mock_provider,
        content_id="nonexistent",
        formats=["linkedin"],
    )
    assert result["success"] is False
    assert len(result["errors"]) > 0
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_repurpose_agent.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.state'`

**Step 3: Write minimal implementation**

```python
# sidecar/agents/state.py
from typing import Any, TypedDict, Annotated
from langgraph.graph.message import add_messages


class RepurposeState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    source_content_id: str
    requested_formats: list[str]
    tone: str
    custom_instructions: dict[str, str]
    source_content: dict[str, Any]
    similar_content: list[dict[str, Any]]
    content_analysis: dict[str, Any]
    generated_content: dict[str, str]
    quality_scores: dict[str, float]
    current_step: str
    errors: list[str]
```

```python
# sidecar/agents/repurpose_agent.py
import logging
from typing import Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from agents.state import RepurposeState
from agents.tools import (
    analyze_content,
    assess_quality,
    GENERATE_FN,
)
from db import get_content_by_id, get_connection
from search import get_similar_content
from providers.base import LLMProvider

logger = logging.getLogger(__name__)


def _fetch_source_node(state: RepurposeState, conn, provider) -> dict:
    content_id = state["source_content_id"]
    content = get_content_by_id(conn, content_id)
    if not content:
        return {
            "errors": state.get("errors", []) + [f"Content {content_id} not found"],
            "current_step": "error",
        }
    similar = get_similar_content(conn, content_id, limit=3)
    return {
        "source_content": content,
        "similar_content": similar,
        "current_step": "analyze",
        "messages": [HumanMessage(content=f"Fetched source: {content['title']}")],
    }


def _analyze_node(state: RepurposeState, conn, provider) -> dict:
    source = state.get("source_content")
    if not source:
        return {"errors": state.get("errors", []) + ["No source content to analyze"]}
    analysis = analyze_content(provider, source)
    return {
        "content_analysis": analysis,
        "current_step": "generate",
        "messages": [HumanMessage(content=f"Analysis complete: {analysis.get('themes', '')}")],
    }


def _generate_node(state: RepurposeState, conn, provider) -> dict:
    source = state.get("source_content", {})
    analysis = state.get("content_analysis", {})
    tone = state.get("tone", "professional")
    custom = state.get("custom_instructions", {})
    formats = state.get("requested_formats", [])

    generated = {}
    errors = list(state.get("errors", []))

    for fmt in formats:
        gen_fn = GENERATE_FN.get(fmt)
        if not gen_fn:
            errors.append(f"Unknown format: {fmt}")
            continue
        try:
            result = gen_fn(
                provider, source, analysis,
                tone=tone,
                custom_instructions=custom.get(fmt, ""),
            )
            generated[fmt] = result
        except Exception as e:
            errors.append(f"Error generating {fmt}: {e}")
            logger.exception(f"Generation error for {fmt}")

    return {
        "generated_content": generated,
        "errors": errors,
        "current_step": "review",
    }


def _review_node(state: RepurposeState, conn, provider) -> dict:
    generated = state.get("generated_content", {})
    source = state.get("source_content")
    scores = {}
    for fmt, content in generated.items():
        scores[fmt] = assess_quality(content, fmt, source)
        logger.info(f"Quality score for {fmt}: {scores[fmt]:.2f}")
    return {
        "quality_scores": scores,
        "current_step": "done",
    }


def build_repurpose_graph(conn, provider: LLMProvider) -> StateGraph:
    graph = StateGraph(RepurposeState)

    graph.add_node("fetch_source", lambda s: _fetch_source_node(s, conn, provider))
    graph.add_node("analyze", lambda s: _analyze_node(s, conn, provider))
    graph.add_node("generate", lambda s: _generate_node(s, conn, provider))
    graph.add_node("review", lambda s: _review_node(s, conn, provider))

    graph.set_entry_point("fetch_source")

    def route_after_fetch(state):
        if state.get("current_step") == "error":
            return END
        return "analyze"

    graph.add_conditional_edges("fetch_source", route_after_fetch, {"analyze": "analyze", END: END})
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", "review")
    graph.add_edge("review", END)

    return graph.compile()


def repurpose_content(
    conn,
    provider: LLMProvider,
    content_id: str,
    formats: list[str],
    tone: str = "professional",
    custom_instructions: dict[str, str] | None = None,
) -> dict[str, Any]:
    app = build_repurpose_graph(conn, provider)
    initial_state: RepurposeState = {
        "messages": [],
        "source_content_id": content_id,
        "requested_formats": formats,
        "tone": tone,
        "custom_instructions": custom_instructions or {},
        "errors": [],
        "generated_content": {},
        "quality_scores": {},
    }
    try:
        final_state = app.invoke(initial_state)
    except Exception as e:
        return {"success": False, "errors": [str(e)], "generated_content": {}, "quality_scores": {}}

    errors = final_state.get("errors", [])
    generated = final_state.get("generated_content", {})
    return {
        "success": len(generated) > 0,
        "generated_content": generated,
        "quality_scores": final_state.get("quality_scores", {}),
        "analysis": final_state.get("content_analysis", {}),
        "errors": errors,
    }
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_repurpose_agent.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add sidecar/agents/state.py sidecar/agents/repurpose_agent.py sidecar/tests/test_repurpose_agent.py
git commit -m "feat: add LangGraph repurpose agent with 4-node workflow"
```

---

### Task 10: Query Agent

**Files:**
- Create: `sidecar/agents/query_agent.py`
- Create: `sidecar/tests/test_query_agent.py`

Port from: `/Users/jm/Projects/Content-Intelligence-Hub-Demo/src/agents/query_agent.py`

Key change: Uses our LLMProvider instead of ChatOpenAI. Filter extraction via structured prompt.

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_query_agent.py
import json
from unittest.mock import MagicMock, patch
from agents.query_agent import extract_filters, discover_content


def test_extract_filters_basic():
    provider = MagicMock()
    provider.complete.return_value = json.dumps({
        "search_terms": "cloud migration",
        "filters": {"content_type": "blog", "persona": "cto"},
    })
    result = extract_filters(provider, "Find blog posts about cloud migration for CTOs")
    assert result["search_terms"] == "cloud migration"
    assert result["filters"]["content_type"] == "blog"
    assert result["filters"]["persona"] == "cto"


def test_extract_filters_no_filters():
    provider = MagicMock()
    provider.complete.return_value = json.dumps({
        "search_terms": "devops best practices",
        "filters": {},
    })
    result = extract_filters(provider, "tell me about devops best practices")
    assert result["search_terms"] == "devops best practices"
    assert result["filters"] == {}


@patch("agents.query_agent.hybrid_search")
@patch("agents.query_agent.keyword_search")
def test_discover_content(mock_keyword, mock_hybrid):
    mock_keyword.return_value = [
        {"id": "1", "title": "Cloud Guide", "body": "Content...", "summary": "Summary", "score": 0.9}
    ]
    mock_hybrid.return_value = mock_keyword.return_value

    provider = MagicMock()
    # First call: extract_filters
    provider.complete.side_effect = [
        json.dumps({"search_terms": "cloud", "filters": {}}),
        "Based on the results, here's what I found about cloud migration...",
    ]
    mock_conn = MagicMock()
    mock_embed = MagicMock()
    mock_embed.embed_text.return_value = [0.1] * 384

    result = discover_content(
        conn=mock_conn,
        provider=provider,
        embedding_model=mock_embed,
        query="tell me about cloud",
    )
    assert "answer" in result
    assert "results" in result
    assert len(result["results"]) > 0
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_query_agent.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.query_agent'`

**Step 3: Write minimal implementation**

```python
# sidecar/agents/query_agent.py
import json
import logging
from typing import Any

from providers.base import LLMProvider, Message
from search import hybrid_search, keyword_search
from embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


FILTER_EXTRACTION_PROMPT = """Extract search parameters from the user's query.

Return a JSON object with:
- "search_terms": the core search keywords (string)
- "filters": an object with optional keys:
  - "content_type": one of [blog, case_study, email, social_post, landing_page, whitepaper] or null
  - "persona": one of [cto, cfo, developer, marketing_leader, engineer, ceo, cmo] or null
  - "funnel_stage": one of [awareness, consideration, decision, retention] or null
  - "performance_score_gte": minimum performance score (number) or null

Only include filter keys when the user explicitly mentions them or clearly implies them.

<examples>
Query: "Find blog posts about kubernetes for CTOs"
{{"search_terms": "kubernetes", "filters": {{"content_type": "blog", "persona": "cto"}}}}

Query: "high performing content about AI"
{{"search_terms": "AI", "filters": {{"performance_score_gte": 70}}}}

Query: "tell me about cloud migration"
{{"search_terms": "cloud migration", "filters": {{}}}}
</examples>

User query: {query}

Respond with ONLY the JSON object, no other text."""


ANSWER_PROMPT = """Based on the search results below, provide a concise natural language answer to the user's query.

<query>{query}</query>

<results>
{results_text}
</results>

Summarize the key findings. Reference specific content by title. Be concise (2-4 sentences)."""


def extract_filters(provider: LLMProvider, query: str) -> dict:
    prompt = FILTER_EXTRACTION_PROMPT.format(query=query)
    response = provider.complete(
        messages=[Message(role="user", content=prompt)],
        system="You extract structured search parameters from natural language. Respond with JSON only.",
        temperature=0.0,
        max_tokens=256,
    )
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse filter response: {response}")
        return {"search_terms": query, "filters": {}}


def _format_results_for_answer(results: list[dict], limit: int = 5) -> str:
    lines = []
    for i, r in enumerate(results[:limit], 1):
        lines.append(f"{i}. **{r.get('title', 'Untitled')}** ({r.get('content_type', '')})")
        if r.get("summary"):
            lines.append(f"   {r['summary'][:200]}")
        lines.append("")
    return "\n".join(lines)


def discover_content(
    conn,
    provider: LLMProvider,
    embedding_model: EmbeddingModel,
    query: str,
) -> dict[str, Any]:
    # 1. Extract search terms and filters
    extracted = extract_filters(provider, query)
    search_terms = extracted.get("search_terms", query)
    filters = extracted.get("filters", {})

    # 2. Run hybrid search
    query_embedding = embedding_model.embed_text(search_terms)
    results = hybrid_search(
        conn, search_terms, query_embedding, filters=filters, limit=10
    )

    # Fallback to keyword-only if hybrid returns nothing
    if not results:
        results = keyword_search(conn, search_terms, filters=filters, limit=10)

    # 3. Generate natural language answer
    results_text = _format_results_for_answer(results)
    answer_prompt = ANSWER_PROMPT.format(query=query, results_text=results_text)
    answer = provider.complete(
        messages=[Message(role="user", content=answer_prompt)],
        system="You are a helpful content discovery assistant. Be concise and specific.",
        temperature=0.3,
    )

    return {
        "query": query,
        "answer": answer,
        "results": results,
        "filters_applied": filters,
        "search_terms": search_terms,
    }
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_query_agent.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add sidecar/agents/query_agent.py sidecar/tests/test_query_agent.py
git commit -m "feat: add query agent with filter extraction and hybrid search"
```

---

### Task 11: Content Sources + File Ingestion

**Files:**
- Create: `sidecar/sources/base.py`
- Create: `sidecar/sources/local_files.py`
- Create: `sidecar/ingest.py`
- Create: `sidecar/tests/test_ingest.py`

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_ingest.py
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

    # Verify it's in the database
    row = conn.execute("SELECT * FROM marketing_content WHERE source_path = ?", (str(md_file),)).fetchone()
    assert row is not None


def test_ingest_directory(tmp_path):
    (tmp_path / "post1.md").write_text("# Post One\n\nFirst post content.")
    (tmp_path / "post2.md").write_text("# Post Two\n\nSecond post content.")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")  # Should be skipped

    conn = get_connection(":memory:")
    init_schema(conn)
    mock_embed = MagicMock()
    mock_embed.embed_text.return_value = [0.1] * 384

    results = ingest_directory(conn, str(tmp_path), mock_embed)
    assert len(results) == 2
    total = conn.execute("SELECT COUNT(*) FROM marketing_content").fetchone()[0]
    assert total == 2
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_ingest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sources.base'`

**Step 3: Write minimal implementation**

```python
# sidecar/sources/base.py
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class RawContent:
    path: str
    title: str
    body: str
    content_type: str = ""
    metadata: dict = field(default_factory=dict)


class ContentSource(ABC):
    @abstractmethod
    def extract(self, path: str) -> RawContent | None:
        """Extract content from a file. Returns None if unsupported."""
        ...

    @abstractmethod
    def supported_extensions(self) -> set[str]:
        ...
```

```python
# sidecar/sources/local_files.py
import re
from pathlib import Path
from sources.base import ContentSource, RawContent


class LocalFileSource(ContentSource):
    def supported_extensions(self) -> set[str]:
        return {".md", ".markdown", ".txt", ".pdf", ".docx"}

    def extract(self, path: str) -> RawContent | None:
        p = Path(path)
        if p.suffix.lower() not in self.supported_extensions():
            return None
        if not p.exists():
            return None

        ext = p.suffix.lower()
        if ext in (".md", ".markdown"):
            return self._extract_markdown(p)
        elif ext == ".txt":
            return self._extract_text(p)
        elif ext == ".pdf":
            return self._extract_pdf(p)
        elif ext == ".docx":
            return self._extract_docx(p)
        return None

    def _extract_markdown(self, path: Path) -> RawContent:
        text = path.read_text(encoding="utf-8")
        # Extract title from first # heading
        title = path.stem.replace("-", " ").replace("_", " ").title()
        match = re.match(r"^#\s+(.+)$", text, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            # Remove the title line from body
            body = text[match.end():].strip()
        else:
            body = text.strip()
        return RawContent(path=str(path), title=title, body=body)

    def _extract_text(self, path: Path) -> RawContent:
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").replace("_", " ").title()
        return RawContent(path=str(path), title=title, body=text.strip())

    def _extract_pdf(self, path: Path) -> RawContent:
        try:
            import pymupdf
            doc = pymupdf.open(str(path))
            text_parts = [page.get_text() for page in doc]
            doc.close()
            body = "\n\n".join(text_parts).strip()
            title = path.stem.replace("-", " ").replace("_", " ").title()
            # Try to get title from first line
            if body:
                first_line = body.split("\n")[0].strip()
                if len(first_line) < 200:
                    title = first_line
            return RawContent(path=str(path), title=title, body=body)
        except ImportError:
            return RawContent(path=str(path), title=path.stem, body="[PDF extraction unavailable]")

    def _extract_docx(self, path: Path) -> RawContent:
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            title = path.stem.replace("-", " ").replace("_", " ").title()
            if paragraphs:
                title = paragraphs[0]
                body = "\n\n".join(paragraphs[1:])
            else:
                body = ""
            return RawContent(path=str(path), title=title, body=body)
        except ImportError:
            return RawContent(path=str(path), title=path.stem, body="[DOCX extraction unavailable]")
```

```python
# sidecar/ingest.py
import uuid
import json
import logging
from pathlib import Path

from db import insert_content, get_connection
from sources.local_files import LocalFileSource
from embeddings import EmbeddingModel

logger = logging.getLogger(__name__)

_source = LocalFileSource()


def ingest_file(
    conn,
    file_path: str,
    embedding_model: EmbeddingModel,
) -> dict | None:
    """Extract, embed, and insert a single file into the database."""
    raw = _source.extract(file_path)
    if raw is None:
        return None

    # Check if already ingested (by source_path)
    existing = conn.execute(
        "SELECT id FROM marketing_content WHERE source_path = ?", (file_path,)
    ).fetchone()

    content_id = existing["id"] if existing else str(uuid.uuid4())

    # Generate embedding from title + summary + body
    embed_text = f"{raw.title} {raw.body[:500]}"
    embedding = embedding_model.embed_text(embed_text)

    content = {
        "id": content_id,
        "title": raw.title,
        "body": raw.body,
        "summary": raw.body[:200] if len(raw.body) > 200 else raw.body,
        "content_type": raw.content_type or _infer_content_type(raw),
        "source_path": file_path,
        "topics": json.dumps(raw.metadata.get("topics", [])),
    }
    insert_content(conn, content)

    # Insert/update embedding in vss table
    try:
        if existing:
            conn.execute("DELETE FROM vss_content WHERE rowid = (SELECT rowid FROM marketing_content WHERE id = ?)", (content_id,))
        rowid = conn.execute("SELECT rowid FROM marketing_content WHERE id = ?", (content_id,)).fetchone()
        if rowid:
            conn.execute(
                "INSERT INTO vss_content(rowid, embedding) VALUES (?, ?)",
                (rowid[0], json.dumps(embedding)),
            )
            conn.commit()
    except Exception as e:
        # vss table may not be initialized yet
        logger.debug(f"VSS insert skipped: {e}")

    logger.info(f"Ingested: {raw.title} ({file_path})")
    return content


def ingest_directory(
    conn,
    dir_path: str,
    embedding_model: EmbeddingModel,
) -> list[dict]:
    """Ingest all supported files in a directory (non-recursive)."""
    results = []
    p = Path(dir_path)
    if not p.is_dir():
        return results

    for file_path in sorted(p.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in _source.supported_extensions():
            result = ingest_file(conn, str(file_path), embedding_model)
            if result:
                results.append(result)
    return results


def _infer_content_type(raw) -> str:
    """Simple heuristic to guess content type from filename/content."""
    name = Path(raw.path).stem.lower()
    if "case-study" in name or "case_study" in name:
        return "case_study"
    if "email" in name:
        return "email"
    if "landing" in name:
        return "landing_page"
    return "blog"
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_ingest.py -v`
Expected: 6 passed

**Step 5: Commit**

```bash
git add sidecar/sources/ sidecar/ingest.py sidecar/tests/test_ingest.py
git commit -m "feat: add content sources, local file extraction, and ingestion pipeline"
```

---

### Task 12: File Watcher

**Files:**
- Create: `sidecar/watcher.py`
- Create: `sidecar/tests/test_watcher.py`

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_watcher.py
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from watcher import ContentWatcher
import pytest


def test_watcher_init(tmp_path):
    watcher = ContentWatcher(
        watched_dirs=[str(tmp_path)],
        on_file_changed=MagicMock(),
    )
    assert len(watcher.watched_dirs) == 1


def test_watcher_detects_new_file(tmp_path):
    callback = MagicMock()
    watcher = ContentWatcher(
        watched_dirs=[str(tmp_path)],
        on_file_changed=callback,
    )
    watcher.start()
    try:
        # Create a new markdown file
        test_file = tmp_path / "new-post.md"
        test_file.write_text("# New Post\n\nContent here.")
        time.sleep(1.5)  # Wait for event processing
    finally:
        watcher.stop()

    # Callback should have been called with the file path
    assert callback.call_count >= 1
    call_args = [str(c[0][0]) for c in callback.call_args_list]
    assert any("new-post.md" in arg for arg in call_args)


def test_watcher_ignores_unsupported_files(tmp_path):
    callback = MagicMock()
    watcher = ContentWatcher(
        watched_dirs=[str(tmp_path)],
        on_file_changed=callback,
    )
    watcher.start()
    try:
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        time.sleep(1.5)
    finally:
        watcher.stop()

    # Should not trigger for .png files
    call_args = [str(c[0][0]) for c in callback.call_args_list]
    assert not any(".png" in arg for arg in call_args)
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_watcher.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'watcher'`

**Step 3: Write minimal implementation**

```python
# sidecar/watcher.py
import logging
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from sources.local_files import LocalFileSource

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = LocalFileSource().supported_extensions()


class _ContentHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event.src_path)

    def _handle(self, path: str) -> None:
        if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS:
            logger.info(f"File change detected: {path}")
            self.callback(path)


class ContentWatcher:
    def __init__(
        self,
        watched_dirs: list[str],
        on_file_changed: Callable[[str], None],
    ):
        self.watched_dirs = watched_dirs
        self.on_file_changed = on_file_changed
        self._observer = Observer()
        self._handler = _ContentHandler(on_file_changed)

    def start(self) -> None:
        for dir_path in self.watched_dirs:
            if Path(dir_path).is_dir():
                self._observer.schedule(self._handler, dir_path, recursive=False)
                logger.info(f"Watching: {dir_path}")
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5)

    def update_dirs(self, new_dirs: list[str]) -> None:
        """Update watched directories. Stops and restarts the observer."""
        self.stop()
        self.watched_dirs = new_dirs
        self._observer = Observer()
        self.start()
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_watcher.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add sidecar/watcher.py sidecar/tests/test_watcher.py
git commit -m "feat: add file watcher with watchdog for content directory monitoring"
```

---

### Task 13: FastAPI REST Endpoints

**Files:**
- Create: `sidecar/api.py`
- Create: `sidecar/tests/test_api.py`

**Step 1: Write the failing tests**

```python
# sidecar/tests/test_api.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Patch heavy dependencies before importing api
    with patch("api.EmbeddingModel") as mock_embed_cls, \
         patch("api._init_vss"):
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = [0.1] * 384
        mock_embed_cls.return_value = mock_embed

        from api import app
        with TestClient(app) as c:
            yield c


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
```

**Step 2: Run test to verify it fails**

Run: `cd sidecar && python -m pytest tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api'`

**Step 3: Write minimal implementation**

```python
# sidecar/api.py
import json
import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from db import get_connection, init_schema, get_content_by_id, insert_content
from search import (
    keyword_search,
    hybrid_search,
    list_all_content,
    get_content_stats,
    get_similar_content,
    get_top_performers,
)
from generated import (
    save_generated_content,
    get_generated_by_id,
    list_generated_content,
    keyword_search_generated,
    get_generated_stats,
)
from embeddings import EmbeddingModel
from ingest import ingest_file, ingest_directory

logger = logging.getLogger(__name__)

# Module-level state
_conn: sqlite3.Connection | None = None
_embedding_model: EmbeddingModel | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        settings.ensure_dirs()
        _conn = get_connection(settings.db_path)
        init_schema(_conn)
        _init_vss(_conn)
    return _conn


def _init_vss(conn: sqlite3.Connection) -> None:
    """Initialize sqlite-vss extension and virtual table."""
    try:
        import sqlite_vss
        sqlite_vss.load(conn)
        conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS vss_content USING vss0(embedding({settings.embedding_dimensions}))"
        )
        conn.commit()
    except Exception as e:
        logger.warning(f"sqlite-vss not available: {e}")


def _get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_conn()
    logger.info(f"Sidecar ready on port {settings.port}")
    yield
    if _conn:
        _conn.close()


app = FastAPI(title="Content Intelligence Hub Sidecar", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health ---

@app.get("/health")
def health():
    return {"status": "ok", "port": settings.port}


# --- Content ---

class SearchRequest(BaseModel):
    query: str
    filters: dict[str, Any] | None = None
    limit: int | None = None
    offset: int = 0


@app.get("/api/content")
def api_list_content(
    content_type: str | None = None,
    persona: str | None = None,
    funnel_stage: str | None = None,
    search: str | None = None,
    limit: int | None = None,
    offset: int = 0,
):
    conn = _get_conn()
    filters = {}
    if content_type:
        filters["content_type"] = content_type
    if persona:
        filters["persona"] = persona
    if funnel_stage:
        filters["funnel_stage"] = funnel_stage
    return list_all_content(conn, filters=filters or None, limit=limit, offset=offset, search_query=search)


@app.get("/api/content/stats")
def api_content_stats():
    return get_content_stats(_get_conn())


@app.get("/api/content/{content_id}")
def api_get_content(content_id: str):
    result = get_content_by_id(_get_conn(), content_id)
    if not result:
        raise HTTPException(status_code=404, detail="Content not found")
    return result


@app.get("/api/content/{content_id}/similar")
def api_similar_content(content_id: str, limit: int = 5):
    return get_similar_content(_get_conn(), content_id, limit=limit)


@app.post("/api/content/search")
def api_search_content(req: SearchRequest):
    conn = _get_conn()
    embed = _get_embedding_model()
    query_embedding = embed.embed_text(req.query)
    results = hybrid_search(
        conn, req.query, query_embedding,
        filters=req.filters, limit=req.limit,
    )
    return {"items": results, "query": req.query}


# --- Agents ---

class RepurposeRequest(BaseModel):
    content_id: str
    formats: list[str]
    tone: str = "professional"
    custom_instructions: dict[str, str] | None = None
    save: bool = True


class QueryRequest(BaseModel):
    query: str


@app.post("/api/agents/repurpose")
def api_repurpose(req: RepurposeRequest):
    from agents.repurpose_agent import repurpose_content
    from providers.anthropic import AnthropicProvider

    if not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="Anthropic API key not configured")

    provider = AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.llm_model)
    conn = _get_conn()
    result = repurpose_content(
        conn=conn, provider=provider,
        content_id=req.content_id, formats=req.formats,
        tone=req.tone, custom_instructions=req.custom_instructions,
    )

    # Save generated content if requested
    if req.save and result.get("success"):
        source = get_content_by_id(conn, req.content_id)
        source_title = source["title"] if source else ""
        for fmt, body in result.get("generated_content", {}).items():
            gen_id = save_generated_content(
                conn,
                source_content_id=req.content_id,
                source_title=source_title,
                format=fmt,
                tone=req.tone,
                body=body,
                quality_score=result.get("quality_scores", {}).get(fmt),
            )
            result.setdefault("saved_ids", {})[fmt] = gen_id

    return result


@app.post("/api/agents/query")
def api_query(req: QueryRequest):
    from agents.query_agent import discover_content
    from providers.anthropic import AnthropicProvider

    if not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="Anthropic API key not configured")

    provider = AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.llm_model)
    return discover_content(
        conn=_get_conn(),
        provider=provider,
        embedding_model=_get_embedding_model(),
        query=req.query,
    )


# --- Generated Content ---

@app.get("/api/generated")
def api_list_generated(
    format: str | None = None,
    tone: str | None = None,
    limit: int | None = None,
    offset: int = 0,
):
    filters = {}
    if format:
        filters["format"] = format
    if tone:
        filters["tone"] = tone
    return list_generated_content(_get_conn(), filters=filters or None, limit=limit, offset=offset)


@app.get("/api/generated/stats")
def api_generated_stats():
    return get_generated_stats(_get_conn())


@app.get("/api/generated/{gen_id}")
def api_get_generated(gen_id: str):
    result = get_generated_by_id(_get_conn(), gen_id)
    if not result:
        raise HTTPException(status_code=404, detail="Generated content not found")
    return result


@app.post("/api/generated/search")
def api_search_generated(req: SearchRequest):
    return {"items": keyword_search_generated(_get_conn(), req.query, limit=req.limit)}


# --- Ingestion ---

class IngestRequest(BaseModel):
    paths: list[str]


@app.post("/api/ingest")
def api_ingest(req: IngestRequest):
    conn = _get_conn()
    embed = _get_embedding_model()
    results = []
    for path in req.paths:
        p = Path(path)
        if p.is_dir():
            results.extend(ingest_directory(conn, str(p), embed))
        elif p.is_file():
            result = ingest_file(conn, str(p), embed)
            if result:
                results.append(result)
    return {"ingested": len(results), "items": results}


# --- Settings ---

class SettingsUpdate(BaseModel):
    anthropic_api_key: str | None = None
    watched_folders: list[str] | None = None


@app.get("/api/settings")
def api_get_settings():
    return {
        "anthropic_api_key_set": bool(settings.anthropic_api_key),
        "watched_folders": settings.watched_folders,
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
    }


@app.put("/api/settings")
def api_update_settings(req: SettingsUpdate):
    if req.anthropic_api_key is not None:
        settings.anthropic_api_key = req.anthropic_api_key
    if req.watched_folders is not None:
        settings.watched_folders = req.watched_folders
    # Persist to app_settings table
    conn = _get_conn()
    if req.anthropic_api_key is not None:
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES ('anthropic_api_key', ?)",
            (req.anthropic_api_key,),
        )
    if req.watched_folders is not None:
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES ('watched_folders', ?)",
            (json.dumps(req.watched_folders),),
        )
    conn.commit()
    return {"status": "updated"}
```

**Step 4: Run test to verify it passes**

Run: `cd sidecar && python -m pytest tests/test_api.py -v`
Expected: 7 passed

**Step 5: Commit**

```bash
git add sidecar/api.py sidecar/tests/test_api.py
git commit -m "feat: add FastAPI REST endpoints for content, search, agents, settings"
```

---

### Task 14: Electron + Vite Project Scaffolding

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `tsconfig.node.json`
- Create: `electron.vite.config.ts`
- Create: `electron/main.ts`
- Create: `electron/preload.ts`
- Create: `src/index.html`
- Create: `src/main.tsx`
- Create: `src/App.tsx`
- Create: `tailwind.config.js`
- Create: `postcss.config.js`
- Create: `src/index.css`

**Step 1: Initialize Node project and install deps**

Run:
```bash
cd /Users/jm/Projects/Content-Intelligence-Hub
npm init -y
npm install react react-dom react-router-dom @tanstack/react-table
npm install -D electron electron-vite vite @vitejs/plugin-react typescript \
  @types/react @types/react-dom tailwindcss postcss autoprefixer \
  electron-builder vitest @testing-library/react @testing-library/jest-dom \
  jsdom
```

**Step 2: Create package.json (update the generated one)**

Update `package.json` scripts and main entry:

```json
{
  "name": "content-intelligence-hub",
  "version": "0.1.0",
  "main": "dist/main/index.js",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build",
    "preview": "electron-vite preview",
    "dist": "electron-vite build && electron-builder",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

**Step 3: Create TypeScript configs**

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*", "electron/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

```json
// tsconfig.node.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["electron.vite.config.ts"]
}
```

**Step 4: Create electron-vite config**

```typescript
// electron.vite.config.ts
import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: { index: resolve(__dirname, 'electron/main.ts') },
      },
    },
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: { index: resolve(__dirname, 'electron/preload.ts') },
      },
    },
  },
  renderer: {
    root: resolve(__dirname, 'src'),
    build: {
      rollupOptions: {
        input: { index: resolve(__dirname, 'src/index.html') },
      },
    },
    plugins: [react()],
    resolve: {
      alias: { '@': resolve(__dirname, 'src') },
    },
  },
})
```

**Step 5: Create minimal Electron main process**

```typescript
// electron/main.ts
import { app, BrowserWindow } from 'electron'
import path from 'path'

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    win.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    win.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  app.quit()
})
```

```typescript
// electron/preload.ts
import { contextBridge } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
})
```

**Step 6: Create React entry point and shell**

```html
<!-- src/index.html -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Content Intelligence Hub</title>
  </head>
  <body class="bg-background text-foreground">
    <div id="root"></div>
    <script type="module" src="./main.tsx"></script>
  </body>
</html>
```

```typescript
// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen">
        <nav className="w-56 border-r border-border bg-muted/30 p-4 pt-12 flex flex-col gap-1">
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/library">Library</NavLink>
          <NavLink to="/generated">Generated</NavLink>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/dashboard" element={<Placeholder name="Dashboard" />} />
            <Route path="/library" element={<Placeholder name="Library" />} />
            <Route path="/generated" element={<Placeholder name="Generated" />} />
            <Route path="/settings" element={<Placeholder name="Settings" />} />
            <Route path="/content/:id" element={<Placeholder name="Content Detail" />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <a
      href={to}
      className="block rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
    >
      {children}
    </a>
  )
}

function Placeholder({ name }: { name: string }) {
  return (
    <div className="flex items-center justify-center h-full text-muted-foreground">
      <p className="text-lg">{name} — coming soon</p>
    </div>
  )
}

export default App
```

**Step 7: Set up TailwindCSS**

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,tsx,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
      },
    },
  },
  plugins: [],
}
```

```javascript
// postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
  }
  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --border: 240 3.7% 15.9%;
  }
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-app-region: drag;
}

button, a, input, select, textarea {
  -webkit-app-region: no-drag;
}
```

**Step 8: Verify the app starts**

Run: `cd /Users/jm/Projects/Content-Intelligence-Hub && npm run dev`
Expected: Electron window opens showing the sidebar nav and "Dashboard — coming soon" placeholder.

**Step 9: Commit**

```bash
git add package.json tsconfig.json tsconfig.node.json electron.vite.config.ts \
  electron/ src/index.html src/main.tsx src/App.tsx src/index.css \
  tailwind.config.js postcss.config.js
git commit -m "feat: scaffold Electron + React + Vite + TailwindCSS app shell"
```

---

### Task 15: Sidecar Process Manager

**Files:**
- Create: `electron/sidecar.ts`
- Modify: `electron/main.ts`

**Step 1: Create sidecar process manager**

```typescript
// electron/sidecar.ts
import { spawn, ChildProcess } from 'child_process'
import path from 'path'
import { app } from 'electron'
import http from 'http'

const SIDECAR_PORT = 8420
const HEALTH_URL = `http://localhost:${SIDECAR_PORT}/health`
const MAX_RETRIES = 30
const RETRY_INTERVAL_MS = 500

let sidecarProcess: ChildProcess | null = null

export function startSidecar(): Promise<void> {
  return new Promise((resolve, reject) => {
    const isDev = !app.isPackaged
    const sidecarDir = isDev
      ? path.join(app.getAppPath(), 'sidecar')
      : path.join(process.resourcesPath, 'sidecar')

    const pythonPath = isDev
      ? path.join(sidecarDir, '.venv', 'bin', 'python')
      : path.join(sidecarDir, 'python', 'bin', 'python3')

    console.log(`Starting sidecar from ${sidecarDir}`)

    sidecarProcess = spawn(
      pythonPath,
      ['-m', 'uvicorn', 'api:app', '--port', String(SIDECAR_PORT), '--host', '127.0.0.1'],
      {
        cwd: sidecarDir,
        stdio: ['ignore', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
      },
    )

    sidecarProcess.stdout?.on('data', (data) => {
      console.log(`[sidecar] ${data.toString().trim()}`)
    })

    sidecarProcess.stderr?.on('data', (data) => {
      console.error(`[sidecar] ${data.toString().trim()}`)
    })

    sidecarProcess.on('error', (err) => {
      console.error('Failed to start sidecar:', err)
      reject(err)
    })

    sidecarProcess.on('exit', (code) => {
      console.log(`Sidecar exited with code ${code}`)
      sidecarProcess = null
    })

    // Wait for health endpoint
    waitForHealth(0, resolve, reject)
  })
}

function waitForHealth(attempt: number, resolve: () => void, reject: (err: Error) => void): void {
  if (attempt >= MAX_RETRIES) {
    reject(new Error('Sidecar failed to start'))
    return
  }
  setTimeout(() => {
    http
      .get(HEALTH_URL, (res) => {
        if (res.statusCode === 200) {
          console.log('Sidecar is ready')
          resolve()
        } else {
          waitForHealth(attempt + 1, resolve, reject)
        }
      })
      .on('error', () => {
        waitForHealth(attempt + 1, resolve, reject)
      })
  }, RETRY_INTERVAL_MS)
}

export function stopSidecar(): void {
  if (sidecarProcess) {
    console.log('Stopping sidecar...')
    sidecarProcess.kill('SIGTERM')
    sidecarProcess = null
  }
}
```

**Step 2: Update main.ts to use sidecar manager**

```typescript
// electron/main.ts
import { app, BrowserWindow } from 'electron'
import path from 'path'
import { startSidecar, stopSidecar } from './sidecar'

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(async () => {
  try {
    await startSidecar()
  } catch (err) {
    console.error('Sidecar start failed, continuing without it:', err)
  }
  createWindow()
})

app.on('window-all-closed', () => {
  stopSidecar()
  app.quit()
})

app.on('before-quit', () => {
  stopSidecar()
})
```

**Step 3: Verify sidecar starts with app**

Run (in separate terminals):
```bash
# Terminal 1: Start sidecar manually to confirm it works
cd sidecar && source .venv/bin/activate && python -m uvicorn api:app --port 8420
# Terminal 2: Verify health
curl http://localhost:8420/health
```
Expected: `{"status":"ok","port":8420}`

**Step 4: Commit**

```bash
git add electron/sidecar.ts electron/main.ts
git commit -m "feat: add sidecar process manager with health check polling"
```

---

### Task 16: API Client + Dashboard View

**Files:**
- Create: `src/api/client.ts`
- Create: `src/api/types.ts`
- Create: `src/views/Dashboard.tsx`
- Modify: `src/App.tsx`

**Step 1: Create API types**

```typescript
// src/api/types.ts
export interface ContentItem {
  id: string
  title: string
  body: string
  summary: string
  content_type: string
  persona: string
  funnel_stage: string
  channel: string
  topics: string // JSON array
  performance_score: number
  url: string
  created_at: string
  source_path: string
  score?: number
}

export interface GeneratedItem {
  id: string
  source_content_id: string
  source_title: string
  format: string
  tone: string
  body: string
  quality_score: number | null
  prompts: string
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface ContentStats {
  total: number
  avg_performance: number
  by_content_type: Record<string, number>
  by_persona: Record<string, number>
  by_funnel_stage: Record<string, number>
  by_channel: Record<string, number>
}

export interface SearchResponse {
  items: ContentItem[]
  query: string
}

export interface RepurposeRequest {
  content_id: string
  formats: string[]
  tone: string
  custom_instructions?: Record<string, string>
  save?: boolean
}

export interface RepurposeResponse {
  success: boolean
  generated_content: Record<string, string>
  quality_scores: Record<string, number>
  analysis: Record<string, string>
  errors: string[]
  saved_ids?: Record<string, string>
}

export interface DiscoverResponse {
  query: string
  answer: string
  results: ContentItem[]
  filters_applied: Record<string, string>
  search_terms: string
}

export interface AppSettings {
  anthropic_api_key_set: boolean
  watched_folders: string[]
  llm_model: string
  embedding_model: string
}
```

**Step 2: Create API client**

```typescript
// src/api/client.ts
const BASE_URL = 'http://localhost:8420'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

import type {
  ContentItem,
  PaginatedResponse,
  ContentStats,
  SearchResponse,
  GeneratedItem,
  RepurposeRequest,
  RepurposeResponse,
  DiscoverResponse,
  AppSettings,
} from './types'

export const api = {
  // Health
  health: () => request<{ status: string }>('/health'),

  // Content
  listContent: (params?: Record<string, string | number>) => {
    const query = params ? '?' + new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString() : ''
    return request<PaginatedResponse<ContentItem>>(`/api/content${query}`)
  },
  getContent: (id: string) => request<ContentItem>(`/api/content/${id}`),
  getSimilar: (id: string) => request<ContentItem[]>(`/api/content/${id}/similar`),
  searchContent: (query: string, filters?: Record<string, string>) =>
    request<SearchResponse>('/api/content/search', {
      method: 'POST',
      body: JSON.stringify({ query, filters }),
    }),
  getContentStats: () => request<ContentStats>('/api/content/stats'),

  // Agents
  repurpose: (req: RepurposeRequest) =>
    request<RepurposeResponse>('/api/agents/repurpose', {
      method: 'POST',
      body: JSON.stringify(req),
    }),
  discover: (query: string) =>
    request<DiscoverResponse>('/api/agents/query', {
      method: 'POST',
      body: JSON.stringify({ query }),
    }),

  // Generated
  listGenerated: (params?: Record<string, string | number>) => {
    const query = params ? '?' + new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString() : ''
    return request<PaginatedResponse<GeneratedItem>>(`/api/generated${query}`)
  },
  getGenerated: (id: string) => request<GeneratedItem>(`/api/generated/${id}`),

  // Ingestion
  ingest: (paths: string[]) =>
    request<{ ingested: number }>('/api/ingest', {
      method: 'POST',
      body: JSON.stringify({ paths }),
    }),

  // Settings
  getSettings: () => request<AppSettings>('/api/settings'),
  updateSettings: (updates: { anthropic_api_key?: string; watched_folders?: string[] }) =>
    request<{ status: string }>('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(updates),
    }),
}
```

**Step 3: Create Dashboard view**

```typescript
// src/views/Dashboard.tsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { ContentItem, ContentStats } from '../api/types'

export default function Dashboard() {
  const [query, setQuery] = useState('')
  const [stats, setStats] = useState<ContentStats | null>(null)
  const [recentContent, setRecentContent] = useState<ContentItem[]>([])
  const [searchResults, setSearchResults] = useState<ContentItem[] | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.getContentStats().then(setStats).catch(console.error)
    api.listContent({ limit: 6 }).then((r) => setRecentContent(r.items)).catch(console.error)
  }, [])

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) {
      setSearchResults(null)
      return
    }
    setLoading(true)
    try {
      const res = await api.searchContent(query)
      setSearchResults(res.items)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const displayItems = searchResults ?? recentContent

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="pt-4">
        <h1 className="text-2xl font-semibold mb-2">Content Intelligence Hub</h1>
        <p className="text-muted-foreground text-sm">Search, explore, and repurpose your marketing content.</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search content... (e.g., 'cloud migration for CTOs')"
          className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* Stats */}
      {stats && stats.total > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Total Content" value={stats.total} />
          <StatCard label="Avg Performance" value={`${stats.avg_performance}%`} />
          <StatCard label="Content Types" value={Object.keys(stats.by_content_type).length} />
          <StatCard label="Personas" value={Object.keys(stats.by_persona).length} />
        </div>
      )}

      {/* Content Grid */}
      <div>
        <h2 className="text-lg font-medium mb-3">
          {searchResults ? `Search Results (${searchResults.length})` : 'Recent Content'}
        </h2>
        {displayItems.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            {searchResults ? 'No results found.' : 'No content yet. Add watched folders in Settings to get started.'}
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayItems.map((item) => (
              <ContentCard key={item.id} item={item} onClick={() => navigate(`/content/${item.id}`)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  )
}

function ContentCard({ item, onClick }: { item: ContentItem; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="text-left rounded-lg border border-border p-4 hover:bg-accent/50 transition-colors"
    >
      <div className="flex gap-2 mb-2">
        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
          {item.content_type}
        </span>
        {item.performance_score > 0 && (
          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
            {item.performance_score}%
          </span>
        )}
      </div>
      <h3 className="font-medium text-sm line-clamp-2">{item.title}</h3>
      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{item.summary}</p>
    </button>
  )
}
```

**Step 4: Update App.tsx to use real views**

Replace the `Placeholder` usage for Dashboard:

```typescript
// In App.tsx, add import:
import Dashboard from './views/Dashboard'

// Replace the dashboard route:
<Route path="/dashboard" element={<Dashboard />} />
```

**Step 5: Verify Dashboard renders**

Run: `npm run dev`
Expected: Dashboard shows search bar, stats cards (empty state), and "No content yet" message.

**Step 6: Commit**

```bash
git add src/api/ src/views/Dashboard.tsx src/App.tsx
git commit -m "feat: add API client, types, and Dashboard view with search and stats"
```

---

### Task 17: Library View (Existing Content)

**Files:**
- Create: `src/views/Library.tsx`
- Modify: `src/App.tsx`

**Step 1: Create Library view with data table**

```typescript
// src/views/Library.tsx
import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table'
import { api } from '../api/client'
import type { ContentItem } from '../api/types'

const columnHelper = createColumnHelper<ContentItem>()

const columns = [
  columnHelper.accessor('title', {
    header: 'Title',
    cell: (info) => (
      <span className="font-medium line-clamp-1">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor('content_type', {
    header: 'Type',
    cell: (info) => (
      <span className="text-xs px-2 py-0.5 rounded-full bg-muted">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor('persona', { header: 'Persona' }),
  columnHelper.accessor('funnel_stage', { header: 'Funnel Stage' }),
  columnHelper.accessor('performance_score', {
    header: 'Score',
    cell: (info) => `${info.getValue() ?? 0}%`,
  }),
  columnHelper.accessor('created_at', {
    header: 'Date',
    cell: (info) => {
      const val = info.getValue()
      return val ? new Date(val).toLocaleDateString() : ''
    },
  }),
]

export default function Library() {
  const [data, setData] = useState<ContentItem[]>([])
  const [total, setTotal] = useState(0)
  const [sorting, setSorting] = useState<SortingState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const params: Record<string, string | number> = { limit: 50 }
    if (filters.content_type) params.content_type = filters.content_type
    if (filters.persona) params.persona = filters.persona
    if (globalFilter) params.search = globalFilter
    api.listContent(params).then((r) => {
      setData(r.items)
      setTotal(r.total)
    })
  }, [filters, globalFilter])

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  const selectedItem = useMemo(
    () => data.find((d) => d.id === selectedId),
    [data, selectedId],
  )

  return (
    <div className="flex h-full gap-4">
      <div className="flex-1 flex flex-col min-w-0">
        {/* Filter bar */}
        <div className="flex gap-2 mb-4 flex-wrap">
          <input
            type="text"
            placeholder="Search library..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm flex-1 min-w-[200px] focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
          <FilterSelect
            label="Type"
            value={filters.content_type || ''}
            options={['blog', 'case_study', 'email', 'social_post', 'landing_page', 'whitepaper']}
            onChange={(v) => setFilters((f) => ({ ...f, content_type: v }))}
          />
          <FilterSelect
            label="Persona"
            value={filters.persona || ''}
            options={['cto', 'cfo', 'developer', 'marketing_leader', 'engineer']}
            onChange={(v) => setFilters((f) => ({ ...f, persona: v }))}
          />
        </div>

        {/* Table */}
        <div className="border border-border rounded-lg overflow-auto flex-1">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 sticky top-0">
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id}>
                  {hg.headers.map((h) => (
                    <th
                      key={h.id}
                      onClick={h.column.getToggleSortingHandler()}
                      className="text-left px-3 py-2 font-medium text-muted-foreground cursor-pointer select-none"
                    >
                      {flexRender(h.column.columnDef.header, h.getContext())}
                      {{ asc: ' ^', desc: ' v' }[h.column.getIsSorted() as string] ?? ''}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => setSelectedId(row.original.id)}
                  onDoubleClick={() => navigate(`/content/${row.original.id}`)}
                  className={`border-t border-border cursor-pointer hover:bg-accent/50 ${
                    selectedId === row.original.id ? 'bg-accent' : ''
                  }`}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-2">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.length === 0 && (
            <p className="text-center text-muted-foreground py-8 text-sm">No content found.</p>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-2">{total} items total</p>
      </div>

      {/* Preview panel */}
      {selectedItem && (
        <div className="w-80 border border-border rounded-lg p-4 overflow-auto flex-shrink-0">
          <h3 className="font-semibold mb-2">{selectedItem.title}</h3>
          <div className="flex gap-1 mb-3 flex-wrap">
            <Tag>{selectedItem.content_type}</Tag>
            <Tag>{selectedItem.persona}</Tag>
            <Tag>{selectedItem.funnel_stage}</Tag>
          </div>
          <p className="text-sm text-muted-foreground mb-4">{selectedItem.summary}</p>
          <button
            onClick={() => navigate(`/content/${selectedItem.id}`)}
            className="w-full rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            View Details
          </button>
        </div>
      )}
    </div>
  )
}

function FilterSelect({
  label, value, options, onChange,
}: {
  label: string; value: string; options: string[]; onChange: (v: string) => void
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-md border border-border bg-background px-2 py-1.5 text-sm"
    >
      <option value="">All {label}s</option>
      {options.map((o) => (
        <option key={o} value={o}>{o.replace('_', ' ')}</option>
      ))}
    </select>
  )
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
      {children}
    </span>
  )
}
```

**Step 2: Update App.tsx**

```typescript
// Add import
import Library from './views/Library'

// Replace route
<Route path="/library" element={<Library />} />
```

**Step 3: Verify Library renders**

Run: `npm run dev`
Expected: Library view shows filter bar and empty table.

**Step 4: Commit**

```bash
git add src/views/Library.tsx src/App.tsx
git commit -m "feat: add Library view with @tanstack/react-table, filters, and preview panel"
```

---

### Task 18: Content Detail + Repurpose View

**Files:**
- Create: `src/views/ContentDetail.tsx`
- Modify: `src/App.tsx`

**Step 1: Create Content Detail view**

```typescript
// src/views/ContentDetail.tsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { ContentItem, RepurposeResponse } from '../api/types'

const FORMATS = [
  { id: 'linkedin', label: 'LinkedIn Post' },
  { id: 'email', label: 'Email' },
  { id: 'twitter', label: 'Twitter Thread' },
  { id: 'summary', label: 'Summary' },
]

const TONES = ['professional', 'casual', 'technical', 'friendly']

export default function ContentDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [content, setContent] = useState<ContentItem | null>(null)
  const [similar, setSimilar] = useState<ContentItem[]>([])
  const [error, setError] = useState('')

  // Repurpose state
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['linkedin'])
  const [tone, setTone] = useState('professional')
  const [repurposeResult, setRepurposeResult] = useState<RepurposeResponse | null>(null)
  const [repurposing, setRepurposing] = useState(false)
  const [activeTab, setActiveTab] = useState('')

  useEffect(() => {
    if (!id) return
    api.getContent(id).then(setContent).catch(() => setError('Content not found'))
    api.getSimilar(id).then(setSimilar).catch(() => {})
  }, [id])

  async function handleRepurpose() {
    if (!id || selectedFormats.length === 0) return
    setRepurposing(true)
    setRepurposeResult(null)
    try {
      const result = await api.repurpose({
        content_id: id,
        formats: selectedFormats,
        tone,
        save: true,
      })
      setRepurposeResult(result)
      if (result.generated_content) {
        setActiveTab(Object.keys(result.generated_content)[0] || '')
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setRepurposing(false)
    }
  }

  if (error && !content) {
    return <div className="text-center py-8 text-red-500">{error}</div>
  }
  if (!content) {
    return <div className="text-center py-8 text-muted-foreground">Loading...</div>
  }

  return (
    <div className="max-w-6xl mx-auto flex gap-6">
      {/* Main content */}
      <div className="flex-1 min-w-0">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block"
        >
          &larr; Back
        </button>
        <h1 className="text-2xl font-semibold mb-2">{content.title}</h1>
        <div className="flex gap-2 mb-4 flex-wrap">
          <Tag>{content.content_type}</Tag>
          <Tag>{content.persona}</Tag>
          <Tag>{content.funnel_stage}</Tag>
          {content.performance_score > 0 && <Tag>{content.performance_score}%</Tag>}
        </div>
        {content.summary && (
          <p className="text-muted-foreground text-sm mb-4 italic">{content.summary}</p>
        )}
        <div className="prose prose-sm max-w-none">
          <div className="whitespace-pre-wrap text-sm leading-relaxed">{content.body}</div>
        </div>

        {/* Repurpose Results */}
        {repurposeResult && repurposeResult.success && (
          <div className="mt-8 border-t border-border pt-6">
            <h2 className="text-lg font-semibold mb-3">Generated Content</h2>
            <div className="flex gap-1 mb-4">
              {Object.keys(repurposeResult.generated_content).map((fmt) => (
                <button
                  key={fmt}
                  onClick={() => setActiveTab(fmt)}
                  className={`px-3 py-1.5 text-sm rounded-md ${
                    activeTab === fmt ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-accent'
                  }`}
                >
                  {fmt}
                  {repurposeResult.quality_scores[fmt] != null && (
                    <span className="ml-1 opacity-70">
                      ({Math.round(repurposeResult.quality_scores[fmt] * 100)}%)
                    </span>
                  )}
                </button>
              ))}
            </div>
            {activeTab && repurposeResult.generated_content[activeTab] && (
              <div className="border border-border rounded-lg p-4 bg-muted/20">
                <pre className="whitespace-pre-wrap text-sm font-sans">
                  {repurposeResult.generated_content[activeTab]}
                </pre>
              </div>
            )}
          </div>
        )}
        {repurposeResult && !repurposeResult.success && (
          <div className="mt-4 text-red-500 text-sm">
            Errors: {repurposeResult.errors.join(', ')}
          </div>
        )}
      </div>

      {/* Repurpose sidebar */}
      <div className="w-72 flex-shrink-0 space-y-6">
        <div className="border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-3">Repurpose Content</h3>

          <div className="mb-4">
            <p className="text-xs font-medium text-muted-foreground mb-2">Formats</p>
            {FORMATS.map((f) => (
              <label key={f.id} className="flex items-center gap-2 text-sm mb-1">
                <input
                  type="checkbox"
                  checked={selectedFormats.includes(f.id)}
                  onChange={(e) => {
                    setSelectedFormats(
                      e.target.checked
                        ? [...selectedFormats, f.id]
                        : selectedFormats.filter((x) => x !== f.id),
                    )
                  }}
                />
                {f.label}
              </label>
            ))}
          </div>

          <div className="mb-4">
            <p className="text-xs font-medium text-muted-foreground mb-2">Tone</p>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
            >
              {TONES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleRepurpose}
            disabled={repurposing || selectedFormats.length === 0}
            className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {repurposing ? 'Generating...' : 'Generate'}
          </button>
        </div>

        {/* Similar content */}
        {similar.length > 0 && (
          <div className="border border-border rounded-lg p-4">
            <h3 className="font-semibold mb-3 text-sm">Similar Content</h3>
            {similar.map((s) => (
              <button
                key={s.id}
                onClick={() => navigate(`/content/${s.id}`)}
                className="block text-left text-sm text-muted-foreground hover:text-foreground mb-2 w-full"
              >
                {s.title}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
      {children}
    </span>
  )
}
```

**Step 2: Update App.tsx**

```typescript
// Add import
import ContentDetail from './views/ContentDetail'

// Replace route
<Route path="/content/:id" element={<ContentDetail />} />
```

**Step 3: Verify Content Detail renders**

Run: `npm run dev`, navigate to `/content/some-id`
Expected: Shows "Content not found" error (no data yet), layout is correct.

**Step 4: Commit**

```bash
git add src/views/ContentDetail.tsx src/App.tsx
git commit -m "feat: add Content Detail view with repurpose panel and similar content"
```

---

### Task 19: Settings View

**Files:**
- Create: `src/views/Settings.tsx`
- Modify: `src/App.tsx`

**Step 1: Create Settings view**

```typescript
// src/views/Settings.tsx
import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { AppSettings } from '../api/types'

export default function Settings() {
  const [settings, setSettings] = useState<AppSettings | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [newFolder, setNewFolder] = useState('')
  const [folders, setFolders] = useState<string[]>([])
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getSettings().then((s) => {
      setSettings(s)
      setFolders(s.watched_folders)
    }).catch((e) => setError(e.message))
  }, [])

  async function saveApiKey() {
    try {
      await api.updateSettings({ anthropic_api_key: apiKey })
      setApiKey('')
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
      // Refresh settings
      const s = await api.getSettings()
      setSettings(s)
    } catch (e: any) {
      setError(e.message)
    }
  }

  async function addFolder() {
    if (!newFolder.trim()) return
    const updated = [...folders, newFolder.trim()]
    try {
      await api.updateSettings({ watched_folders: updated })
      setFolders(updated)
      setNewFolder('')
    } catch (e: any) {
      setError(e.message)
    }
  }

  async function removeFolder(path: string) {
    const updated = folders.filter((f) => f !== path)
    try {
      await api.updateSettings({ watched_folders: updated })
      setFolders(updated)
    } catch (e: any) {
      setError(e.message)
    }
  }

  async function ingestFolder(path: string) {
    try {
      const result = await api.ingest([path])
      alert(`Ingested ${result.ingested} files from ${path}`)
    } catch (e: any) {
      setError(e.message)
    }
  }

  if (!settings) {
    return <div className="text-center py-8 text-muted-foreground">Loading settings...</div>
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <h1 className="text-2xl font-semibold">Settings</h1>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {/* API Key */}
      <section className="border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-1">Anthropic API Key</h2>
        <p className="text-sm text-muted-foreground mb-3">
          Required for content repurposing and AI-powered search.
          {settings.anthropic_api_key_set && <span className="text-green-600 ml-2">Configured</span>}
        </p>
        <div className="flex gap-2">
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={settings.anthropic_api_key_set ? '********' : 'sk-ant-...'}
            className="flex-1 rounded-md border border-border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
          <button
            onClick={saveApiKey}
            disabled={!apiKey}
            className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {saved ? 'Saved!' : 'Save'}
          </button>
        </div>
      </section>

      {/* Watched Folders */}
      <section className="border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-1">Watched Folders</h2>
        <p className="text-sm text-muted-foreground mb-3">
          Content from these folders will be automatically imported.
        </p>
        {folders.length > 0 && (
          <ul className="space-y-2 mb-3">
            {folders.map((f) => (
              <li key={f} className="flex items-center justify-between text-sm border border-border rounded-md px-3 py-2">
                <span className="font-mono text-xs truncate flex-1">{f}</span>
                <div className="flex gap-2 ml-2">
                  <button
                    onClick={() => ingestFolder(f)}
                    className="text-xs text-primary hover:underline"
                  >
                    Import Now
                  </button>
                  <button
                    onClick={() => removeFolder(f)}
                    className="text-xs text-red-500 hover:underline"
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
        <div className="flex gap-2">
          <input
            type="text"
            value={newFolder}
            onChange={(e) => setNewFolder(e.target.value)}
            placeholder="/path/to/content/folder"
            className="flex-1 rounded-md border border-border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
          <button
            onClick={addFolder}
            disabled={!newFolder.trim()}
            className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Add
          </button>
        </div>
      </section>

      {/* Info */}
      <section className="border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-2">System Info</h2>
        <dl className="grid grid-cols-2 gap-y-1 text-sm">
          <dt className="text-muted-foreground">LLM Model</dt>
          <dd>{settings.llm_model}</dd>
          <dt className="text-muted-foreground">Embedding Model</dt>
          <dd>{settings.embedding_model}</dd>
        </dl>
      </section>
    </div>
  )
}
```

**Step 2: Update App.tsx**

```typescript
// Add import
import Settings from './views/Settings'

// Replace route
<Route path="/settings" element={<Settings />} />
```

**Step 3: Commit**

```bash
git add src/views/Settings.tsx src/App.tsx
git commit -m "feat: add Settings view with API key config and watched folders"
```

---

### Task 20: Generated Library + Final App.tsx + Nav

**Files:**
- Create: `src/views/Generated.tsx`
- Modify: `src/App.tsx` (final version with all routes and proper NavLink)

**Step 1: Create Generated Library view**

```typescript
// src/views/Generated.tsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { GeneratedItem } from '../api/types'

export default function Generated() {
  const [items, setItems] = useState<GeneratedItem[]>([])
  const [total, setTotal] = useState(0)
  const [formatFilter, setFormatFilter] = useState('')
  const [toneFilter, setToneFilter] = useState('')
  const [search, setSearch] = useState('')
  const [selectedItem, setSelectedItem] = useState<GeneratedItem | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const params: Record<string, string | number> = { limit: 50 }
    if (formatFilter) params.format = formatFilter
    if (toneFilter) params.tone = toneFilter
    api.listGenerated(params).then((r) => {
      setItems(r.items)
      setTotal(r.total)
    })
  }, [formatFilter, toneFilter])

  return (
    <div className="flex h-full gap-4">
      <div className="flex-1 flex flex-col min-w-0">
        <h1 className="text-2xl font-semibold mb-4">Generated Content</h1>

        <div className="flex gap-2 mb-4 flex-wrap">
          <select
            value={formatFilter}
            onChange={(e) => setFormatFilter(e.target.value)}
            className="rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          >
            <option value="">All Formats</option>
            {['linkedin', 'email', 'twitter', 'summary'].map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
          <select
            value={toneFilter}
            onChange={(e) => setToneFilter(e.target.value)}
            className="rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          >
            <option value="">All Tones</option>
            {['professional', 'casual', 'technical', 'friendly'].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="border border-border rounded-lg overflow-auto flex-1">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 sticky top-0">
              <tr>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground">Source</th>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground">Format</th>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground">Tone</th>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground">Quality</th>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground">Date</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  className={`border-t border-border cursor-pointer hover:bg-accent/50 ${
                    selectedItem?.id === item.id ? 'bg-accent' : ''
                  }`}
                >
                  <td className="px-3 py-2 font-medium">{item.source_title}</td>
                  <td className="px-3 py-2">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-muted">{item.format}</span>
                  </td>
                  <td className="px-3 py-2">{item.tone}</td>
                  <td className="px-3 py-2">
                    {item.quality_score != null ? `${Math.round(item.quality_score * 100)}%` : '-'}
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {new Date(item.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.length === 0 && (
            <p className="text-center text-muted-foreground py-8 text-sm">
              No generated content yet. Repurpose content from the Library.
            </p>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-2">{total} items total</p>
      </div>

      {/* Preview panel */}
      {selectedItem && (
        <div className="w-96 border border-border rounded-lg p-4 overflow-auto flex-shrink-0">
          <div className="flex justify-between items-start mb-3">
            <div>
              <p className="text-xs text-muted-foreground">Source</p>
              <button
                onClick={() => navigate(`/content/${selectedItem.source_content_id}`)}
                className="text-sm font-medium text-primary hover:underline"
              >
                {selectedItem.source_title}
              </button>
            </div>
            <div className="flex gap-1">
              <span className="text-xs px-2 py-0.5 rounded-full bg-muted">{selectedItem.format}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-muted">{selectedItem.tone}</span>
            </div>
          </div>
          <pre className="whitespace-pre-wrap text-sm font-sans leading-relaxed">
            {selectedItem.body}
          </pre>
        </div>
      )}
    </div>
  )
}
```

**Step 2: Write final App.tsx with proper routing and NavLink**

```typescript
// src/App.tsx
import { HashRouter, Routes, Route, Navigate, NavLink as RouterNavLink } from 'react-router-dom'
import Dashboard from './views/Dashboard'
import Library from './views/Library'
import Generated from './views/Generated'
import ContentDetail from './views/ContentDetail'
import Settings from './views/Settings'

function App() {
  return (
    <HashRouter>
      <div className="flex h-screen">
        <nav className="w-56 border-r border-border bg-muted/30 p-4 pt-12 flex flex-col gap-1">
          <SidebarLink to="/dashboard">Dashboard</SidebarLink>
          <SidebarLink to="/library">Library</SidebarLink>
          <SidebarLink to="/generated">Generated</SidebarLink>
          <SidebarLink to="/settings">Settings</SidebarLink>
        </nav>
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/library" element={<Library />} />
            <Route path="/generated" element={<Generated />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/content/:id" element={<ContentDetail />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  )
}

function SidebarLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
          isActive
            ? 'bg-accent text-accent-foreground'
            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
        }`
      }
    >
      {children}
    </RouterNavLink>
  )
}

export default App
```

Note: Changed from `BrowserRouter` to `HashRouter` — Electron file:// protocol requires hash routing.

**Step 3: Verify all views render**

Run: `npm run dev`
Expected: All nav links work, all views render placeholders or empty states properly.

**Step 4: Commit**

```bash
git add src/views/Generated.tsx src/App.tsx
git commit -m "feat: add Generated Library view and finalize app routing with HashRouter"
```

---

## Post-Implementation Checklist

After all 20 tasks are complete, verify:

1. **Sidecar starts**: `cd sidecar && python -m uvicorn api:app --port 8420` — health check returns OK
2. **All Python tests pass**: `cd sidecar && python -m pytest -v`
3. **Electron app starts**: `npm run dev` — window opens, sidecar starts automatically
4. **End-to-end flow**: Settings → set API key → add watched folder → import content → search → repurpose → view generated content
5. **Frontend tests pass**: `npm run test`

## Future Enhancements (out of scope for this plan)

- Keyboard shortcuts (Cmd+K for search, arrow keys for table nav)
- Drag & drop file import
- Native macOS menu bar integration
- Dark mode toggle
- electron-builder packaging + code signing
- Auto-update via electron-updater
- ONNX-optimized embeddings for faster inference
- Recursive directory watching
