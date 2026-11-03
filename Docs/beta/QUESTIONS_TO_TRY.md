# Questions to try in the Socrates beta

Measured on 3 November 2026 (India). The same 34 developer-authored tasks were used during fixes; these are development results, not an independent test. All outcomes are retained. The release run completed 28/28 supported tasks under the declared technical checks; six further unsupported requests were appropriately declined or clarified. This does not establish factual accuracy or flawless teaching.

Open the app at http://127.0.0.1:8770. Set the stated class and subject. For follow-ups, remain in the same conversation.

## Strong observed examples

| Class / subject | Question | What was observed |
|---|---|---|
| 8 / Science | Why do rough surfaces oppose motion through friction? | Live reply passed format and expected-source checks. |
| 10 / Mathematics | What makes an expression quadratic after simplifying it? | Live reply passed format and expected-source checks. |
| 10 / Mathematics | What does the discriminant tell us about real roots? | Live reply passed format and expected-source checks. |
| 10 / Science | How does photosynthesis help a plant make food? | Live reply passed format and expected-source checks. |
| 12 / Biology | Why should DNA replicate before a cell divides? | Live reply passed format and expected-source checks. |
| 10 / Social Science | Why is power sharing important in a democracy? | Live reply passed format and expected-source checks. |
| 10 / English | Why does Lencho write a letter to God in the story? | Live reply passed format and expected-source checks. |
| 10 / Science | Can you explain photosyntesis in plain English? | Live reply passed format and expected-source checks. The spelling error was handled. |
| 12 / Biology | Explain DNA replication in simple English. | Live reply passed format and expected-source checks. Follow with “I still don’t understand. Could you make that simpler?” Context was retained; question difficulty still needs review. |
| 10 / Mathematics | What is an arithmetic progression? | Live reply passed format and expected-source checks. Follow with “I think it just means numbers go up. Is that enough?” The source-backed distinction was explained. |

## Weakest or unavailable examples

| Class / subject | Question | Observed limitation |
|---|---|---|
| 12 / Mathematics | Can you teach me integration by parts and check my answer? | No normalized Class 12 maths teaching/checking adapter yet. |
| 11 / Urdu | Explain the meaning of the poem in my Urdu textbook. | The beta retrieval scope is English-first; Urdu teaching is not enabled. |
| 9 / ICT | Explain computer networking from my Class 9 ICT textbook. | No acquired active Class 9 ICT book; publisher Coming Soon. |
| 10 / Science | Using the attached diagram, tell me which ray is refracted. | No image was supplied and this beta has no diagram-understanding adapter. |
| 12 / Economics | What is today's live stock price and should I buy it? | No live market data or financial-advice tool in this textbook tutor. |
| 10 / Science | Why does it do that? | No prior referent/topic; clarification is needed rather than inventing a source. |

## Fragile supported questions found during development

- “What does the discriminant tell us about real roots?” — initially exceeded the reply limit; the release run used the explicitly recorded format-repair path.
- “What is an arithmetic progression?” followed by “I think it just means numbers go up. Is that enough?” — initially produced advanced source recovery and a grading phrase; foundational retrieval and question phrasing were improved.
- “Why does Lencho write a letter to God in the story?” — initially cited a workbook; primary-reader coverage was recovered through the data plug-in.
- “How do acids and bases differ in their properties?” — an overly broad guard falsely rejected a factual description. A private audit confirmed the false block; the narrowed rule is covered by factual-description and unsafe-instruction tests.

These are regression questions with known history, not proof of persistent factual errors in the current model. The release run passed them under the declared checks; future wording can still expose problems.

## Checked maths examples

Use Practice & quick checks. These six public practice prompts were tested by submitting answers independently calculated from their givens, rather than asking the language model to grade. The API supports choosing a public question ID in practice mode; diagnostic/quiz ordering remains server-controlled.

- **q_a5aa3cfe9241fbe1f927** — An AP starts at 34 with common difference 6. Find term 17, using one-based positions.
- **q_a3ba7cec64df726ab50e** — Find the sum of the first 13 terms of an AP with first term -8 and common difference 6.
- **q_77c56ff5fa66c5daa3e3** — Find every distinct real root of (-2)*x^2+(-20)*x+(-66)=0. Give exact values; do not repeat a repeated root.
- **q_5ecd82f7d79c0cb294b9** — Find every distinct real root of (3)*x^2+(36)*x+(-135)=0. Give exact values; do not repeat a repeated root.
- **q_49922f00fe38892497ab** — A right triangle has hypotenuse 13, opposite side 12 and adjacent side 5 relative to acute angle A. C is its other acute angle. Find sec(A) exactly.
- **q_6e25990548d58ad7e456** — Classify the real roots of (-2)*x^2+(32)*x+(-128)=0 as two_distinct_real, repeated_real or no_real, using a checked discriminant.

## How to read the results

- Baseline: 25/34 met completion checks (25/28 supported tasks), 25 actual model calls.
- Current beta: 28/34 met completion checks (28/28 supported tasks), 26 actual model calls, including 1 bounded format repair.
- All runs retained all six deliberate unsupported tasks as incomplete and recorded appropriate abstention separately.
- The original literature response cited a relevant NCERT workbook instead of the expected primary reader. That was a source-preference failure, not proof its factual answer was wrong. A validated primary-reader quote was added through the import CLI and the next run cited it.
- All four runs are retained: 25/34, 27/34, 27/34 and 28/34 completions, with 25, 25, 27 and 26 model calls respectively. Earlier chemistry rejections were diagnosed as a guard false positive, not proof of unsafe model instructions.
- Response format and source-ID matches do not prove semantic grounding. Analogies, generated examples and the difficulty of questions need human assessment.
- No final held-out cases were read or used. A future independent beta sample should be authored and labelled separately.
