import sqlite3
import uuid

from shared.config import settings
from shared.db import utcnow
from shared.jobs import add_artifact, get_job, update_job_status
from shared.providers.anthropic import AnthropicProvider
from shared.storage import write_object
from workers.repurpose_graph import build_repurpose_graph


def _get_provider() -> AnthropicProvider:
    api_key = settings.anthropic_api_key or ""
    if not api_key:
        raise RuntimeError("CIH_CLOUD_ANTHROPIC_API_KEY is not configured")
    return AnthropicProvider(api_key=api_key)


def process_repurpose_job(conn: sqlite3.Connection, job_id: str) -> dict:
    job = get_job(conn, job_id)
    payload = job["payload"]
    source_content_id = payload["content_id"]
    source = conn.execute(
        "SELECT * FROM content_items WHERE id = ?",
        (source_content_id,),
    ).fetchone()
    if source is None:
        update_job_status(
            conn, job_id, status="failed", error="Source content not found"
        )
        raise ValueError("Source content not found")

    provider = _get_provider()
    source_dict = dict(source)
    update_job_status(conn, job_id, status="running")
    app = build_repurpose_graph(provider)
    final_state = app.invoke(
        {
            "source_content": source_dict,
            "requested_formats": payload.get("formats", []),
            "tone": payload.get("tone", "professional"),
            "custom_instructions": payload.get("custom_instructions", {}),
            "generated_content": {},
            "quality_scores": {},
            "errors": [],
        }
    )

    generated_content: dict[str, str] = final_state.get("generated_content", {})
    quality_scores: dict[str, float] = final_state.get("quality_scores", {})
    analysis = final_state.get("analysis", {})
    saved_ids: dict[str, str] = {}

    for fmt, body in generated_content.items():
        object_path = f"generated/{job_id}/{fmt}.txt"
        write_object(object_path, body.encode("utf-8"))
        add_artifact(
            conn,
            job_id=job_id,
            kind=fmt,
            path=object_path,
            preview_text=body[:200],
        )

        generated_id = str(uuid.uuid4())
        saved_ids[fmt] = generated_id
        conn.execute(
            """
            INSERT INTO generated_items
            (id, workspace_id, source_content_id, source_title, format, tone, body, quality_score, prompts, artifact_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                generated_id,
                source_dict.get("workspace_id"),
                source_content_id,
                source_dict["title"],
                fmt,
                payload.get("tone", "professional"),
                body,
                quality_scores[fmt],
                "{}",
                object_path,
                utcnow(),
            ),
        )

    conn.commit()
    result = {
        "success": len(generated_content) > 0,
        "generated_content": generated_content,
        "quality_scores": quality_scores,
        "analysis": analysis,
        "errors": final_state.get("errors", []),
        "saved_ids": saved_ids,
    }
    update_job_status(conn, job_id, status="succeeded", result=result)
    return result
