# Decision briefs for the Lead, 13 Nov 2026

**Status of every brief: Awaiting the Lead.** Nothing here is decided. Each brief gives a recommendation for a person to accept, change or reject. Record each outcome in `Docs/DECISIONS.md` with the date and the decider's own words (task F1 in `Docs/m3/TEAM_ROLE_PLAN_2026-11-13.md:149`). Drafted with Claude Code; the evidence was checked against `Beta` on 13 Nov.

## Summary

| ID | Question | Recommendation | Decider | Urgency |
|---|---|---|---|---|
| B-01 | Confirm D-5 (Haiku 5.5 as supervisor)? | Confirm, and state that the original condition can no longer be tested | Lead (R3 proposed) | Before viva |
| B-02 | Record D-3 (re-dated milestones, four cuts) | Record as agreed on 1 Nov, only with meeting evidence | Lead, confirmed by team | Before viva |
| B-03 | Record D-4 (NCERT file handling) | Record as agreed on 1 Nov, only with meeting evidence | Lead, confirmed by team | Before viva |
| B-04 | Does Shivam Srivastava take R5b? | Yes, with the role narrowed to writing and labelling B1 and acting as second rater | Lead + Shivam | Before viva |
| B-05 | Close the 31 Oct course-model and key items | Close the model items (D-5, D-7 replaced them). Run live evaluations locally, with no shared GitHub secret | Lead, R6 | Before viva |
| B-06 | Close the plan's kickoff questions Q1–Q9 | Close each one with a line saying what was actually done | Lead | After viva |
| B-07 | R3 Q1: is the code-routed graph accepted as the item-1 equivalent? | Accept it as a documented equivalent and state the gap openly | Lead (R1) | Before viva |
| B-08 | R3 Q2: should `TUTOR_CONTEXTUAL_HINTS=1` be the default? | No, not until a funded live run checks it | Lead | After viva |
| B-09 | R3 Q3: build real agents? | Not now. If the team wants them, start with one tutor tool choice after C1 | Lead, R3 | After viva |
| B-10 | R2 Q1: does a correct answer after the last hint count as solved? | No. It clears the revisit mark only | R1 | After viva |
| B-11 | R2 Q2: cooldown length? | 7 days, fixed. No skipping based on mastery | R1 + R2 | After viva |
| B-12 | R2 Q3: move a twice-abandoned saved question to the back of the queue? | Yes, after the second give-up | R1 + R3 | After viva |
| B-13 | R2 Q4: who builds the cross-session cooldown, and when? | After D4 migration; R2, R3, R5 as proposed; off in evals | Lead | After viva |
| B-14 | Should harmless "ignore all previous…" messages stay blocked? | Keep blocking for now; report them as a separate slice | Lead (R1) + R4 | After viva |
| B-15 | Supplemental screen: fail open or closed, and run before consent? | Fail open with a time limit, a failure count and an alert. Run it before the consent check | Lead (R1) + R4 | After viva, before A1 `on` |
| B-16 | Allow a tutor provider under `reference_checked_beta`? | Keep the guard. Add a separate teaching-only provider that cannot approve | Lead | After viva |
| B-17 | Record crisis events for safeguarding review? | Record a minimal event with no text and no profile link | Lead (R1) + R4 | After viva, before A1 `on` |
| B-18 | Classifier fallback is the supervisor's model | Use no model fallback. An error is treated as UNSAFE (fail closed) | R4 proposes, Lead confirms | After viva |
| B-19 | Classifier budget when it is switched on | Give it its own small cap; classify only messages bound for the live model | Lead | After viva |

---

## B-01 · Confirm D-5, the supervisor model
- **Context:** D-5 makes `anthropic/claude-haiku-5.5` the supervisor and planner, "provisional until the first `dev_live` run with agent specialists" (`Docs/DECISIONS.md:58-60`). That run cannot happen now. `eval/configs/dev_live.toml` no longer runs and the course key is spent (`Docs/m3/R3_SPECIALISTS.md:47`). Also, code chooses the route, not the model (`R3_SPECIALISTS.md:5`), so the routing condition does not test what it was meant to test.
- **Options:** (a) Confirm it now and state the condition is moot. (b) Keep it provisional until a funded run. (c) Replace the model.
- **Recommendation:** (a). The model writes wording but does not route, so the remaining risk is the quality of its wording, and B4 measures that. The viva will ask about D-5, and "provisional for ten days with no way to test it" is a weaker answer.
- **Risks:** confirming without a live routing run; say so in the report.
- **Decides:** Lead. **Consult:** R3 (Poonam).
- **Changes:** update D-5 status in `DECISIONS.md`; report section on models.

