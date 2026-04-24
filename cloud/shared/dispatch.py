import sqlite3

from shared.config import settings
from shared.jobs import update_job_status
from workers.ingest_worker import process_ingest_job
from workers.repurpose_worker import process_repurpose_job


def dispatch_job(conn: sqlite3.Connection, job_id: str, job_type: str) -> None:
    if settings.queue_mode != "inline":
        return

    try:
        if job_type == "repurpose":
            process_repurpose_job(conn, job_id)
        elif job_type == "ingest":
            process_ingest_job(conn, job_id)
    except Exception as exc:
        update_job_status(conn, job_id, status="failed", error=str(exc))
