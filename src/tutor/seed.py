"""Reset the POC state and seed two demo learners with different learner models."""
from __future__ import annotations

import shutil

from . import store
from .config import VAR_DIR, db_path
from .setup_content import build

DEMO_LEARNERS = {
    # Learner A: weak on factorisation, qe_m04 already suspected, responded well to counterexamples before.
    "L-A": {"alias": "Student A", "mastery": {"qe01": 0.90, "qe02": 0.85, "qe03": 0.70, "qe04": 0.20, "qe05": 0.30},
            "misconceptions": {"qe_m04": "suspected"}, "styles": [("qe_m04", "counterexample", 1, 0)]},
    # Learner B: has mastered qe01-qe04; no misconceptions on record.
    "L-B": {"alias": "Student B", "mastery": {"qe01": 0.97, "qe02": 0.96, "qe03": 0.96, "qe04": 0.96, "qe05": 0.50},
            "misconceptions": {}, "styles": []},
}
ALIASES = {"A": "L-A", "B": "L-B"}


def seed_learner(conn, learner_id: str, spec: dict) -> None:
    conn.execute("INSERT OR REPLACE INTO learners VALUES (?,?,?)", (learner_id, spec.get("alias", learner_id), store.now()))
    for cid, p in spec.get("mastery", {}).items():
        conn.execute("INSERT OR REPLACE INTO mastery VALUES (?,?,?,?)", (learner_id, cid, p, store.now()))
    for mid, status in spec.get("misconceptions", {}).items():
        conn.execute("INSERT OR REPLACE INTO misconceptions VALUES (?,?,?,?,?)", (learner_id, mid, status, 1, store.now()))
    for mid, style, ok, bad in spec.get("styles", []):
        conn.execute("INSERT OR REPLACE INTO explanations VALUES (?,?,?,?,?)", (learner_id, mid, style, ok, bad))


def reset_and_seed() -> dict:
    counts = build()
    if VAR_DIR.exists():
        shutil.rmtree(VAR_DIR)
    conn = store.connect(db_path("tutor.db"))
    for lid, spec in DEMO_LEARNERS.items():
        seed_learner(conn, lid, spec)
    conn.close()
    return counts
