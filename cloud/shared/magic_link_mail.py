"""Send magic-link email via Resend (https://resend.com)."""

from __future__ import annotations

import logging
from urllib.parse import quote

import resend

from shared.config import settings

logger = logging.getLogger(__name__)


def magic_link_sign_in_url(token: str) -> str | None:
    base = (settings.magic_link_app_base_url or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}/#/login?token={quote(token, safe='')}"


def send_magic_link_email(to_email: str, token: str) -> bool:
    """
    Send the signed magic-link token by email.
    Returns True if Resend accepted the message, False if skipped or on failure.
    """
    if not settings.resend_api_key:
        return False

    resend.api_key = settings.resend_api_key
    sign_in = magic_link_sign_in_url(token)
    minutes = settings.magic_link_ttl_minutes

    if sign_in:
        html = f"""\
<!DOCTYPE html>
<html><body style="font-family: system-ui, sans-serif; line-height: 1.5;">
  <p>Sign in to Content Intelligence Hub:</p>
  <p><a href="{sign_in}" style="display:inline-block;padding:10px 16px;background:#111;color:#fff;\
text-decoration:none;border-radius:6px;">Sign in</a></p>
  <p style="color:#666;font-size:14px;">This link expires in about {minutes} minutes. \
If the button does not work, open the app and paste the token below.</p>
  <pre style="background:#f4f4f5;padding:12px;border-radius:6px;word-break:break-all;\
font-size:12px;">{token}</pre>
</body></html>"""
        text = (
            f"Sign in (copy into your browser if needed):\n{sign_in}\n\n"
            f"Or paste this token in the app (expires in ~{minutes} minutes):\n\n{token}\n"
        )
    else:
        html = f"""\
<!DOCTYPE html>
<html><body style="font-family: system-ui, sans-serif;">
  <p>Your Content Intelligence Hub sign-in token:</p>
  <pre style="background:#f4f4f5;padding:12px;border-radius:6px;word-break:break-all;\
font-size:12px;">{token}</pre>
  <p style="color:#666;font-size:14px;">Paste it in the app. Expires in about {minutes} minutes.</p>
  <p style="color:#666;font-size:14px;">Set <code>CIH_CLOUD_MAGIC_LINK_APP_BASE_URL</code> \
to add a one-click link in future emails.</p>
</body></html>"""
        text = (
            f"Paste this token in Content Intelligence Hub "
            f"(expires in ~{minutes} minutes):\n\n{token}\n"
        )

    params: resend.Emails.SendParams = {
        "from": settings.magic_link_from_email,
        "to": [to_email],
        "subject": "Your Content Intelligence Hub sign-in link",
        "html": html,
        "text": text,
        "tags": [{"name": "category", "value": "magic_link"}],
    }
    try:
        resend.Emails.send(params)
        return True
    except Exception:
        logger.exception("Resend magic link send failed for %s", to_email)
        return False
