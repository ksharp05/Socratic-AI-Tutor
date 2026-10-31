"""The evaluation pipeline (R5): leak checker, simulator, harness, metrics, judge parsing, agreement and security.
All offline: the tutor runs on its stub and no API key is needed."""
import json

import pytest

from socratic_data import math_kernel as mk
from socratic_data import tasks as kt
from tutor.config import ROOT
from tutor_eval import agreement, harness, judge, leakcheck, security, simulator

ROOTS = mk.finite_set([18, -1])
PROMPT = "x^2 - 17x - 18 = 0"


@pytest.mark.parametrize("text, expected, produced, level", [
    ("So x = 18 or x = -1.", ROOTS, None, "full"),
    ("One root is 18. What's the other?", ROOTS, None, "partial"),
    ("You gave 18. Check the other factor.", ROOTS, [mk.finite_set([18])], "none"),
    ("Look at the constant term, 18. Could either factor be zero?", ROOTS, None, "none"),
    ("Answer like 'x = 2 or x = -3' (or 'no real roots').", {"kind": "finite_set", "values": []}, None, "none"),
    ("This equation has no real roots.", {"kind": "finite_set", "values": []}, None, "full"),
    ("Correct: no real roots.", {"kind": "finite_set", "values": []}, [{"kind": "finite_set", "values": []}], "none"),
    ("The answer is 7.", mk.scalar(7), None, "full"),
    ("x = -4 + 3sqrt(3) or x = -4 - 3√3", mk.finite_set([mk.exact("-4+3*sqrt(3)"), mk.exact("-4-3*sqrt(3)")]), None, "full"),
    ("It is undefined.", {"kind": "defined_value", "defined": False, "value": None}, None, "full"),
])
def test_leak_levels_follow_the_teaching_policy(text, expected, produced, level):
    assert leakcheck.check(text, expected, prompt=PROMPT, produced=produced)["level"] == level


def test_buggy_rules_give_the_misconceptions_wrong_answer():
    solve = kt.problem("quadratic_solve", {"a": 1, "b": 0, "c": -16})
    assert simulator.render(simulator.RULES["qe_m05"](solve["task_type"], solve["givens"])) == "x = 4"
    term = kt.problem("ap_term", {"a": 3, "d": 2, "n": 5})
    assert simulator.render(simulator.RULES["ap_m03"](term["task_type"], term["givens"])) == "13"  # a + n*d, not 11
    tan = kt.problem("trig_triangle_ratio", {"opposite": 3, "adjacent": 4, "hypotenuse": 5, "reference": "A", "ratio": "tan"})
    assert simulator.render(simulator.RULES["tr_m04"](tan["task_type"], tan["givens"])) == "4/3"


def test_student_shows_the_misconception_and_clears_only_when_named_and_targeted():
    card = {"student_id": "t1", "hidden_card": {"seeded_misconception_ids": ["qe_m05"], "true_mastery_by_concept": {},
                                                 "persona": {}}}
    catalogue = {"qe_m05": {"concept_id": "qe03", "incorrect_rule": "Taking a square root gives only a positive answer."}}
    student = simulator.Student(card, catalogue, seed=1)
    solve = kt.problem("quadratic_solve", {"a": 1, "b": 0, "c": -9})
    assert student.answer(solve)["rule"] == "qe_m05"
    assert student.end_session(named={"qe_m05"}, targeted=set()) == []  # rule 1 needs both
    student.told.add("item-1")
    assert student.answer(solve, "item-1")["rule"] == "copied_from_tutor"  # rule 3


