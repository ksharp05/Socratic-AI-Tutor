"""The tutor configurations ("arms") an experiment compares. The harness calls make_app; each arm is built by its
owner, so the evaluation never writes the system it measures (separation rules, D-1).

| Arm | Experiment | Owner | State |
|---|---|---|---|
| c2 | E1 team of agents; the base of E2–E4 | R3 | the POC session graph |
| c1 | E1 single agent with every tool | R3 | not built |
| c0 | E1 fixed workflow | R3 | not built |
| memory_off | E4a no learner model | R2 | not built |
| direct_answers | E4b tutor may answer, leak guard off | R3 + R4 | not built |

Defences are a separate switch (`defences` in the config). Per-layer switches for E2 are R4's to add.
"""
from __future__ import annotations

OWNERS = {"c2": "R3", "c1": "R3", "c0": "R3", "memory_off": "R2", "direct_answers": "R3 + R4"}


def make_app(arm: str, *, defences: bool, llm_mode: str | None, db_name: str, checkpoint_name: str):
    if arm == "c2":
        from tutor.app import TutorApp
        return TutorApp(defences=defences, llm_mode=llm_mode, db_name=db_name, checkpoint_name=checkpoint_name)
    if arm in OWNERS:
        raise SystemExit(f"Arm '{arm}' is not built yet. Its owner is {OWNERS[arm]}; the contract is in "
                         f"src/tutor_eval/arms.py and eval/README.md.")
    raise SystemExit(f"Unknown arm '{arm}'. Known arms: {', '.join(OWNERS)}.")
