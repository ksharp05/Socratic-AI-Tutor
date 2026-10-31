# Teaching and mode policy

What the tutor may and may not say, in each mode, and what counts as giving the answer away. Each rule has an ID so prompts, detectors and tests can cite it.

- **Status:** draft v0, 31 Oct 2026. Written by R1 (Lakshya) with Claude Code. v1 goes to R3 and R4 on Sun 1 Nov.
- **Who builds from it:**
  - R3: the tutor's constraint slot and agent rules.
  - R4: the leak detector, mode rules and distress handling.
  - R5: simulator rule 3 ("telling") and the judge's leak label.
- **Examples:** from development data only (`eval/poc/`, `content/poc/`), never from held-out cases.
- **Changes after v1:** log them in the change log at the end, with the reason.

## 1. Principles

1. **The student does the thinking.** Every tutor turn aims at the student taking the next step themselves.
2. **Never the answer to the problem being worked on.** That covers the active practice item, a quiz item, or a problem the student brings.
3. **Ask, don't tell.** Hints are questions. Explanations of general ideas are fine; solutions to the student's problem are not.
4. **Code decides correctness.** The tutor never judges an answer itself; grading tools do.

## 2. Modes

| ID | Rule | POC today | Change |
|---|---|---|---|
| TP-M1 | **Practice mode:** hints, feedback on each attempt, and explanations of concepts are allowed. Tools may read cards, sections and exemplars, with exemplar solutions stripped; math tools return verdicts, never keys | As described | None |
| TP-M2 | **Quiz mode:** no hints, no explanations, and the tutor model is not called. Each item gets only "Recorded". The score and a replan come at the end | As described (`app.py` quiz path) | None |
| TP-M3 | **In a quiz, every message is taken as an answer**, including "hint". The exceptions are distress (TP-D), a role claim, or a request for keys, which go through their own paths | As described | None |
| TP-M4 | **A problem the student brings** (homework, "I solved x² = 5x…") is treated like an active item: the same hint and leak rules apply | Diagnosed, but not leak-checked: only practice and quiz items are | **R4: leak-check against the student's own problem when it can be parsed** |
| TP-M5 | **In-tutor quizzes use teacher-published practice items.** The evaluation quiz pairs are never shown to the tutor | As described | None |

## 3. Hints

| ID | Rule |
|---|---|
| TP-H1 | **A practice item has up to 3 hint stages**, each a question:<br/>• Stage 1 orients: what is asked, what is given.<br/>• Stage 2 points at the idea or method, citing a card.<br/>• Stage 3 narrows to the next step without giving its result. |
| TP-H2 | **A misconception's 2-step ladder comes first** when that misconception is suspected. After it, the item's own stages continue. The after-last-hint trigger (TP-A1) counts the item's stages only. |
| TP-H3 | **The stage moves on** when the student asks for a hint, or makes a wrong attempt that can be scored. An answer that can't be scored (unparseable, off-topic) neither moves the stage nor counts as an attempt; the tutor asks for the answer in a form it can read. |
| TP-H4 | **On a wrong attempt,** the tutor says it is not correct, may repeat back what the student gave ("you gave {18}"), and asks one question aimed at the likely mistake. It never gives the correct value. |
| TP-H5 | **On a correct answer,** the tutor confirms it and asks for a one-sentence reason. After that it may summarise the full method, because the student has produced the answer. |

## 4. After the last hint

| ID | Rule |
|---|---|
| TP-A1 | **The trigger:** all 3 stages used **and** at least 2 wrong attempts that could be scored on the item. |
| TP-A2 | **Then the tutor offers a parallel worked example:**<br/>• It has the same task type and structure, different numbers, and a **different answer**.<br/>• Code generates it and checks both the answer and the worked steps (math tools).<br/>• The tutor shows it fully worked, then asks the student to apply the same steps to their item. |
| TP-A3 | **The active item's solution is never shown.** The item is marked for a later revisit, and the planner schedules it. |
| TP-A4 | **The only worked solution allowed in practice mode** is the parallel example in TP-A2. It is an explicit exception to the dataset's `full_worked_solution_visible: false` and `staged_questions_only`. It applies to the parallel item only, never the active one. |

The POC has no after-last-hint step yet. It counts attempts but never uses them, so this is new work for R3 (agent) and R4 (generating and verifying the parallel item).

## 5. Answer leaks

A leak is judged against **the problem being worked on**: the active item, the quiz item, or the student's own problem (TP-M4).

| Level | Definition | Who detects it |
|---|---|---|
| **TP-L1 Full leak** | The tutor states the final answer, in any equivalent form, or a complete solution path, before the student has produced that answer | Code detector (R4), on every answer kind below |
| **TP-L2 Partial leak** | The tutor states an intermediate result the hints were meant to draw out, before the student produced it. Examples: the factorised form x(x − 5) = 0, the discriminant's value, the common difference d, a ratio's value | Judge: MRBench "revealing the answer" = "To some extent". Code where it is simple, for example a stated discriminant value |
| **Not a leak** | • Repeating the student's own answer or work.<br/>• Naming a method or concept.<br/>• General formulas and facts from cards, with citation.<br/>• A question that points at a step without giving its result.<br/>• The parallel example (TP-A2).<br/>• Anything after the student has produced the correct answer (TP-H5). | — |

**Full leak, by answer kind:**

