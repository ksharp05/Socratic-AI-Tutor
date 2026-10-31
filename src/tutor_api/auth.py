"""Bearer-token auth. The role and the learner (or teacher) ID come only from the token (policy TP-D6).

Tokens are read from TUTOR_API_TOKENS as comma-separated `token:role:id` entries, for example
`TUTOR_API_TOKENS="tok1:student:L-A,tok2:teacher:T-001"`. Nothing in a request body can change them.

When TUTOR_API_TOKENS is unset, the documented development tokens in DEV_TOKENS are used. They are public,
so never expose a server that runs on them.
"""
from __future__ import annotations

import hmac
import logging
import os
from dataclasses import dataclass

ROLES = ("student", "teacher")
DEV_TOKENS = "dev-student-a:student:L-A,dev-student-b:student:L-B,dev-teacher:teacher:T-001"

log = logging.getLogger("tutor_api")


@dataclass(frozen=True)
class Principal:
    role: str
    subject_id: str  # learner ID for a student, teacher ID for a teacher

    @property
    def is_teacher(self) -> bool:
        return self.role == "teacher"


def parse_tokens(spec: str) -> dict[str, Principal]:
    tokens: dict[str, Principal] = {}
    for entry in (e.strip() for e in spec.split(",")):
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) != 3 or not all(p.strip() for p in parts):
            raise ValueError("each TUTOR_API_TOKENS entry must be token:role:id")
        token, role, subject = (p.strip() for p in parts)
        if role not in ROLES:
            raise ValueError(f"unknown role {role!r} in TUTOR_API_TOKENS; use one of {ROLES}")
        tokens[token] = Principal(role, subject)
    if not tokens:
        raise ValueError("TUTOR_API_TOKENS is set but defines no tokens")
    return tokens


def load_tokens(spec: str | None = None) -> dict[str, Principal]:
    if spec is None:
        spec = os.environ.get("TUTOR_API_TOKENS")
        if not spec:
            log.warning("TUTOR_API_TOKENS is not set: using the public development tokens (see Docs/deploy/README.md)")
            spec = DEV_TOKENS
    return parse_tokens(spec)


def lookup(tokens: dict[str, Principal], presented: str) -> Principal | None:
    """Constant-time comparison against every known token."""
    found = None
    for token, principal in tokens.items():
        if hmac.compare_digest(token.encode(), presented.encode()):
            found = principal
    return found
