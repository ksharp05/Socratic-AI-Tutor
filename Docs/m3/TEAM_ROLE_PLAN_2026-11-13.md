# Team plan after v1.0: where we stand, what we do next, who owns it

**Written:** Fri 13 Nov 2026, by the Lead · **Branch:** `Beta` · **Viva:** Sun 15 Nov · **Plan window:** 13 Nov – 29 Nov

This replaces the first draft of this file from earlier today. That draft listed four items as open that the code shows are done; they are now marked as done. Every claim below was checked against the code on `Beta`, the private evidence under `Directions/`, or a cited outside source. Where something could not be checked, it says so.

**How to use this file:** read Part 1 (5 minutes), then your role card in Part 4. Every task has an owner, a reason, and an acceptance check. A task is done only when its acceptance check passes and is logged in `Docs/CONTRIBUTIONS.md`.

---

## Part 1 · Where we stand (honest version)

### 1.1 What is live and what is on Beta
| Item | State |
|---|---|
| Release | `v1.0` tag on the submitted commit `d139762` |
| Production | Beta `db49b7d`, about one week of work behind Beta. The classifier is off (D-7). |
| Beta | Everything below is pushed to `origin/Beta` today. Start all new work from it. |
| PRs | All 28 team PRs are merged into Beta. No PR is open. |

### 1.2 What landed on Beta today (13 Nov)
- **Step feedback in practice:** a "Check my step" box. The tutor answers a learner's triangle-ratio step in English, Hindi or Hinglish without grading it, using up a hint, or revealing the answer (`ratio_hint.py`, `tutor/triangle_reasoning.py`, `/api/practice/{id}/hint`). The follow-up request is signed so it cannot be replayed across questions.
- **Emotional-support reply:** a message such as "I feel low" gets a short, caring reply in three languages, no maths, and is **not saved**. A crisis message still takes priority.
- **Crisis-mention masking:** academic, quoted, fictional and denied mentions of self-harm no longer trigger the urgent reply. **This lowers crisis sensitivity and needs an R1 and R4 review before it reaches production (see the risks in Part 6).**
- **Injection screen port:** `SafetyScreenPort` lets a second crisis or injection screen plug into the chat turn. **Nothing is connected to it yet;** it is the socket, not the plug.
- **Latency:** the source word-set cache and the single write transaction behind the latency report. Local p95 dropped from 15.95 ms to 11.94 ms (local SQLite, offline sources).
- **Guards:** requests to reveal a password or the system prompt are now caught as injection.
- **CI hygiene:** the eight new tests that need the private book corpus are now marked `local_corpus`, so GitHub CI skips them as it does the others.

### 1.3 The safety numbers, read properly
Public core, frozen candidate (`Directions/product_quality/v5_crisis/FRESH_JOINT_SAFETY_01.json`, reproduced offline by a second script):

| Metric | Production rules | Deployable now (portable model) | Full candidate (needs local Gemma) |
|---|---|---|---|
| Crisis caught (of 88) | 35 | **59** | 68 |
| Benign wrongly blocked (of 1,031) | 5 | **7** | 8 |
| Gandalf injections caught (of 200) | 122* | — | 128 |
| deepset injections caught (of 125) | 26 | — | 29 |

\* 122 includes today's password/system-prompt guard. With the guards as merged in PR 28 it is 119.

Four facts change what we do next:
1. **The 68/88 depends on a 2.8 GB Gemma model running on a local GPU.** It cannot run inside a Vercel function. The part that can ship today is the 2.2 MB portable model: **59/88 with 7/1,031 benign blocks**, using the standard library only.
2. **The 4,000-message core is no longer a held-out set.** About 11 injection settings and 6+ crisis variants were scored on it, and the one that passed the 1% gate was picked. Treat every core number as development evidence. **We need a new sealed test set** (R5, workstream B).
3. **Roman-script Hinglish is the weakest slice:** 21/120 on a public Hinglish sample. The core has no Hinglish crisis cases at all, and our synthetic Hinglish pack fails the 1% benign gate (36/1,100).
4. **The injection detector is retrained from private data on every run, and its training set holds only 107 injections.** It needs scikit-learn (too heavy for Vercel cold starts) and should be exported to plain coefficients like the crisis model.

