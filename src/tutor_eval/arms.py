"""The tutor configurations ("arms") an experiment compares. The harness calls make_app; each arm is built by its
owner, so the evaluation never writes the system it measures (separation rules, D-1).

| Arm | Experiment | Owner | State |
|---|---|---|---|
| c2 | E1 team of agents; the base of E2Ã¢â‚¬â€œE4 | R3 | the POC session graph |
| c1 | E1 single-controller development baseline | R3 | implemented; offline smoke only |
| c0 | E1 fixed teaching workflow | R3 | isolated development variant |
| memory_off | E4a no learner model | R2 | isolated development variant |
| direct_answers | E4b registered telling | R3 + R4 | isolated fixture-only variant |

Defences are a separate switch (`defences` in the config). Per-layer switches for E2 are R4's to add.
"""
from __future__ import annotations

OWNERS = {"c2": "R3", "c1": "R3", "c0": "R3", "memory_off": "R2", "direct_answers": "R3 + R4"}


def make_app(arm: str, *, defences: bool, llm_mode: str | None, db_name: str, checkpoint_name: str,
             allow_dev_fixtures: bool = False, contextual: bool = False, playbook: dict | None = None):
    if contextual or arm in ("c0", "memory_off", "direct_answers"):
        from tutor_eval.experiment_arms import make_experiment_app
        return make_experiment_app(arm, defences=defences, llm_mode=llm_mode, db_name=db_name,
                                   checkpoint_name=checkpoint_name, allow_dev_fixtures=allow_dev_fixtures, playbook=playbook)
    if arm == "c2":
        from tutor.app import TutorApp
        return TutorApp(defences=defences, llm_mode=llm_mode, db_name=db_name, checkpoint_name=checkpoint_name,
                        allow_dev_fixtures=allow_dev_fixtures)
    if arm == "c1":
        from tutor_eval.single_agent import SingleAgentTutor
        return SingleAgentTutor(defences=defences, llm_mode=llm_mode, db_name=db_name, checkpoint_name=checkpoint_name,
                        allow_dev_fixtures=allow_dev_fixtures)
    if arm in OWNERS:
        raise SystemExit(f"Arm '{arm}' is not built yet. Its owner is {OWNERS[arm]}; the contract is in "
                         f"src/tutor_eval/arms.py and eval/README.md.")
    raise SystemExit(f"Unknown arm '{arm}'. Known arms: {', '.join(OWNERS)}.")
