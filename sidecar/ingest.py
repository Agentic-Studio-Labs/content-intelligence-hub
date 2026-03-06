import uuid
import json
import logging
from pathlib import Path

from db import insert_content
from sources.local_files import LocalFileSource
from embeddings import EmbeddingModel

logger = logging.getLogger(__name__)

_source = LocalFileSource()


def ingest_file(conn, file_path: str, embedding_model: EmbeddingModel) -> dict | None:
    raw = _source.extract(file_path)
    if raw is None:
        return None
    existing = conn.execute(
        "SELECT id FROM marketing_content WHERE source_path = ?", (file_path,)
    ).fetchone()
    content_id = existing["id"] if existing else str(uuid.uuid4())
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
        logger.debug(f"VSS insert skipped: {e}")
    logger.info(f"Ingested: {raw.title} ({file_path})")
    return content


def ingest_directory(conn, dir_path: str, embedding_model: EmbeddingModel) -> list[dict]:
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
    name = Path(raw.path).stem.lower()
    if "case-study" in name or "case_study" in name:
        return "case_study"
    if "email" in name:
        return "email"
    if "landing" in name:
        return "landing_page"
    return "blog"
