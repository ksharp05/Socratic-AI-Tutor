# R1 · Domain and product lead · Lakshya (Lead)

**What the guide asks.** The R1 owner:
- defines the problem, the users, the data, the written policies and the golden-set content;
- talks to the domain expert;
- owns the demo script;
- checks the held-out cases against the written policy.

## What exists

| Piece | Where |
|---|---|
| Problem, users, success criteria | Report section 1 |
| Teaching policy, with rule IDs that prompts, guards and tests cite | `Docs/policy/TEACHING_POLICY.md` |
| Dataset: concepts, misconception catalogue (30 types), cards, quiz pairs | `content/dataset-v0.10.0/` |
| Decision log D-1 to D-9 | `Docs/DECISIONS.md` |
| DPDP readiness note, safe-messaging audit (F3), crisis-masking review (F2) | `Docs/policy/DPDP_READINESS.md`, `Docs/m3/F2_CRISIS_MASKING_REVIEW.md` |
| Demo script | `Docs/demo/DEMO_SCRIPT.md` |
| What a pilot needs | Report section 8 |

## Who built it

All of the above was done by Lakshya (ksharp05), with Claude Code drafting. R1 is the Lead's own role.

## How it works

**The teaching policy is enforced in code, not only in prompts.**
- **TP-M4:** the tutor never solves the student's own problem.
- **TP-H1:** hints are questions, in at most three stages.
- **TP-A2:** after the last hint, the tutor gives a parallel worked example with different numbers.
- **TP-M2:** quizzes get no hints and no model call.
- **Correctness:** code decides whether an answer is right.

The guards and tests cite these IDs.

**Decisions that changed the design:**
- **D-7:** Gemma 4 31B was chosen as the classifier. It is switched off because it blocks 18% of safe messages.
- **D-8:** crisis masking is off by default. It hid 7 of 8 disguised disclosures.
- **D-9:** the B3 safety pre-registration is frozen.

## Likely questions

- **Who is the user, and what outcome do you measure?** Class 10 students (children) and their teacher. We measure answer leaks, diagnosis, quiz change on simulated students, and safety on attack sets.
- **Which decisions are made by the model, by code and by a person?**
  - The model writes wording and proposes a diagnosis.
  - Code routes, grades, checks leaks and checks citations.
  - A person (the teacher) approves question sets.
- **Why is the classifier off?** Its false-block rate. Children would be wrongly refused about 1 time in 5.
- **What is needed before a pilot?** Guardian consent (DPDP), named safeguarding review of flags, teacher-approved content, outside test sets, and an institution-owned key with a cap.

**Files to open:** `Docs/DECISIONS.md`, `Docs/policy/TEACHING_POLICY.md`, report sections 1 and 8.
