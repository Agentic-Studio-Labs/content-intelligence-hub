import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import get_db, require_user

router = APIRouter(prefix="/api/content", tags=["content"])


class SearchRequest(BaseModel):
    query: str
    filters: dict[str, str] | None = None


@router.get("")
def list_content(
    limit: int = Query(default=50),
    offset: int = Query(default=0),
    search: str | None = Query(default=None),
    content_type: str | None = Query(default=None),
    persona: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_user),
):
    clauses = ["1=1"]
    params: list[object] = []
    if search:
        clauses.append("(title LIKE ? OR summary LIKE ? OR body LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if content_type:
        clauses.append("content_type = ?")
        params.append(content_type)
    if persona:
        clauses.append("persona = ?")
        params.append(persona)

    total = conn.execute(
        f"SELECT COUNT(*) FROM content_items WHERE {' AND '.join(clauses)}",
        tuple(params),
    ).fetchone()[0]
    rows = conn.execute(
        f"""
        SELECT * FROM content_items
        WHERE {" AND ".join(clauses)}
        ORDER BY updated_at DESC
        LIMIT ? OFFSET ?
        """,
        tuple(params + [limit, offset]),
    ).fetchall()
    items = [dict(row) for row in rows]
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


@router.post("/search")
def search_content(
    req: SearchRequest,
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_user),
):
    filters = req.filters or {}
    query = req.query
    clauses = ["(title LIKE ? OR summary LIKE ? OR body LIKE ?)"]
    params: list[object] = [f"%{query}%", f"%{query}%", f"%{query}%"]
    if filters.get("content_type"):
        clauses.append("content_type = ?")
        params.append(filters["content_type"])
    if filters.get("persona"):
        clauses.append("persona = ?")
        params.append(filters["persona"])
    rows = conn.execute(
        f"""
        SELECT * FROM content_items
        WHERE {" AND ".join(clauses)}
        ORDER BY updated_at DESC
        LIMIT 25
        """,
        tuple(params),
    ).fetchall()
    return {
        "items": [dict(row) for row in rows],
        "query": query,
    }


@router.get("/stats")
def content_stats(
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_user),
):
    total = conn.execute("SELECT COUNT(*) FROM content_items").fetchone()[0]
    avg_performance = conn.execute(
        "SELECT COALESCE(AVG(performance_score), 0) FROM content_items"
    ).fetchone()[0]

    def group(column: str) -> dict[str, int]:
        rows = conn.execute(
            f"SELECT {column}, COUNT(*) AS count FROM content_items WHERE {column} != '' GROUP BY {column}"
        ).fetchall()
        return {row[0]: row[1] for row in rows}

    return {
        "total": total,
        "avg_performance": round(avg_performance, 1),
        "by_content_type": group("content_type"),
        "by_persona": group("persona"),
        "by_funnel_stage": group("funnel_stage"),
        "by_channel": group("channel"),
    }


@router.get("/{content_id}")
def get_content(
    content_id: str,
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_user),
):
    row = conn.execute(
        "SELECT * FROM content_items WHERE id = ?", (content_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return dict(row)


@router.get("/{content_id}/similar")
def get_similar_content(
    content_id: str,
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_user),
):
    row = conn.execute(
        "SELECT content_type, id FROM content_items WHERE id = ?",
        (content_id,),
    ).fetchone()
    if row is None:
        return []
    rows = conn.execute(
        """
        SELECT * FROM content_items
        WHERE content_type = ? AND id != ?
        ORDER BY updated_at DESC
        LIMIT 5
        """,
        (row["content_type"], content_id),
    ).fetchall()
    return [dict(item) for item in rows]
