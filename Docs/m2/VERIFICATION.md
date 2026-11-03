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


**Later working-tree verification:** The publication-integrity changes passed 230 offline tests across all four project test directories. The change and its limits, including the original teacher-edit/learner-turn race, are described in [publication integrity](PUBLICATION_INTEGRITY.md). This later run did not test a live provider or a fresh machine.


**Concurrency follow-up:** The original race was reproduced and addressed for cooperating processes sharing one local SQLite path. Cross-process lock contention and interrupted-turn revalidation passed on this Windows machine. This does not establish multi-host or network-filesystem behavior; see [publication integrity](PUBLICATION_INTEGRITY.md).

The final concurrency working tree passed **238 offline tests** across the four project suites on this Windows machine. This later result does not replace the recorded historical checkpoint above.


**Canonical workspace verification:** After restoring missing tracked application files, development fixtures, UI files and the public practice slice, all **238 offline tests** passed when run from `D:\Work\IITB\Socratic Tutor` with its `.venv_app` interpreter. `tutor.cmd --help` also starts in stub mode. The first collection attempt exposed missing modules and API packages; a subsequent run exposed older local source revisions and missing support files. Those failures were recorded in the session output and fixed before the passing run. The necessary app packages were installed offline from hash-verified files already installed on this machine. This is still not a fresh installation, Docker verification, live-provider test, independent evaluation or educator review.


**Mounted beta integration:** The canonical working tree passed **248 offline tests** across all four suites after connecting mounted beta practice to teacher publication. Synthetic API tests covered approval, edits, quizzes, retries, service failures, mismatched payloads and concurrent grading; the beta JavaScript passed a syntax check. This is not a browser-visual review, actual teacher approval, a live-model test or evidence that beta and graph learner state are unified. See [mounted beta approval](MOUNTED_BETA_APPROVAL.md).

The strengthened final selection passed **248 tests in each of the canonical workspace and team checkout**. Full local output is retained under the ignored `Directions/git_delivery/` directory as `m2_mount_canonical_tests.log` and `m2_mount_team_tests.log`. Both used existing environments, synthetic development inputs and stub mode.


**Later browser check:** An assistant-operated in-app browser inspected the mounted beta on a temporary localhost server with a synthetic passage, synthetic teacher identity and stub model. The practice screen showed the no-approval message, opened a question after synthetic publication, and displayed a revocation message without a score after the set was edited. The displayed narrow layout was inspected; this is not cross-browser accessibility testing or a real educator review. The temporary server was stopped.


**Beta quiz and planning follow-up:** The canonical working tree passed **267 offline tests** after fixing cross-session quiz access, duplicate grading, partial observation writes, early-exit score exposure and urgent-response delays. A synthetic two-profile check showed that one completed quiz changes only that profile's beta plan revision and reason. The result is not evidence that the beta and graph share learner state or a graph trace. [Details](BETA_QUIZ_INTEGRITY.md). Full local test output is retained under `Directions/git_delivery/m2_quiz_atomic_canonical_tests.log`.


**Final quiz-integrity verification:** Both the canonical workspace and team working tree passed **269 offline tests**. The synthetic mounted API check covered two browser profiles, teacher-published questions and quiz-driven plan changes; an assistant-operated localhost browser also inspected the updated plan and paused-practice screens. Full logs are retained under ignored `Directions/git_delivery/` as `m2_quiz_final_canonical_tests.log` and `m2_quiz_final_team_tests.log`. A subsequent wording-only JavaScript change passed `node --check`. This does not establish shared beta/graph learner identity, human teaching review, independent evaluation, a live-model result or fresh Compose operation.

**Graph quiz recovery verification:** The canonical workspace and team checkout each passed **275 offline tests** across the four suites, with the team checkout using the canonical local data through `SOCRATES_SOURCE_WORKSPACE`. The first canonical run lacked subprocess `PYTHONPATH` (274 passed, one failed); the first team run omitted the data-root setting (241 passed, 34 setup errors). The corrected runs passed; logs are in ignored `Directions/git_delivery/`. These are synthetic stub-model checks, not live-provider or human review. [Details](GRAPH_QUIZ_RECOVERY.md).