## B-02 and B-03 · Record D-3 (dates, pre-cuts) and D-4 (NCERT files)
- **Context:** `DECISIONS.md:24-32` still lists D-3 and D-4 as "to decide" on 1 Nov, but `Docs/LEAD_ROADMAP.md:39`, `:56` and `:70-75` say both were "decided Sun 1 Nov". The milestones have passed, so this is a gap in the record, not an open choice. D-4 has five points: one git-ignored copy in `data/ncert/`, chapters 4, 5 and 8 only, no answers appendix, Science unused, 20–30 typed exercises as a check set.
- **Options:** (a) Record each as agreed on 1 Nov, citing the meeting doc or WhatsApp. (b) Record "never formally agreed; applied in practice".
- **Recommendation:** (a) where the Lead can find the meeting evidence, otherwise (b). Do not reconstruct consent that cannot be shown. For D-4, first check each point still matches what was built (is the check set typed; is Science unused on the beta?).
- **Risks:** a backdated entry with no evidence looks invented at the viva.
- **Decides:** Lead; the team confirms. **Consult:** members present on 1 Nov; R2 (index owner) for D-4.
- **Changes:** new D-3 and D-4 entries dated 1 Nov, recorded on the day they are written; remove them from "Still open"; note any D-4 point that differs in practice.

## B-04 · Shivam Srivastava as R5b
- **Context:** R6 is Sharath (`DECISIONS.md:33`, `:105`). The Lead holds Lead, R1 and R5 and tuned the safety screens, so nobody independent can label the sealed set (`TEAM_ROLE_PLAN_2026-11-13.md:188`, `:217`).
- **Options:** (a) Shivam takes R5b, narrowed to writing and labelling the B1 sealed set and acting as the second judge rater. (b) Shivam takes the full R5b scope (`DECISIONS.md:106`). (c) Someone else becomes the second labeller (R6), and R5b lapses.
- **Recommendation:** (a). Independent labels are the most valuable thing a second person can add, and B3 depends on them. A narrow scope is more likely to be finished by 29 Nov.
- **Risks:** Shivam may not accept, or may not have time. Only Shivam can agree to the role.
- **Decides:** Lead, with Shivam's own agreement. **Consult:** R6, R4 (who must not see B1).
- **Changes:** D-2 follow-up in `DECISIONS.md`; team table in `Docs/LEAD_ROADMAP.md` (F5); B1 owner in the team plan.

## B-05 · The 31 Oct course-model and key items
- **Context:** `DECISIONS.md:19-21`: two plan models were not on the course list, and the plan stored one member's key as a GitHub secret. D-5 and D-7 have since replaced both models. Keys are personal, and the course key was spent on 10 Nov.
- **Options:** (a) Close the model items; drop the GitHub-secret plan and run live evaluations locally. (b) Ask the faculty whether a shared secret is allowed.
- **Recommendation:** (a). It is simpler and follows the faculty's rule now, without waiting for an answer.
- **Risks:** no CI live-evaluation job; the report should say live runs are local.
- **Decides:** Lead. **Consult:** R6.
- **Changes:** "Still open" in `DECISIONS.md`; `Docs/plan/09-delivery.md` live-eval note; remove `anthropic/claude-3-haiku` (`config/app.toml:32`, C5).

