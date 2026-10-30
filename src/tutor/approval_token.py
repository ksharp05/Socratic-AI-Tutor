"""Approval tokens: HMAC over the payload's SHA-256 and the teacher's ID."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from .config import db_path


def _secret() -> bytes:
    env = os.environ.get("APPROVAL_SECRET")
    if env:
        return env.encode("utf-8")
    path = db_path("approval_secret")
    if not path.exists():
        path.write_text(secrets.token_hex(32), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip().encode("utf-8")


def mint(payload_sha256: str, teacher_id: str) -> str:
    return hmac.new(_secret(), f"{payload_sha256}:{teacher_id}".encode("utf-8"), hashlib.sha256).hexdigest()


def verify(token: str, payload_sha256: str, teacher_id: str) -> bool:
    return hmac.compare_digest(token, mint(payload_sha256, teacher_id))