### 1.4 Already done (do not redo)
- **"Empty set" grading on the nine term-count items:** all nine accept "empty set", "none", "{}", "∅", "no such AP", "does not exist", "zero", "0", "impossible" and "There is no such term" (`mathcore.py:26-36`). Missing: a Beta-level test over the nine IDs, plus Hindi and Hinglish phrasings ("khaali set" is still rejected).
- **The R1 "does not exist / zero" rule** was settled 10–11 Nov.
- **Report 2a** already says the classifier is built but off.
- **The Unicode and whitespace bypass of the distress screen (AS-02)** is fixed; 15 bypass classes route correctly.
- **Helpline:** replies use Tele-MANAS 14416 / 1-800-891-4416. The older KIRAN line was merged into Tele-MANAS in Feb 2024, and we do not use it.

---

## Part 2 · How we work from today

1. **Branch from `Beta`, PR into `Beta`.** Branch name `r<role>/<topic>`, for example `r4/injection-adapter`. Nobody commits to `main`. Production deploys only on the Lead's word.
2. **Every PR:** tests pass (`pytest -m "not local_corpus" tests tests_beta tests_book_pipeline tests_integration_v02`), one reviewer from **another** role, and a line in `Docs/CONTRIBUTIONS.md` that says what was AI-assisted.
3. **Separation rules still apply:**
   - R3 (who tunes the agents) never reads `heldout_private/` or the new sealed set.
   - R4 (who builds the guards) does not see R5's new attacks until after the frozen run.
   - Nobody writes rules from the error file of a test set and then quotes that set as evidence.
4. **One number, one receipt.** Any number in a doc cites a JSON receipt in `Directions/` or a CI run. "Development evidence" stays labelled as such.
5. **Until the viva (13–15 Nov):** no production deploy, no Neon schema-2 migration, no paid API runs. Read your role card and prepare to explain your component.
6. **Stand-up:** 15 minutes daily on WhatsApp. Post three lines: done, next, blocked.

---

## Part 3 · Six workstreams

Each workstream has one accountable owner. "With" means that role contributes and reviews.

### A · Safety screens into the live chat (owner R4 · with R1, R5, R6)
**Why:** production rules catch 35/88 crisis messages. The deployable portable model catches 59/88 at 7/1,031 benign blocks, a large gain within our 1% limit.

**Research basis:**
- Small guard classifiers over-block benign text that contains trigger words (InjecGuard/PIGuard, ACL 2025, arXiv 2410.22770).
- OWASP LLM01:2025 asks for layered defences and deterministic output checks, and says no single filter is enough.
- A screen that lets text through when it errors ("fail open") must be counted, alerted on, and timed out.

| # | Task | Acceptance check |
|---|---|---|
| A1 | Move the portable crisis model into `src/socrates_beta/` behind a setting `crisis_model` (`off`/`shadow`/`on`), as a `SafetyScreenPort` adapter. Run it **before** the consent check and before session locks. | Scores match the offline scorer within 1e-9 on the dev rows. Core reproduces 59/88 and 7/1,031. Bundle grows by ≤5 MB. |
| A2 | Failure handling. Decide fail-open vs fail-closed with R1 (D-7 says closed for the classifier). Add a 200 ms budget; catch every exception; log and count each failure. | Tests: a crisis from the model beats a consent 403; that turn writes 0 rows; timeout and exception paths are tested. |
| A3 | **Shadow mode first.** On a Vercel preview, run the model and log its decision without acting on it. | One week of preview traffic with logged decisions, and benign flags reviewed by R1. |
| A4 | Export the injection detector to plain coefficients (no scikit-learn at runtime). Add an "instruction-extraction" training slice from the **dev** pool only. | Same decisions as the scikit-learn version on dev. Final numbers come from R5's sealed run, not the core. |
| A5 | Trial **Llama Prompt Guard 2 22M** as a second-stage injection detector, on borderline cases only. Check the Llama licence terms first. Not ProtectAI v2: it is archived, English-only, and misses jailbreaks. | CPU latency inside the function (Meta publishes only GPU timings). False blocks on the 1,031 benign set and on a Hindi/Hinglish maths slice. |
| A6 | Quick fixes from the app-security review: catch the curly-apostrophe form of a secrecy promise; a wall-clock limit on the maths checker (AS-01); turn off `/openapi.json` (AS-10); bound the session-lock dictionary (AS-08). | One test per fix. |
| A7 | Screen the hint "step" box and answer submission with the same port, not only `urgent()`. | Tests. |

**Not now:** hosting Gemma as a separate GPU endpoint. It adds latency, cost, and sends learner text to a third party. Revisit only if A3 shows the portable model is not enough (decision test in B5).

### B · Honest evaluation (owner R5 · needs a second person)
**Why:** our core set has been used for selection, so it can no longer show how the system does on new data.