## B-06 · Kickoff questions Q1–Q9
- **Context:** `DECISIONS.md:17` asks for Q1–Q9 (`Docs/plan/README.md:216-229`) to be recorded once settled. None are, though most were settled in practice (private repository, named roles).
- **Options / recommendation:** close each with a one-line "what we did", marking any never answered (likely Q3's teacher reviewer). Alternative: leave open.
- **Decides:** Lead. **Consult:** R6 (Q1, Q4, Q7). **Changes:** `DECISIONS.md` "Still open" only.

## B-07 to B-09 · R3 specialists (Q1–Q3)
- **Context:** R3 proposes the LangGraph graph (code-chosen routes, role allowlists) as the item-1 equivalent; "The model never chooses a tool" (`Docs/m3/R3_SPECIALISTS.md:3-5`, `:44`). Hint turns reach the model only with `TUTOR_CONTEXTUAL_HINTS=1` (`:46`); the only live evidence is a 5-turn pilot that predates PRs #4 and #5 (`:47`). Questions at `:49-53`.
- **B-07 (Q1):** options are accept as a documented equivalent, or require real agents. **Recommend accepting:** code routing is easier to test and safer for minors, but the report and viva must say plainly it is not agent behaviour. Risk: graders may count a partial miss.
- **B-08 (Q2):** options are default on, keep off, or on for a preview only. **Recommend keeping it off** until a funded live run with leak probes: it adds model calls on every hint turn and breaks evaluation comparability.
- **B-09 (Q3):** **recommend no real agents in this window**; revisit after C1 with the tutor choosing between its two read tools, behind a setting.
- **Decides:** Lead (R1). **Consult:** R3; R5 and R6 for B-08.
- **Changes:** status line in `R3_SPECIALISTS.md`; a D-entry; report architecture section. Nothing in code until B-08 or B-09 change.

## B-10 to B-13 · R2 cross-session cooldown (Q1–Q4)
- **Context:** R2 proposes a soft cooldown so a question solved in an earlier session is not served first. It needs no new table on the beta (`Docs/m3/R2_CROSS_SESSION_PROPOSAL.md:10-34`). Selection has changed results before, so it is off by default in evaluations (`:36-42`). Questions at `:44-51`.
- **B-10 (Q1):** a correct answer after the last hint is **not** solved; it clears the revisit mark only. The answer came after full scaffolding. *Decides R1.*
- **B-11 (Q2):** **7 days, fixed.** Mastery-based skipping waits until diagnosis is reliable. Option: 3 days, if the bank is small for some chapters. *Decides R1 + R2.*
- **B-12 (Q3):** **move it to the back after a second give-up**, so one hard question does not lead every session (PR 8 finding F4). *Decides R1 + R3.*
- **B-13 (Q4):** **after the viva and after the D4 Neon migration.** R2 builds the store and the beta read, R3 the selection in `app.py`, and R5 the evaluation switch. *Decides Lead; consult R2, R3, R5.*
- **Risks:** a silent change to selection would mix old and new results. Keep the switch in the run manifest.
- **Changes:** the memory policy row; `app.py` selection; `eval/configs/*.toml` switch (default off); the tests listed at `:53-57`.

## B-14 · Harmless "ignore all previous instructions"
- **Context:** Swati asks whether "ignore all previous instructions" prompts with harmless content should count as blocked; they are blocked now (`Docs/CONTRIBUTIONS.md:21`). They are most of the rise in the dev pool's wrongly blocked safe messages, from 43 to 62 (`:18`). Blocked messages get the `access_boundary` reply, which invites a concept question (`src/socrates_beta/dialogue.py:157-158`).
- **Options:** (a) Keep blocking them, and report them as a separate "benign-labelled injection" slice. (b) Allow them when the rest of the message is harmless. (c) Decide after A5 (Prompt Guard trial).
- **Recommendation:** (a), then review it after A5. A learner rarely needs this phrase, the reply is gentle, and a "harmless remainder" rule is the kind of exception attackers use.
- **Risks:** the 1% benign gate may look worse; that is why the slice is reported separately.
- **Decides:** Lead (R1) with R4. **Consult:** R5 (metric labels).
- **Changes:** label note in `Docs/testing/PUBLIC_TESTSET.md`; B1 hard-negative guidance; a reply in `CONTRIBUTIONS.md`.

## B-15 · Supplemental screen: failure and ordering (A2)
- **Context:** `supplemental_screen` runs inside `_turn`, after the consent check and after the owner guard and session lock (`dialogue.py:110-112`, `:138-144`). It catches only `OSError` and `ValueError`, logs a warning and continues. So it fails open with no time limit and no count. Any other exception becomes a server error. The team plan wants it before consent and locks (`TEAM_ROLE_PLAN_2026-11-13.md:85-86`). D-7 says the *classifier* fails closed (`DECISIONS.md:37`).
- **Options:** (a) Fail open, with a 200 ms budget, every exception caught, and failures counted and alerted. (b) Fail closed: show the urgent reply, or block the turn, when the screen errors. (c) Fail open in `shadow`, then fail closed in `on`.
- **Recommendation:** (a), and run it **before** the consent check. The fixed `urgent()` screen always runs first (`dialogue.py:101-103`) and stays as the floor. Failing closed would show crisis text or block maths on every error. A learner in crisis should get help whether or not they consented to the live model. Running before consent is acceptable only because the portable model runs locally. A screen that sends text to a third party (hosted Gemma) must stay after consent. Record why this differs from D-7: D-7 governs blocking harmful content, while this screen adds crisis detection on top of the fixed screens.
- **Risks:** silent misses during an outage; mitigated by the counter and alert (E1/E6).
- **Decides:** Lead (R1) with R4. **Consult:** R6 (alerting), R5.
- **Changes:** `dialogue.py` ordering and exception handling; the A2 tests; a D-entry; threat model.

## B-16 · Tutor provider under `reference_checked_beta` (C1)
- **Context:** `api.py:74-75` raises `ValueError` if a tutor provider is passed with `reference_checked_beta`: "Reference beta publication does not imply graph teacher approval". The other branch uses the provider for `ApprovedAssessmentService` (`api.py:78-80`). C1 needs the graph's diagnose and worked-example services in practice (`TEAM_ROLE_PLAN_2026-11-13.md:116`).
- **Options:** (a) Remove the guard. (b) Keep the guard; add a separate teaching-only provider parameter, off by default, that can never approve items. (c) Do not connect the graph in this window.
- **Recommendation:** (b). The guard stops the beta from implying teacher approval, and it should stay. Diagnosis and worked examples do not need approval rights.
- **Risks:** a worked example on a quiz item; C1 already requires a test that quiz items never get one.
- **Decides:** Lead. **Consult:** R3 (builder), R1 (teaching), R2 (memory side), R5 (eval impact).
- **Changes:** `api.py` signature and tests; a new setting; a D-entry.

## B-17 · Recording crisis events
- **Context:** urgent replies return `persistence: 'not_saved_urgent'` and support replies `'not_saved_support'` (`dialogue.py:109`, `:119`). Nothing is stored, so nobody can review how often the screens fire or whether replies were right. The beta's users are probably minors (`Docs/THREAT_MODEL.md:6`).
- **Options:** (a) Keep saving nothing. (b) Save a minimal event: date and hour, kind (crisis/abuse/secrecy), language, which screen, and the reply version. No message text and no profile link. (c) Save the message text for review.
- **Recommendation:** (b). It supports the F3 audit and the A3 shadow review without keeping a child's disclosure. (c) needs guardian consent, a named reviewer and legal advice on POCSO first (`THREAT_MODEL.md:50`).
- **Risks:** even counts can be sensitive on a tiny site. Keep only daily totals if traffic is low. Because events carry no profile link, Forget cannot delete them; state this in the privacy text.
- **Decides:** Lead (R1) with R4. **Consult:** R2 (memory policy), R6 (storage), F4 DPDP note.
- **Changes:** a new table or log line; memory-policy and privacy text; tests that no text is stored.

## B-18 · Classifier fallback model
- **Context:** `config/app.toml:21` sets `safety_fallback_model = "anthropic/claude-haiku-5.5"`, the D-5 supervisor model. The PR 10 review flagged this conflict with the "different model" rationale (`Docs/m3/PR10_REVIEW.md:28`). D-7 does not name a fallback (`DECISIONS.md:37`).
- **Options:** (a) No model fallback: an error counts as UNSAFE, and the fixed screens still run. (b) A fallback from another family, such as GPT-5 nano (64/88, but 286 unreadable replies, `DECISIONS.md:46`).
- **Recommendation:** (a). No listed alternative is good enough, and failing closed is already the rule.
- **Decides:** R4 proposes; Lead confirms. **Consult:** R5.
- **Changes:** `config/app.toml:21`; `guards.py` tests; a D-7 note.

## B-19 · Classifier budget when switched on
- **Context:** every classifier call would use the hosted lease. R4's open item is "its own small cap so it does not halve the 200-request lease" (`THREAT_MODEL.md:45`). The options in `PR10_REVIEW.md:29-34` say "Lakshya decides this." The classifier is off (`config/app.toml:19`).
- **Options:** (a) A separate small cap, classifying only messages bound for the live model. (b) Share the lease. (c) A rule prefilter in front of it.
- **Recommendation:** (a), with (c) where the portable model already acts as the prefilter. Decide it now, but it applies only when the classifier is turned on.
- **Decides:** Lead. **Consult:** R4, R6.
- **Changes:** settings and budget guard; `Docs/deploy/VERCEL_BETA.md`.
