"""Deterministic replies for learner messages that are about the session rather than a maths step.

The tutor used to answer these with the next hint or a generic first-step question, so a learner asking
"what should I practise next?" or "how do I delete my history?" got an unrelated maths prompt. Each reply
here states only what the app actually does; none reveals an answer, key, prompt or another learner's data.
"""
from __future__ import annotations

import re

INTENTS = [
    # Requests that must never be satisfied come first, so a mixed message is answered on its riskiest part.
    ("secret", re.compile(r"\b(api[ _-]?key|hidden (instructions|prompt)|system prompt|password|access token|secret)\b", re.I)),
    ("other_learner", re.compile(r"\b(learner_?[a-z0-9]+|another (student|learner)|other (students?|learners?)|someone else)'?s?\b.*"
                                 r"\b(grades?|results?|scores?|data|records?|progress)\b", re.I)),
    ("tool_action", re.compile(r"\b(run|execute)\b.*\b(command|shell|script|sql)\b|\bdelete all\b|\bdrop (the )?(table|database)\b", re.I)),
    ("score_change", re.compile(r"\b(mark|set|change|make)\b.*\b(quiz|score|result|answer)s?\b.*\b(correct|100|full marks?|right)\b", re.I)),
    ("deletion", re.compile(r"\b(delete|deletion|remove|erase|forget)\b.*\b(history|data|record|account|progress)\b", re.I)),
    ("approval", re.compile(r"\b(approv\w*|publish\w*)\b.*\b(question set|questions?|set)\b|\bquestion set\b.*\bapprov\w*", re.I)),
    ("trace", re.compile(r"\btrace\b|\bwhich (teaching )?tools\b|\bwhat tools\b", re.I)),
    ("citation", re.compile(r"\b(cit(e|ation|ations)|make up|made up|source does not|sources?)\b", re.I)),
    ("plan", re.compile(r"\b(what (should|do|can) i (practi[cs]e|study|work on|do) next|my (study |learning )?plan|"
                        r"practi[cs]e next|based on my quiz|my (own )?(quiz )?(results?|scores?|progress))\b", re.I)),
    ("frustration", re.compile(r"\b(frustrat\w*|confus\w*|give up|too hard|useless|annoy\w*|overwhelm\w*|stressed)\b", re.I)),
    ("smaller_step", re.compile(r"\b(smaller (hint|step|question)|break (it|this|the next step) (down|into)|"
                                r"simpler|step by step|not the (final )?answer)\b", re.I)),
]

POLICY = {
    "secret": "I can't share keys, passwords or my hidden instructions; they are never part of our chat.",
    "other_learner": "I can only show your own progress. Other learners' results stay private.",
    "tool_action": "I can't run commands or change any records; I only help with maths here.",
    "score_change": "I can't change scores. Only answers the checker marks correct count, and unattempted questions stay unscored.",
    "deletion": ("Your teacher handles deletion requests: ask them, and they can delete your connected learning record "
                 "from the Data requests page. Anonymous browser history is cleared separately."),
    "approval": ("Teachers review question sets in their own view, and only they can approve them. Approval is tied to "
                 "the exact content, so any edit needs a fresh approval before learners see it."),
    "trace": ("Your teacher can see a summary of which tools, checks and model calls were used in a session. "
              "It never shows hidden prompts, answer keys or private settings."),
    # Avoid "none": the answer-leak checker reads it as a claim that the equation has no real roots.
    "citation": ("I only cite reference cards I actually retrieved for this chapter. If a card doesn't cover your question, "
                 "I'll tell you instead of inventing a page."),
}


def intent(text: str) -> str | None:
    text = " ".join(text.split())
    for name, pattern in INTENTS:
        if pattern.search(text):
            return name
    return None


def plan_summary(plan: dict | None) -> str:
    steps = (plan or {}).get("steps") or []
    if not steps:
        if plan:
            return ("Your current study plan has no new steps. Ask your teacher about a review quiz "
                    "or what to study next.")
        return "You don't have a study plan yet. Try a practice question or a quiz, and I'll build one from how you do."
    lines = [f"{k}. {s['action'].replace('_', ' ').capitalize()}: {s['title']} ({s['why']})"
             for k, s in enumerate(steps[:3], 1)]
    reason = plan.get("replan_reason")
    head = f"Here is your current plan{f', updated {reason}' if reason else ''}:"
    return head + "\n" + "\n".join(lines) + "\nType 'practice' when you're ready for a question."


def reply(kind: str, *, plan: dict | None, next_step: str | None, in_quiz: bool) -> str:
    """`next_step` is the current hint prompt or first-step question, already safe to show."""
    if kind in POLICY:
        text = POLICY[kind]
    elif kind == "plan":
        return plan_summary(plan) if not in_quiz else (
            "Your plan updates when the quiz finishes, using your results. Answer this question when you're ready.")
    elif kind == "frustration":
        text = "That's understandable; this is a tricky step, and getting stuck is part of learning it."
    else:  # smaller_step
        text = "Sure, let's take a smaller step."
    if in_quiz:
        return text + " This is a quiz, so there are no hints; answer as best you can, or leave the quiz without a score."
    return f"{text} {next_step}" if next_step else text


def small_step(chapter: str) -> str:
    return {
        "arithmetic_progressions": "Which quantity is the first term, and what is the common difference?",
        "trigonometry": "Which angle is the reference angle in this question?",
        "quadratic_equations": "Which terms or factors can you identify before calculating?",
    }[chapter]


def clarify_step(chapter: str) -> str:
    return {
        "arithmetic_progressions": "Are you recognising a progression, finding a term, or finding a sum?",
        "trigonometry": "Is the difficult part choosing the reference angle, naming the sides, or choosing a ratio?",
        "quadratic_equations": "Is the difficult part arranging the equation, choosing a method, or checking possible solutions?",
    }[chapter]
