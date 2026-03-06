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
        (gen_id, source_content_id, source_title, format, tone, body,
         quality_score, json.dumps(prompts or {})),
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
