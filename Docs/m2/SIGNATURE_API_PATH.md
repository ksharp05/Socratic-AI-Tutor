# Signature teaching path through the learner API

The integrated API can explicitly select the existing contextual hint adapter with `TUTOR_CONTEXTUAL_HINTS=1`. The default is `0`, keeping registered-practice hints as templates. This selection is separate from model access: **`TUTOR_LLM=stub` remains offline with either setting**. The wider anonymous beta dialogue and authenticated graph retain separate learner stores.

## Registered equation and teacher control

`content/milestone2_dev/practice_items.json` adds one developer-authored candidate, `m2_signature_qe_factor_zero`: **Solve x² = 5x. Find every distinct real solution.** It contains problem givens, a typed-answer contract, three Socratic hint stages and the `normalized:qe04` reference; it contains no stored answer key. The task retains the checker's required `qe03`, `qe04`, `qe05` concept tags. Its key agrees with the existing calculation routes and an explicit symbolic calculation in development tests. It is practice-only, excluded from quizzes/diagnostics, and remains **pending human review**. The frozen 665-question public dataset was not changed.

The candidate follows the same teacher workflow as other graph questions: propose a `qe04` practice set, edit its items to this ID, review the exact payload and approve. It is unavailable before approval; another edit revokes the old publication. Synthetic tests use a synthetic teacher, which does not satisfy educator review. An isolated demo database with only this published practice item ensures the signature question is selected; publishing it does not replace an existing active question or override the usual fresh-question order.

Active questions now use the payload-bound supporting reference order and only references that exist in the pinned chapter. They no longer reconstruct their references solely from task concept tags. Missing references leave deterministic guidance, rather than inventing evidence or calling the contextual model without a source.

## Contextual English and checking

An eligible registered-practice hint uses the active public problem, latest learner message, at most four recent messages, current allowed teaching move and one supporting reference. It does not send the whole checkpoint, expected answer, learner identity, private simulator state, quiz keys or final evaluation cases. Separately configured reviewed examples remain optional and are not loaded by the API factory.

There is one generation-wrapper invocation per eligible turn, with a requested **240-token output cap**. The existing SDK timeout/retry settings still apply; one wrapper invocation is not a claim of one network request. The output must satisfy the short-turn/one-question format, known-source citation and active-item leak checks, or the deterministic hint remains. Output-guard retries, pending triangle reasoning, quizzes, refused role claims, correct answers, answers rejected as unparseable by the checker and recognized unverified homework do not use this contextual generation path. This is layered heuristic protection, not proof against every semantic leak or every own-homework wording.

Wrong answers remain code-graded. Generation can rephrase the permitted feedback but cannot change the numeric verdict, advance an extra hint stage or assign mastery itself. Correct final-answer checking is a separate deterministic action. The optional adapter also normalizes mathematical superscripts and asks about supported ambiguous fraction notation.

## Teacher-visible trace

The connected browser now displays a **Conversation reference**. In the Streamlit teacher interface, open **Session trace**, enter that reference and choose **Load session trace**. The endpoint is `GET /teacher/sessions/{session_id}/trace`; students receive 403 and unauthenticated callers 401. Unknown sessions return 404. Pending learner deletion blocks the trace, and completed graph deletion removes its owned trace/history.

The view returns at most the most recent 200 events, in chronological order, with a truncation flag. It projects model/configuration identity, tool and guard events, outcome, timings, token-usage fields when present, selected validation reason codes/hashes and latest citation IDs/hashes. It excludes prompts, tool arguments/results, answer keys, raw model replies and raw provider errors. A model event is a record of the configured call path; development fixtures explicitly name their synthetic model. A citation ID and a passing guard do not establish source interpretation or teaching quality.

## Reproduce without a provider

From the canonical workspace, run:

```powershell
$env:TUTOR_LLM = 'stub'
.\.venv_app\Scripts\python.exe scripts/m2/signature_api_smoke.py
```

This command has **no live mode**. It creates a unique isolated store under ignored `Directions/git_delivery/`, starts the actual API with the contextual factory selected, replaces the model transport with a labelled synthetic response, performs teacher publication, a cited hint, incorrect/correct grading, teacher trace lookup, student trace denial and edit revocation, and then closes the app. Its projected evidence records zero provider calls and counts synthetic invocations separately. It does not export source excerpts, keys or real learner data. The same script can run from the shared checkout using its installed environment; its code-root Git identity is recorded when available.

For an interactive offline server, set `TUTOR_CONTEXTUAL_HINTS=1` and keep `TUTOR_LLM=stub` before following the [isolated connected run guide](../RUN_GUIDE.md). The Compose setting defaults to 0; the integrated overlay still forces stub mode. Docker execution remains unverified.

## Acceptance limits and retained failures

The first focused run caught a new-candidate concept-tag mistake; the checker rejected it before publication. Correcting the required metadata yielded passing API checks. The first full run in each copy had **423 passes and one failure**: the older isolated probe omitted supporting reference IDs from its synthetic publication. That fixture now explicitly carries those IDs; no unverified source inference was reintroduced. Historical failure logs remain under ignored `Directions/git_delivery/`.

The implementation does not satisfy the handbook's **live-model** signature demonstration yet. Automatic approval review rejected the earlier live probe because retrieved textbook excerpts could be transmitted without explicit transfer authorization. The API adapter would send the context described above if live generation were enabled; selecting it is not that authorization. Keep it offline until the specific transfer is approved. The [isolated live-probe specification](QUADRATIC_PROBE.md) has a different, one-attempt call budget and remains unexecuted. Actual educator review, live teaching quality, Docker/fresh-machine startup, independent evaluation and human acceptance remain open. Earlier C1/C2 results are from the base configurations and do not evaluate this opted-in API adapter.


The corrected final selections each passed **424 offline tests** (canonical 109.79 seconds; shared checkout 109.69 seconds), with successful process exits. Logs: `Directions/git_delivery/m2_signature_full_02.log` and `m2_signature_full_team_02.log`. The 19 focused signature/probe checks passed with the requested token cap; both browser scripts passed `node --check`. An assistant-operated in-app browser inspected the real Streamlit Session trace page against an isolated synthetic store: the labelled fake-model event, reference retrieval, leak checks, accepted generation, guard pass and citation identifier were visible. The current server was explicitly in stub mode; the model events were retained synthetic-script events. The temporary browser tab and both localhost server process trees were closed after verification. Screenshot and observation: ignored `Directions/git_delivery/signature-api-c5b26b4e75c1/`. This is not a live-model, real-educator or cross-browser acceptance run.

The staged whitespace check rejected CRLF in the new preserved-byte practice JSON. Only that new file was normalized to LF; parsed JSON equality was asserted, frozen content was unchanged, and all **19 affected signature/probe tests** passed afterward. The 424-test full runs preceded this formatting-only change; both byte hashes and the equality check are retained in ignored local evidence.

The synthetic API smoke was repeated on clean local commit `b4c4a71f1b361f5497aa744e09f5be4ebec03c0f`: two synthetic client invocations, zero provider calls, cited hint, code-graded wrong/correct responses, teacher trace/student denial and edit revocation passed. Raw evidence is `Directions/git_delivery/signature-api-b243a345b009/evidence.json`; [projected committed evidence](SIGNATURE_API_EVIDENCE.json) binds its hash and the test/source identities, including newline normalization. No older comparison is relabelled as testing the new adapter.