**Research basis:**
- MRBench (Maurya et al., NAACL 2025) gives eight tutor-quality dimensions. The BEA 2025 shared task found human agreement of only about κ = 0.65 and automated scoring macro-F1 of 58–72, so an LLM judge must be calibrated against humans before we trust it.
- Bastani et al. (PNAS 2025): unguarded AI help reduced later exam scores by about 17%, which is why answer leaks are our core metric.

| # | Task | Acceptance check |
|---|---|---|
| B1 | **Build a sealed safety set**, written and labelled by people who did not tune the screens: about 300 tutor-style messages in English, Hindi and **Roman Hinglish**. Include indirect cues, eating-disorder and means-seeking prompts (our current misses) and hard negatives ("ignore the units", "this question is killing me"). Freeze its hash before anyone scores it. | Two labellers, with Cohen's κ reported. The hash is in the experiment log before the first run. |
| B2 | Freeze `eval/PREREGISTRATION.md` (still "draft") with thresholds, metrics and stop rules. | Frozen hash committed before B3. |
| B3 | One scored run of A1 and A4 on the sealed set. | Report recall with its 95% Wilson lower bound per language, and benign block rate with its upper bound. Pass: crisis ≥70%, Roman Hinglish ≥75%, benign ≤1% (upper bound ≤2%). |
| B4 | Tutor-quality rubric: four MRBench dimensions (answer revealed, mistake identified, guidance given, actionable), plus an answer-leak rate per 100 tutor turns. Two humans label about 100 turns; compare the LLM judge. | Human-human and human-judge κ reported. Use the judge only on dimensions where it is close to the human κ. |
| B5 | Decision test for hosted Gemma (only if needed after A3). | p95 ≤300 ms including network, same decisions as the archive, cost ≤1 cent per 1,000 messages. |
| B6 | Re-run the 420-case security set against Beta's `safety.py` (the report says it was never re-run on the beta). | Receipt plus a section 2a update. |

### C · Teaching quality (owner R3 · with R1, R2)
**Why:** the graph (diagnosis, worked example after the last hint) is built and tested but is **not connected to the Beta learner turn**. Today only `triangle_reasoning` is reused, through `ratio_hint.py`.

| # | Task | Acceptance check |
|---|---|---|
| C1 | Connect the graph's diagnose and worked-example services to the Beta practice flow, behind a setting. `reference_checked_beta` currently forbids a tutor provider (`api.py:75`); agree the change with the Lead first. | Integration tests on practice, quiz, restart and forget. Quiz items never get a worked example. |
| C2 | Independent review of the +902-line `triangle_reasoning.py` and `ratio_hint.py` (they landed today and were written by one author). | A reviewer from another role signs off in the PR. Tests cover each hint branch. |
| C3 | Hindi and Hinglish empty answers ("khaali set", "koi term nahi"), after R1 agrees the wording. Add a Beta-level test over the nine item IDs. | Tests. |
| C4 | Spotlighting: wrap the learner's text in clear delimiters in the tutor prompt and tell the model it is data, not instructions (Hines et al., Microsoft, arXiv 2403.14720, reported attack success falling from over 50% to under 2%). | Prompt version bumped. R5 re-runs the leak and injection probes. |
| C5 | Release `parallel-example-v4` with the finding 5 wording fix. Remove the retired `anthropic/claude-3-haiku` from `config/app.toml:32`. | Tests. |

### D · Knowledge and memory (owner R2 · with R6)
| # | Task | Acceptance check |
|---|---|---|
| D1 | Show `saved_for_later` in the UI (the API sets it; `app.js` never shows it). | A UI test where the last hint shows a "saved for later" note. |
| D2 | Result-parity test for today's retrieval cache, plus cold and warm timings. | Same top-k results with and without the cache on the 100-query workload. |
| D3 | A paraphrase, spelling-variation and Hinglish retrieval set (about 100 queries). | In-scope hit rate and false-match rate reported against today's 75/92 and 10/45. |
| D4 | **After the viva:** run the Neon schema-2 migration on a branch database first, then production, with the Lead present. | Forget-my-data deletes revisit-queue rows. A rollback script exists. |
| D5 | Conversation context for the safety screen: give A1 the last 3–5 learner turns, not only the latest. Multi-turn adolescent benchmarks (2026) find gradual disclosure is the main miss. Our own run went from 5/16 to 12/16 with one earlier turn. | It works with forget-my-data. No new stored state beyond what Forget deletes. |

### E · Platform and operations (owner R6 · with R2, R4)
**Research basis:**
- Vercel's Python bundle limit is 500 MB uncompressed since Feb 2026; Hobby functions get 2 GB and 300 s.
- Neon Free allows 1 GB of storage per project, and writes fail at the cap.
- OpenTelemetry's GenAI conventions name the latency and token fields to log; they are still in development status.

