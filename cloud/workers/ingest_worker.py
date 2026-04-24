import json
import sqlite3
import uuid
from pathlib import Path

from shared.db import utcnow
from shared.embeddings import EmbeddingModel
from shared.jobs import add_artifact, get_job, update_job_status
from shared.storage import sanitize_object_path, write_object
from workers.local_file_source import LocalFileSource

_source = LocalFileSource()


def _infer_content_type(file_path: str) -> str:
    name = Path(file_path).stem.lower()
    if "case-study" in name or "case_study" in name:
        return "case_study"
    if "email" in name:
        return "email"
    if "landing" in name:
        return "landing_page"
    return "blog"


def _upsert_content(
    conn: sqlite3.Connection, *, object_path: str, raw, embedding: list[float]
) -> str:
    existing = conn.execute(
        "SELECT id FROM content_items WHERE source_path = ?",
        (object_path,),
    ).fetchone()
    content_id = existing["id"] if existing else str(uuid.uuid4())
    now = utcnow()
    conn.execute(
        """
        INSERT OR REPLACE INTO content_items
        (id, workspace_id, title, body, summary, content_type, persona, funnel_stage, channel, topics, performance_score, url, source_path, embedding_json, created_at, updated_at)
        VALUES (?, COALESCE((SELECT workspace_id FROM content_items WHERE id = ?), (SELECT id FROM workspaces ORDER BY created_at LIMIT 1)), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM content_items WHERE id = ?), ?), ?)
        """,
        (
            content_id,
            content_id,
            raw.title,
            raw.body,
            raw.body[:200] if len(raw.body) > 200 else raw.body,
            raw.content_type or _infer_content_type(object_path),
            "general",
            "awareness",
            "cloud_upload",
            json.dumps(raw.metadata.get("topics", [])),
            0,
            "",
            object_path,
            json.dumps(embedding),
            content_id,
            now,
            now,
        ),
    )
    conn.commit()
    return content_id


def process_ingest_job(conn: sqlite3.Connection, job_id: str) -> dict:
    job = get_job(conn, job_id)
    object_paths = job["payload"].get("object_paths", [])
    model = EmbeddingModel()
    ingested: list[dict] = []

    update_job_status(conn, job_id, status="running")

    for object_path in object_paths:
        local_path = sanitize_object_path(object_path)
        raw = _source.extract(str(local_path))
        if raw is None:
            continue

        embedding = model.embed_text(f"{raw.title} {raw.body[:500]}")
        content_id = _upsert_content(
            conn, object_path=object_path, raw=raw, embedding=embedding
        )
        normalized_path = f"normalized/{job_id}/{Path(object_path).stem}.txt"
        write_object(normalized_path, raw.body.encode("utf-8"))
        add_artifact(
            conn,
            job_id=job_id,
            kind="source-text",
            path=normalized_path,
            preview_text=raw.body[:200],
        )
        ingested.append(
            {
                "id": content_id,
                "title": raw.title,
                "object_path": object_path,
                "artifact_path": normalized_path,
            }
        )

    result = {"ingested": len(ingested), "items": ingested}
    update_job_status(conn, job_id, status="succeeded", result=result)
    return result