def test_harness_runs_end_to_end_and_passes_its_gate(tmp_path):
    run_dir = harness.run(ROOT / "eval" / "configs" / "dev_smoke.toml", out_dir=tmp_path)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["summary"]["sessions"] == 2 and manifest["summary"]["failures"] == 0
    assert manifest["gate"]["status"] == "pass" and manifest["partitions"] == ["development"]
    sessions = [json.loads(line) for line in (run_dir / "sessions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(s["turns"] and s["pre"] and s["post"] for s in sessions)
    assert "A development run: not a result." in (run_dir / "report.md").read_text(encoding="utf-8")


def test_harness_refuses_heldout_data_without_a_frozen_preregistration(tmp_path, monkeypatch):
    card = json.loads((ROOT / "eval" / "poc" / "students.json").read_text(encoding="utf-8"))[0]
    students = tmp_path / "students.json"
    students.write_text(json.dumps([{**card, "partition": "candidate_final"}]), encoding="utf-8")
    config = tmp_path / "heldout.toml"
    config.write_text(f'[run]\nname="x"\narm="c2"\ndefences=true\nllm="stub"\nseeds=[1]\nmax_turns=2\nturn_timeout_s=120\n'
                      f'[data]\nstudents="{students.as_posix()}"\nquiz_pairs="eval/poc/quiz_pairs.json"\n', encoding="utf-8")
    monkeypatch.setattr(harness, "ROOT", ROOT)
    with pytest.raises(SystemExit, match="held-out"):
        harness.run(config, out_dir=tmp_path)


def test_kappa():
    assert agreement.cohen_kappa(list("aabb"), list("abab")) == 0
    assert agreement.cohen_kappa(list("abab"), list("abab")) == 1
    assert agreement.weighted_kappa(["none", "full"], ["none", "partial"], agreement.ORDINAL["leak"]) < 1


def test_judge_output_is_checked_against_the_label_options():
    good = ('Fine. {"mistake_identification":"Yes","mistake_location":"No","revealing_of_the_answer":"No",'
            '"providing_guidance":"Yes","actionability":"Yes","coherence":"Yes","tutor_tone":"Neutral",'
            '"humanlikeness":"Yes","leak":"none","targets":["qe_m04"]}')
    assert judge.parse(good, {"qe_m04": "rule"})["targets"] == ["qe_m04"]
    with pytest.raises(ValueError):
        judge.parse(good.replace('"leak":"none"', '"leak":"maybe"'), {"qe_m04": "rule"})


def test_security_cases_hold_with_defences_and_break_without(tmp_path):
    fixtures = [ROOT / "eval" / "fixtures" / "security_smoke.jsonl"]
    on = json.loads((security.run(fixtures, "on", True, tmp_path) / "manifest.json").read_text(encoding="utf-8"))["summary"]
    off = json.loads((security.run(fixtures, "off", False, tmp_path) / "manifest.json").read_text(encoding="utf-8"))["summary"]
    assert on["attack_success_rate"] == 0 and on["false_block_rate"] == 0 and on["unsupported"] == 2
    assert off["attack_success_rate"] > 0


def test_simulator_validation_on_the_poc_cards():
    from tutor_eval import validate_sim
    cards = json.loads((ROOT / "eval" / "poc" / "students.json").read_text(encoding="utf-8"))
    pairs = {p["pair_id"]: (p["pre"], p["post"]) for p in json.loads((ROOT / "eval" / "poc" / "quiz_pairs.json").read_text(encoding="utf-8"))}
    catalogue = {m["misconception_id"]: m for m in (json.loads(line) for line in
                 (ROOT / "content/dataset-v0.10.0/misconceptions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
    rows = validate_sim.validate(cards, pairs, {}, catalogue)
    assert rows and all(r["ok"] for r in rows)
    assert all(r["clear_named_only"] == 0 and r["clear_targeted_only"] == 0 for r in rows)


def test_every_misconception_has_a_rule():
    catalogue = [json.loads(line) for line in (ROOT / "content/dataset-v0.10.0/misconceptions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert {m["misconception_id"] for m in catalogue} == set(simulator.RULES)


def test_llm_voice_keeps_values_and_falls_back_safely():
    card = {"student_id": "t2", "hidden_card": {"seeded_misconception_ids": ["qe_m05"], "true_mastery_by_concept": {},
                                                 "persona": {"communication_style": "brief"}}}
    student = simulator.Student(card, {"qe_m05": {"concept_id": "qe03", "incorrect_rule": "Roots are positive."}}, seed=1)

    class Fake:
        def __init__(self, reply):
            self.reply, self.prompts = reply, []

        def invoke(self, messages):
            self.prompts.append(messages[-1][1])
            return type("R", (), {"content": self.reply})()

    good = simulator.Voice("llm", client=Fake("hmm i got x = 3, thats right na?"))
    assert good.say("I got x = 3. Is that right?", student, keep=["x = 3"]) == "hmm i got x = 3, thats right na?"
    assert "Roots are positive." in good.client.prompts[0]  # the card is re-injected on every message
    dropped = simulator.Voice("llm", client=Fake("is that right?"))
    assert dropped.say("I got x = 3. Is that right?", student, keep=["x = 3"]) == "I got x = 3. Is that right?"
    leaky = simulator.Voice("llm", client=Fake("my qe_m05 says x = 3"))
    assert leaky.say("I got x = 3.", student, keep=["x = 3"]) == "I got x = 3."
    assert dropped.counts["fallback"] == leaky.counts["fallback"] == 1


def test_budget_stops_a_run_before_it_overspends(tmp_path):
    config = tmp_path / "capped.toml"
    config.write_text((ROOT / "eval" / "configs" / "dev_smoke.toml").read_text(encoding="utf-8").replace(
        "[gate]", "[budget]\nmax_llm_calls = 0\n\n[gate]"), encoding="utf-8")
    manifest = json.loads((harness.run(config, out_dir=tmp_path) / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["budget"]["sessions_not_run"] == ["sim_v2_010 seed 1", "sim_v2_013 seed 1"]
    assert manifest["summary"]["sessions"] == 0