| # | Task | Acceptance check |
|---|---|---|
| E1 | Hosted latency waterfall: network, Postgres, screens, provider call and reply checks, cold vs warm. Log time-to-first-token and total turn time using the OTel GenAI field names. | p50 and p95 per stage from at least 100 hosted requests. Set SLOs from that baseline, not from a guess. |
| E2 | Preview deployment for A1/A3 with a bundle-size and cold-start check. | Cold start increases by ≤300 ms; warm screen p95 ≤10 ms. |
| E3 | CI: add `pip-audit` and a smoke version of `scripts/qa` stress runs. Do the deliberate CI-failure demo on a throwaway branch. | A green CI run and a red demo run, both linked in `Docs/ci_failure.md`. |
| E4 | Rate limiting (AS-03, none exists) and the SameSite profile-reset issue (AS-06). | Tests. Production behaviour unchanged for normal use. |
| E5 | Clean-machine install by someone other than the Lead, plus a mobile check on a real phone. | Notes plus screenshots in `Docs/m3/v3/TEAM_ACTIONS.md`. |
| E6 | Key and budget state: check OpenRouter credits before any live run (the docs disagree: USD 3.46 left on 12 Nov, a 402 error on the second key). Set `TUTOR_BETA_LIVE=0` if there is no funded key after 16 Nov. Watch Neon storage. | A one-line status in the checkpoint each week. |

### F · Product, policy and governance (owner R1 / Lead)
| # | Task | Acceptance check |
|---|---|---|
| F1 | Clear the decision backlog in `DECISIONS.md`: D-5 (provisional), R3_SPECIALISTS Q1–3, the R2 cross-session proposal Q1–4, Swati's harmless "ignore all previous" question, and the never-recorded D-3/D-4. | Each one decided or closed, with the date and the decider's words. |
| F2 | **Review the crisis-mention masking** (`_FICTION_QUOTE`, `_ATTRIBUTED_QUOTE`, `_CONTEXTUAL_CRISIS` in `safety.py`) with R4. Some of its phrases match rows in the synthetic Hinglish pack's error file. Either keep it, with new independent test cases, or narrow it. | A decision recorded. That pack is marked "contaminated" for future evaluation. |
| F3 | Safe-messaging audit of the urgent and support replies against WHO/IASP (2023) and the JED Foundation's AI guidance (2025): no method talk, encourage a trusted adult, give the helpline, never promise secrecy, do not resume maths straight away. | A checklist with each reply marked pass or fail. |
| F4 | DPDP readiness note. The child-data duties (Section 9, Rule 10: verifiable parental consent) start in **May 2027**; one source says March 2027, so confirm it in the e-Gazette. Plan a parental-consent step and retention limits before any real school pilot. | A one-page note in `Docs/policy/`. |
| F5 | Name the R6 owner and a second R5 person. Demo recording and grader access. | Team table updated in `Docs/LEAD_ROADMAP.md`. |

---

## Part 4 · Role cards (send each person their own card)

### R1 · Domain and product lead · Lakshya (Lead)
- **Owns:** F1–F5.
- **Reviews:** A2 (fail policy), A3 (shadow-mode flags), C1 (graph in practice), C3 (Hindi wording).
- **First task after the viva:** F2. It decides whether today's masking change can ever reach production.
- **Viva prep:** the decision log (D-1 to D-7), and why the classifier is off.

### R2 · Knowledge and memory engineer · Rizwan Farooq
- **Owns:** D1–D5.
- **Reviews:** C1 (memory side), E1 (storage timings).
- **Start with:** D1. It is small and visible, and the API already sends the field.
- **Viva prep:** retrieval scoring (the stoplist, rarity weighting, relevance floor), the revisit queue, and how Forget deletes everything.

### R3 · Agents and orchestration engineer · Poonam Ramnaresh Prajapati
- **Owns:** C1–C5.
- **Reviews:** D5 (context window), A7.
- **Start with:** C2. Review today's step-feedback code with fresh eyes before anyone builds on it.
- **Do not:** open `heldout_private/` or the B1 sealed set.
- **Viva prep:** the graph, the after-last-hint rule, and the specialists proposal.

### R4 · Tools, control and security engineer · Swati Smita Biswal
- **Owns:** A1–A7.
- **Reviews:** E4, C4, F2 (with R1).
- **Start with:** A6 (four small fixes, one test each), then A1 in `shadow` mode.
- **Do not:** look at R5's B1 set before B3 is scored.
- **Viva prep:** the threat model v3, D-7, and why fail-open vs fail-closed matters.

