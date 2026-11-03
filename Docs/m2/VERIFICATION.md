# Milestone 2 verification snapshot

**Date:** 4 November 2026. **Code checkpoint:** `6d78fef866dfa3dbd5e65f3a60b94c62fe56db64`. **Decision:** Milestone 2 remains incomplete. These results are development evidence, not human review or an independent final evaluation.

| Check | Observed result | Limit |
|---|---|---|
| Offline regression | 214 tests passed in an isolated local checkout of the code checkpoint. | Used the existing Python environment and local development data; not a fresh-machine, GitHub Actions or Docker run. |
| Prepared data | Existing beta3 index was copied locally, registered with its recorded SHA-256 and used to retrieve results for all three maths chapters. | Same computer only; no authorization to redistribute the derived index is inferred. |
| Quadratic probe | A synthetic-model fixture produced a source-ID-bearing Socratic question and graph/tool events; no provider call. | The fixture was not teacher-approved. The optional live probe has not been run. Heuristic answer-leak detection is not exhaustive. |
| Learner/quiz | A synthetic team-API test produced distinct routes for two seeded learners and a quiz-driven plan version/reason. | Does not establish learning; beta and team learner state remain separate. |
| Teacher workflow | Automated Streamlit widgets and local API demonstrated approval, edit, stale-token rejection and reapproval on synthetic data. | No real educator reviewed the content; full live release walkthrough is outstanding. |
| Local stuck alert | Three explicit stuck reports in distinct sessions for one unambiguous concept produce one teacher-only local event. A checked correct attempt closes the episode. | No external message delivery or human acknowledgement; team-app deletion/retention for this data is not established. |
| C1/C2 | Both stub configurations ran the same two development cards without execution failures/timeouts; each completed 1/2 tasks. Runs `m2_development_c1-20261104-000300` and `m2_development_c2-20261104-000305`. | Shared code and simulator; no model calls or independent authorship. Too small to compare effectiveness. |
| Security | Ten synthetic attack/control pairs; eight attacks measurable, two unsupported, ten controls measurable. No measured bypass or false block in run `m2_exact-20261104-000309`. | Limited checks and same-author development cases. Unsupported cases are not successes. General homework leakage is not proven prevented. |

A clean-clone Docker demonstration is still blocked by the absence of Docker on the current machine. The live-model probe remains unexecuted: automatic approval review rejected an earlier attempt because local textbook excerpts might be transmitted without explicit approval of that transfer. The [probe specification](QUADRATIC_PROBE.md) describes the proposed payload and its one-call limit. Human teacher review, independent evaluation and course participation clarification also remain outstanding.

Raw local results and machine-specific state remain under ignored `Directions/`; no source PDFs, derived index, credentials, private learner data or held-out material are part of this snapshot.

**Subsequent finding:** a later run on documentation checkpoint `2bd4102` failed one quiz schema test because an ordinary question contained the word “values.” The test was corrected to check nested field names; see [work log](WORK_LOG.md). That failure and the fix must remain visible in release evidence.
