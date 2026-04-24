"""Verify OIDC bearer tokens from Cloud Tasks (defense in depth on the worker)."""

from typing import Annotated

from fastapi import Header, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from shared.config import settings


def require_cloud_tasks_oidc(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    verify_cloud_tasks_bearer(authorization)


def verify_cloud_tasks_bearer(authorization: str | None) -> None:
    if settings.skip_worker_oidc:
        return

    audience = (settings.worker_oidc_audience or settings.worker_url or "").rstrip("/")
    if not audience:
        raise HTTPException(
            status_code=500,
            detail="Worker OIDC not configured: set CIH_CLOUD_WORKER_URL or CIH_CLOUD_WORKER_OIDC_AUDIENCE",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing Authorization bearer token"
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=audience,
        )
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid OIDC token")

    expected = (settings.tasks_service_account_email or "").strip()
    if expected and info.get("email") != expected:
        raise HTTPException(status_code=403, detail="Unexpected OIDC principal")