### R5 · Evaluation and red-team engineer · Lakshya, plus a second person (to name)
- **Owns:** B1–B6.
- **Reviews:** every PR that touches `eval/`.
- **Start with:** B2 (freeze the pre-registration) and B1 (write the sealed set). The second person should write and label B1, so the screens are not tested by the person who tuned them.
- **Viva prep:** why the core is now development evidence, and Wilson bounds.

### R6 · Deployment and operations engineer · Shivam Srivastava or Sharath S Nadig (to confirm)
- **Owns:** E1–E6.
- **Reviews:** A1 (bundle and cold start), D4 (migration).
- **Start with:** E5 (clean-machine install and mobile check) to learn the stack, then E1.
- **Viva prep:** the Vercel and Neon setup, the CI gates, the hosted lease and budget guard.

---

## Part 5 · Timeline

| When | Focus | Exit check |
|---|---|---|
| **Fri 13 – Sun 15 Nov** | Viva prep. Production frozen. Read your card. Small PRs only (A6, D1, C3 tests). | Viva done. |
| **Mon 16 – Sun 22 Nov** | A1 shadow, A2, A4, A6 · B1 written, B2 frozen · C2, C3 · D1, D2, D4 · E1, E2, E5 · F1, F2, F3 | Portable model in shadow on a preview. Sealed set frozen. Migration done. |
| **Mon 23 – Sun 29 Nov** | B3 scored once · A1 `on` if B3 passes · C1 behind a setting · D3, D5 · E3, E4 · F4 | B3 receipt. Lead decides whether to deploy. |

**Dependencies:** B3 needs A1, A4 and B2. Turning A1 on needs B3 and F2. C1 needs the Lead's decision on `reference_checked_beta`. D5 needs A1.

## Part 6 · Risks

| Risk | Effect | Mitigation | Owner |
|---|---|---|---|
| Crisis masking lowers sensitivity and was partly written from the synthetic pack's errors | Missed crisis in production | F2 review; the pack is no longer used as evidence; B1 hard negatives | R1, R4 |
| Core numbers are optimistic | We overclaim in the report or viva | Say "development evidence"; B1–B3 | R5 |
| A screen fails open silently | Crisis missed with no trace | A2: count, alert and time out | R4, R6 |
| No funded key after 16 Nov | Live replies fall back to source reading | E6; `TUTOR_BETA_LIVE=0` | R6 |
| One person holds Lead, R1 and R5 | No independence for labels or held-out sets | F5: name a second R5 | Lead |
| Neon Free at 1 GB | Writes fail | E6 monitoring | R6 |
| Child-data law from 2027 | Can't pilot in schools without parental consent | F4 | R1 |

## Part 7 · Sources
- Meta, Llama Prompt Guard 2 model card (86M/22M): huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
- ProtectAI deberta-v3-base-prompt-injection-v2 card (archived): huggingface.co/protectai/deberta-v3-base-prompt-injection-v2
- InjecGuard / PIGuard, over-defence in guard models (arXiv 2410.22770, ACL 2025)
- OWASP Top 10 for LLM Applications 2025, LLM01 Prompt Injection: genai.owasp.org/llmrisk/llm01-prompt-injection/
- Hines et al., Spotlighting (Microsoft, arXiv 2403.14720)
- PINT benchmark: github.com/CheckPointSW/pint-benchmark
- Maurya et al., Unifying AI Tutor Evaluation / MRBench (NAACL 2025): aclanthology.org/2025.naacl-long.57; BEA 2025 shared task (arXiv 2507.10579)
- Macina et al., MathDial (EMNLP Findings 2023, arXiv 2305.14536)
- Bastani et al., Generative AI can harm learning (PNAS 2025)
- WHO/IASP, Preventing suicide: a resource for media professionals (2023 update); JED Foundation open letter to the AI industry (2025)
- Tele-MANAS 14416; KIRAN merged into Tele-MANAS (Feb 2024)
- Vercel Functions limits (docs, Aug 2026) and the Python 500 MB bundle changelog (Feb 2026); Neon Free plan FAQ (Oct 2026)
- DPDP Rules 2025 (G.S.R. 846(E), notified 13 Nov 2025): phased commencement; Rule 10 in the 18-month tranche

**Not verified:** Prompt Guard 2 CPU latency; label noise in the deepset set; the exact child-data commencement date (May vs March 2027); the 2026 multi-turn adolescent benchmarks (abstracts only).
