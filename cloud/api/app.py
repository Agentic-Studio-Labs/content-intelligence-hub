import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    auth,
    content,
    generated,
    integrations,
    jobs,
    me,
    settings,
    uploads,
)
from shared.config import settings as cloud_settings
from shared.db import get_connection, init_schema

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


app = FastAPI(title="Content Intelligence Hub Cloud API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(content.router)
app.include_router(generated.router)
app.include_router(jobs.router)
app.include_router(settings.router)
app.include_router(integrations.router)
app.include_router(uploads.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "port": cloud_settings.port,
        "mode": "cloud",
    }
