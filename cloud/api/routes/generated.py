import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db, require_user

router = APIRouter(prefix="/api/generated", tags=["generated"])


@router.get("")
def list_generated(
    format: str | None = Query(default=None),
    tone: str | None = Query(default=None),
    limit: int = Query(default=50),
    offset: int = Query(default=0),
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_user),
):
    clauses = ["1=1"]
    params: list[object] = []
    if format:
        clauses.append("format = ?")
        params.append(format)
    if tone:
        clauses.append("tone = ?")
        params.append(tone)

    total = conn.execute(
        f"SELECT COUNT(*) FROM generated_items WHERE {' AND '.join(clauses)}",
        tuple(params),
    ).fetchone()[0]
    rows = conn.execute(
        f"""
        SELECT * FROM generated_items
        WHERE {" AND ".join(clauses)}
        ORDER BY created_at DESC
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


@router.get("/{generated_id}")
def get_generated(
    generated_id: str,
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(require_user),
):
    row = conn.execute(
        "SELECT * FROM generated_items WHERE id = ?", (generated_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Generated content not found")
    return dict(row)
