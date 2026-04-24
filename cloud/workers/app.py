import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from shared.db import get_connection, init_schema
from workers.ingest_worker import process_ingest_job
from workers.repurpose_worker import process_repurpose_job

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = get_connection()
        init_schema(_conn)
    return _conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_conn()
    yield
    if _conn is not None:
        _conn.close()


app = FastAPI(title="Content Intelligence Hub Worker", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "worker"}


@app.post("/tasks/jobs/{job_id}")
def process_job(job_id: str, body: dict):
    job_type = body.get("job_type")
    if job_type == "repurpose":
        return process_repurpose_job(_get_conn(), job_id)
    if job_type == "ingest":
        return process_ingest_job(_get_conn(), job_id)
    raise HTTPException(status_code=400, detail=f"Unsupported job type: {job_type}")
