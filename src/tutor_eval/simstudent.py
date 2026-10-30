"""Code-owned simulated student. The card and the knowledge state live here; the tutor never sees them.

These buggy rules are the simulator's own (D17). In the POC the assistant wrote both these and the
diagnostician's rules; R5 should rewrite this file independently before any reported experiment.
"""
from __future__ import annotations

import random

from tutor import mathcore

SLIP, GUESS, LEARN = 0.10, 0.05, 0.15
OPENERS = {
    "qe_m04": "I solved x^2 = 7x by dividing both sides by x and got x = 7. Is that right?",
    "qe_m05": "For x^2 = 16 I took the square root and got x = 4. Is that all?",
    "qe_m01": "Is x^2 + 3 = x^2 + 2x a quadratic equation? It has x squared in it.",
}
BELIEFS = {
    "qe_m04": "I think dividing by x is always safe, so there is only one answer.",
    "qe_m05": "I think a square root only gives the positive value.",
    "qe_m01": "Anything with x squared is quadratic, isn't it?",
}


class SimStudent:
    def __init__(self, card: dict, seed: int):
        hidden = card["hidden_card"]
        self.student_id = card["student_id"]
        self.mastery = dict(hidden["true_mastery_by_concept"])
        self.active = list(hidden["seeded_misconception_ids"])
        self.targets = list(hidden["target_concept_ids"])
        self.rng = random.Random(seed)

    def opener(self) -> str:
        return next((OPENERS[m] for m in self.active if m in OPENERS), "Can you help me with quadratic equations?")

    def reply_to_probe(self) -> str:
        return next((BELIEFS[m] for m in self.active if m in BELIEFS), "Hmm, I'm not sure. Maybe?")

    def answer(self, problem: dict) -> str:
        values = list(mathcore.compute_key(problem)["key"]["values"])
        g = problem["givens"]
        if "qe_m05" in self.active and g.get("b") == 0 and len(values) == 2:
            return "x = " + next(v for v in values if not v.startswith("-"))
        if "qe_m04" in self.active and len(values) == 2:
            kept = [v for v in values if v != "0"] if "0" in values else values[-1:]
            return "x = " + kept[0]
        p = sum(self.mastery.get(c, 0.25) for c in problem["concept_ids"]) / len(problem["concept_ids"])
        if self.rng.random() < p * (1 - SLIP) + (1 - p) * GUESS:
            return "no real roots" if not values else " or ".join(f"x = {v}" for v in values)
        return "x = 1" if not values else " or ".join(f"x = -({v})" for v in values)

    def learn(self, concept_ids: list[str]) -> None:
        for c in concept_ids:
            self.mastery[c] = self.mastery.get(c, 0.25) + (1 - self.mastery.get(c, 0.25)) * LEARN

    def maybe_clear(self, misconception_id: str, diagnosed: bool, targeted: bool) -> bool:
        """Pre-registered POC rule: clears with p=0.7 only if diagnosed AND targeted. Generic feedback never clears."""
        if misconception_id in self.active and diagnosed and targeted and self.rng.random() < 0.7:
            self.active.remove(misconception_id)
            return True
        return False