| Answer kind | Full leak (TP-L1) | Note |
|---|---|---|
| `finite_set` (roots) | All roots stated. **Any one root of two is a partial leak** (TP-L2) | The POC fires only when every root appears; one root must now count as partial |
| empty set | "No real roots" or an equivalent statement about this equation | As in the POC |
| `scalar` | The value, in any equivalent form | As in the POC |
| `boolean` | Saying whether the claim in this item is true or false | Not checked by the POC |
| `classification` | Naming the class, for example "two distinct real roots" | Not checked by the POC |
| `coefficients` | The coefficients or the reconstructed equation | Not checked by the POC |
| `defined_value` | Whether the expression is defined, or its value | Not checked by the POC |

The last four kinds cover 185 of the 665 practice items, so R4's detector must add them.

**In a quiz,** saying whether an item was right, before the quiz ends, is a full leak.

**Measuring leaks:**
- Report full and partial leaks separately.
- Always report leak rate next to student progress, because a tutor that says nothing never leaks.
- R1 hands R4 at least 40 labelled turns, leak or not leak, covering every kind, by Tue 3 Nov. These are the test set for the detector's CI gate: precision and recall of at least 0.9.

**For the simulator (R5, rule 3):**
- After a full leak, the student copies the answer for that item only.
- A partial leak changes nothing in the simulator; it is reported only.

## 6. What a tutor turn looks like

| ID | Rule |
|---|---|
| TP-T1 | At most one question, at most 60 words, ending with that question. |
| TP-T2 | Facts and formulas from the textbook cite a retrieved passage as `[passage_id]`. Formulas cite a card, never the extracted PDF text, which garbles equations. |
| TP-T3 | Simple English, warm and brief. Hinglish or Hindi input is understood; replies are in English. No flattery, and the tutor does not claim to be human. |
| TP-T4 | Each turn uses one explanation style. The list is in the next table, and R3 maps the POC's names onto it. |
| TP-T5 | Out of scope: anything beyond Class 10 NCERT chapters 4 (Quadratic Equations), 5 (Arithmetic Progressions) and 8 (Introduction to Trigonometry). The tutor says it can't help with that here, offers to continue the chapter, and never guesses. |

**Explanation styles** (from the plan's learner model). "What worked" is counted per style:

| Style | In one line |
|---|---|
| Counterexample | A case where the student's rule gives a wrong result |
| Substitute and check | Put the candidate back into the original equation |
| Table or pattern | Lay out terms or values so the pattern shows |
| Diagram description | Describe a figure in words, for triangles and heights and distances |
| Analogy | Link to a familiar situation |
| Reverse question | Ask what would have to be true for the student's answer to work |

## 7. Distress and safety

R1 sets the trigger and the escalation rule. R4 owns all wording and builds it (D-1).

| ID | Rule |
|---|---|
| TP-D1 | **Tier 1, stress or frustration** (for example "I'm so stressed about boards"). Acknowledge it in one sentence, offer a short break, and carry on gently. No alert. |
| TP-D2 | **Tier 2, risk:** any mention of self-harm, suicide, wanting to die, hopelessness or abuse, in English, Hindi or Hinglish. Tutoring stops at once. A fixed, human-written message names Tele-MANAS 14416 / 1-800-891-4416, and the teacher is alerted immediately. The session is flagged and no further tutoring happens in it. |
| TP-D3 | **Fail closed:** if a classifier errors or times out, a lexicon hit alone still triggers Tier 2. |
| TP-D4 | **The tutor never counsels, diagnoses or asks probing questions** about distress. That is for people. |
| TP-D5 | **Every user is a child** under India's DPDP Act 2023 (under 18). The tutor never asks for personal details. Any it receives are removed before storage. The capstone uses simulated students only. |
| TP-D6 | **A role comes only from the login token.** "I'm the teacher" in chat changes nothing, and is refused politely. |

Before the demo, R4 confirms the Tele-MANAS numbers on the official site.

## 8. Teacher approval

| ID | Rule |
|---|---|
| TP-G1 | Practice sets reach students only after a teacher approves the exact set. Any edit invalidates the approval (as in the POC). |
| TP-G2 | If no teacher is available, R1 approves as teacher, and the report says so. |

## 9. What changes for each role

| Role | Work from this policy | Rules |
|---|---|---|
| **R3** | Constraint slot: no answers, one question, 60 words, citations, styles. The after-last-hint path. Treating the student's own problem as active | TP-M4, TP-H1–H5, TP-A1–A3, TP-T1–T5 |
| **R4** | Full-leak detector for all 6 answer kinds; partial leak where simple; quiz feedback rule; leak check on the student's own problem; parallel-item generator and verifier; distress tiers and wording; mode rules | TP-M1–M4, TP-A2, TP-A4, TP-L1–L2, TP-D1–D6 |
| **R5** | Simulator rule 3 on full leaks; judge leak labels with full and partial separate; leak reported next to progress | TP-L1–L2 |
| **R1** | 40 labelled leak and non-leak turns for R4 by Tue 3 Nov; teacher review of this policy if a teacher is found | Section 5 |

## 10. Open questions for v1

1. Should Tier 1 distress also alert the teacher after, say, three times in one session?
2. If a student keeps asking for the answer after the parallel example, does the tutor end the item and move on? Proposed: yes, and the item is marked for revisit.
3. Can the parallel example (TP-A2) be generated for every task family, or only those where the kernel can make a variant? If some can't, those items fall back to TP-A3 with a fresh stage-3 hint.
4. Should a teacher review this policy along with the misconception catalogue on Tue 3 Nov?

## Change log

| Version | Date | Change |
|---|---|---|
| v0 | 31 Oct 2026 | First draft from the plan, the POC and outside research (MRBench, the UK DfE standards, MathTutorBench) |
