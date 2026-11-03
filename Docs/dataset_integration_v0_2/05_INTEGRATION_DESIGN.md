# Runtime integration design and observed execution

## Existing path

The team app uses `TutorApp` and typed `TutorState` in `src/tutor/app.py`. Input screening precedes planner routing. The selected specialist uses ToolBus, the output guard buffers the draft, the graph updates permitted learner state and then responds. `LLM.complete` uses the configured provider client and traces tokens. ToolBus and the existing guard remain the source of tool-role and mode decisions. The Streamlit UI and HTTP entry points are indexed in `01_FILE_INDEX_AND_SCHEMA.md`.

The original active-item hint branch is templated. A different misconception-tutor branch already calls the model. The fresh baseline probe received two real provider responses on diagnostic/misconception paths. Therefore a configured key alone does not settle the S6 concern: each intended route must be checked.

## Additive opt-in candidate

`src/v02_integration/runtime.py` supplies `ContextualPreviewTutor`, a subclass selected only by the explicit probe option. It does not edit the team's prompts, guard, diagnosis, simulator or API files, and is not enabled by default.

- Scope the candidate tutor role explicitly to Quadratic Equations, Arithmetic Progressions and Introduction to Trigonometry.
- Preserve mathematical superscripts/minus signs before the inherited compatibility normalization.
- Clarify explicitly ambiguous division notation and unfinished expressions without moving hint stages, counting a wrong attempt or changing mastery.
- Let base code grade and advance the normal hint ladder. Model generation covers an active-item hint and scorable wrong-answer feedback; correct/unverified attempts keep deterministic handling. A code-owned "Not quite." prefix preserves the incorrect verdict; a model response contradicting that verdict falls back.
- Project the public active problem, latest learner turn, recent sanitized messages, allowed next action and retrieved references. Never serialize the whole state, grading key, hidden card or raw expanded data.
- Request one short English question. The preview's versioned format corrects a conflicting legacy presentation example without modifying the shared prompt source.
- Check length, question shape, actual source IDs and the active-item leak tool before publishing. Tool failure, missing evidence or unsafe output returns the existing deterministic fallback. Existing graph output checks still run afterwards.
- Quiz paths make no calls through this language adapter. Handoff/refusal/publication routes remain inherited and unchanged.
- Close the owned event-loop thread and SQLite connections idempotently after an isolated run; test cleanup confirms no owned state connection remains open.

The approved-example reader requires a server-held manifest hash and policy ID, an exact file allowlist and content hashes. It rejects the raw dataset directory, extra private files and stale projections. The default has no examples. Promotion retains the complete review receipt and ratified policy in a separate private ledger, bound to the runtime manifest. The fixture test exercises review, publication, pinned loading and the actual Main graph prompt path; fixtures count as zero real approvals. A reviewed full dialogue may be stored for provenance, but only its initial reviewed student/probe pair can be selected as a prompt example. Later corrected answers and all critic negatives are excluded.

## Measured live evidence

`evidence/live_contextual_probe.json` binds the current runtime source hash and records two real provider responses: the scorable wrong-answer feedback route and the active-item hint route. Both generation events are accepted after buffered checks. Practice-set selection, quiz start and quiz submission have zero model calls in that probe. The effective candidate prompt version is `expanded-v02-contextual-preview-5`. The temporary teacher actor is an explicitly synthetic isolated fixture, not a human approval or production publication. No raw expanded records were ingested.

Earlier candidate replies failed the presentation check and correctly fell back; those trials remain archived. The current source-bound probe passed both intended routes; earlier successful versions are archived too. This is a narrow smoke test, not a measured production acceptance rate or an English-learning experiment. The legacy POC provides the Quadratics example; full three-chapter traces await R2 content/policy review and R3 application integration.

All 38 integration tests pass. They cover the real Main graph with isolated fixtures, the private review ledger and policy-content binding, distinct qualified reviewers, immutable/bounded projections, incorrect/correct grading authority, ambiguity, signs/fractions, contextual projection, no private fields, bad citations, overlong/multiple questions, positive/error leak checks, no quiz calls and pinning of reviewed stores. Thirty existing app tests also pass. Authentication, HTTP streaming and UI deployment were not revalidated by the direct graph probe.

## Team enablement boundary

R3/R4 review the candidate code and effective prompt version before connecting it to the HTTP app factory. Wire an explicit feature flag, retain baseline selection, and pin any approved example manifest in trusted server configuration. Never take a directory, role, policy ID or approval claim from a learner message. R4 must extend/confirm partial-leak and all-answer-kind protection; the inherited detector is not a semantic proof. Do not enable the unratified worked-parallel-example exception.
