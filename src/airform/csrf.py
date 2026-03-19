"""Zero-config CSRF protection for AirForm.

Tokens are HMAC-signed with a per-process secret that's auto-generated
on import. No configuration needed for single-worker deployments. For
multi-worker production, set the AIRFORM_SECRET environment variable
so all workers share the same secret.

Token format: timestamp:nonce:signature
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time

#: Secret key for signing CSRF tokens. Auto-generated per process,
#: or read from AIRFORM_SECRET env var for multi-worker deployments.
_SECRET: bytes = os.environ.get("AIRFORM_SECRET", "").encode() or secrets.token_bytes(32)

#: How long a CSRF token stays valid (seconds). Default: 1 hour.
CSRF_MAX_AGE: int = 3600

#: Name of the hidden input field in the form.
CSRF_FIELD_NAME: str = "csrf_token"


def generate_csrf_token() -> str:
    """Generate a signed CSRF token."""
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    payload = f"{timestamp}:{nonce}"
    sig = hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def validate_csrf_token(token: str | None, *, max_age: int = CSRF_MAX_AGE) -> str | None:
    """Validate a CSRF token. Returns an error message, or None if valid."""
    if not token:
        return "Missing CSRF token."

    parts = token.split(":")
    if len(parts) != 3:
        return "Invalid CSRF token."

    timestamp_str, nonce, sig = parts

    expected_payload = f"{timestamp_str}:{nonce}"
    expected_sig = hmac.new(_SECRET, expected_payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        return "Invalid CSRF token."

    try:
        token_time = int(timestamp_str)
    except ValueError:
        return "Invalid CSRF token."

    if time.time() - token_time > max_age:
        return "CSRF token has expired. Please resubmit the form."

    return None


def csrf_hidden_input() -> str:
    """Render a hidden input with a fresh CSRF token."""
    token = generate_csrf_token()
    return f'<input type="hidden" name="{CSRF_FIELD_NAME}" value="{token}">'
