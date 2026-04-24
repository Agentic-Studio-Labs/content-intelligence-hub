import sqlite3

from fastapi import Depends, Header, HTTPException

from shared.auth import get_user_for_session
from shared.db import get_connection, init_schema


def get_db():
    conn = get_connection()
    init_schema(conn)
    try:
        yield conn
    finally:
        conn.close()


def require_user(
    authorization: str | None = Header(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    return get_user_for_session(conn, token)
