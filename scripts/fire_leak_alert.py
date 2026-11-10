"""Make Grafana's answer-leak alert fire once, for the demo.

A deliberately leaky tutor answers 20 short questions. Its model always drafts "The answer is ...", so the
output guard blocks each draft, writes a "fail" decision to the trace table and sends a safe template
instead. The API reads those rows into tutor_answer_leak_blocked_total, Prometheus scrapes them, and
Grafana's "Answer-leak spike" rule, once it is provisioned, fires about three minutes later. No live
model is called, and no student sees a leaked draft.

Run it inside the API container, so it writes to the database the API reads:
    docker compose exec -T api python - < scripts/fire_leak_alert.py
"""
import os
import uuid

os.environ["TUTOR_LLM"] = "stub"

from tutor.app import TutorApp  # noqa: E402
from tutor.llm import LLM  # noqa: E402
from tutor.seed import seed_learner  # noqa: E402

DEMO_LEARNER = "L-LEAK-DEMO"
QUESTIONS = ["Can you explain what the discriminant tells us about the roots?",
             "Why can a quadratic equation have two roots?"]
LEAKY_DRAFT = "The answer is x = 0 and x = 5. Do you see why?"


class LeakyLLM(LLM):
    """Pretends to be a live model whose tutor drafts always give the answer away."""

    def __init__(self, conn):
        super().__init__(conn, "stub")
        self.enabled = True

    def complete(self, *, node: str, **_) -> str | None:
        return LEAKY_DRAFT if node == "tutor" else None


def run(tutor: TutorApp, sessions: int = 20) -> int:
    """Run the leaky sessions and return how many drafts the output guard blocked."""
    if not tutor.conn.execute("SELECT 1 FROM learners WHERE learner_id=?", (DEMO_LEARNER,)).fetchone():
        seed_learner(tutor.conn, DEMO_LEARNER, {"alias": "Leak-alert demo"})
    start = tutor.conn.execute("SELECT COALESCE(MAX(id), 0) FROM trace_events").fetchone()[0]
    tutor.llm = LeakyLLM(tutor.conn)
    for n in range(sessions):
        tutor.turn(f"leak-demo-{uuid.uuid4().hex[:8]}", DEMO_LEARNER, QUESTIONS[n % len(QUESTIONS)])
    return tutor.conn.execute("SELECT COUNT(*) FROM trace_events WHERE id > ? AND node='output_guard' "
                              "AND kind='decision' AND name='fail'", (start,)).fetchone()[0]


if __name__ == "__main__":
    tutor = TutorApp()
    try:
        print(f"{run(tutor)} leaky drafts blocked; the alert should fire in about 3 minutes.")
    finally:
        tutor.close()
