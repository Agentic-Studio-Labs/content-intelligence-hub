import json
import sqlite3
import uuid

from shared.db import get_workspace, list_rows, utcnow


def create_job(
    conn: sqlite3.Connection,
    *,
    job_type: str,
    payload: dict,
    created_by: str | None,
    source_content_id: str | None = None,
) -> dict:
    workspace = get_workspace(conn)
    job_id = str(uuid.uuid4())
    now = utcnow()
    conn.execute(
        """
        INSERT INTO jobs
        (id, workspace_id, job_type, status, source_content_id, payload_json, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            workspace["id"],
            job_type,
            "queued",
            source_content_id,
            json.dumps(payload),
            created_by,
            now,
            now,
        ),
    )
    conn.commit()
    return get_job(conn, job_id)


def get_job(conn: sqlite3.Connection, job_id: str) -> dict:
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(job_id)

    artifacts = list_rows(
        conn,
        "SELECT * FROM artifacts WHERE job_id = ? ORDER BY created_at DESC",
        (job_id,),
    )
    result = dict(row)
    result["payload"] = json.loads(result.pop("payload_json") or "{}")
    result["result"] = json.loads(result.pop("result_json") or "null")
    result["artifacts"] = artifacts
    return result


def list_jobs(
    conn: sqlite3.Connection, *, job_type: str | None = None, status: str | None = None
) -> list[dict]:
    clauses = ["1=1"]
    params: list[str] = []
    if job_type:
        clauses.append("job_type = ?")
        params.append(job_type)
    if status:
        clauses.append("status = ?")
        params.append(status)

    rows = list_rows(
        conn,
        f"SELECT * FROM jobs WHERE {' AND '.join(clauses)} ORDER BY created_at DESC",
        tuple(params),
    )
    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "job_type": row["job_type"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "source_content_id": row["source_content_id"],
                "result_preview": None,
            }
        )
    return items


def update_job_status(
    conn: sqlite3.Connection,
    job_id: str,
    *,
    status: str,
    error: str | None = None,
    result: dict | None = None,
) -> None:
    conn.execute(
        "UPDATE jobs SET status = ?, error = ?, result_json = ?, updated_at = ? WHERE id = ?",
        (
            status,
            error,
            json.dumps(result) if result is not None else None,
            utcnow(),
            job_id,
        ),
    )
    conn.commit()


def add_artifact(
    conn: sqlite3.Connection,
    *,
    job_id: str,
    kind: str,
    path: str,
    content_type: str = "text/plain",
    preview_text: str | None = None,
) -> None:
    workspace = get_workspace(conn)
    conn.execute(
        """
        INSERT INTO artifacts (id, workspace_id, job_id, kind, path, content_type, preview_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            workspace["id"],
            job_id,
            kind,
            path,
            content_type,
            preview_text,
            utcnow(),
        ),
    )
    conn.commit()
