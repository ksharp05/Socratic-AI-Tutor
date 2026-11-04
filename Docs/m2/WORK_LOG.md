# Milestone 2 engineering work log

The following local **development** checks were collected on a working tree based on `b3f0d6d4ee958e4498c16a0aaeca84b141ffdfe0`, not evidence from an independently reviewed release commit.

- **Portable index:** `register-index` can now run before historical bootstrap and accepts an expected SHA-256. Two synthetic regression tests cover registration, wrong-hash rejection and later tampering. An authorized local copy of beta3 was registered in a separate workspace on the same machine; hash and offline API health checked, and all three target chapters returned scoped results. Fresh-machine and Docker runs remain open.
- **Boundary:** synthetic integration test verifies that an anonymous beta cookie and a student bearer token cannot access the original teacher endpoints. The two applications still keep separate learner state.
- **Learner:** an offline API test demonstrated two constructed learner histories with different routes and a three-answer quiz triggering an explicit plan-version/reason update. This is not a learning-gain study.
- **Teacher:** Streamlit AppTest with a local stub API exercised propose → approve → edit → reject stale approval → reapprove. An equivalent isolated automated test was added. No teacher reviewed educational content.
- **C1/C2:** `m2_development_c1-20261103-233732` and `m2_development_c2-20261103-233737` each ran two development cards with stub tutors, 16 turns, no execution failures/timeouts, 1/2 tasks completed and no measured full/partial leak turns. The provisional C1 uses a single graph controller with the same deterministic services, guards, learner model and tutor prompt as C2; the diagnostic model is removed. Both runs used no model calls and share the simulator and authored code; they do not establish superiority, independence or human learning.
- **Security:** `m2_development-20261103-233224` ran 10 authored attack/control pairs. Eight attacks and ten controls were measurable; two attacks were unsupported. The checks recorded no bypass or false block among measured cases. They do not measure the unsupported channels or all possible attacks. The scorer was corrected so missing checks are unknown and confirmed violations survive later errors. Cases and controls were written by the implementer; not independent.
- **Regression:** 202 offline tests passed across the team, beta, ingestion and integration suites including the single-controller and automated teacher-interface tests; rerun on the final exact commit.
- **CI:** local workflow configuration now includes the synthetic portability test, teacher UI dependency and offline C1 smoke. A GitHub Actions run on the milestone branch has not been observed.


## Subsequent safety and portability checks

- **Clean checkout:** local commit `2b72fd44fbc98215afa1c802f4240656bf41ff4f` was cloned locally, a copy of the authorized local index was registered against its existing hash, and 202 offline tests passed using the existing Python environment and external local development data. The first checkout attempt found two machine-specific test-path failures; these were fixed and both attempts are retained. This is not a fresh machine, remote clone, fresh environment or Docker verification.
- **Unverified own problem:** a synthetic model was able to disclose the answer to `x² = 5x` while the original graph reported a passing output guard. A conservative deterministic-only fallback now covers common detected learner-supplied problems across C1/C2 and the contextual preview; a follow-up question preserves the boundary. It explicitly reports that the student's own answer was not checked. Detection is pattern-based and not exhaustive; it is not a general proof against answer leakage and also means the exact unregistered demo cannot yet use a live model.
- **Truthful handoff:** the distress response no longer says a teacher was notified merely because a local event was inserted. External delivery and human acknowledgement remain unverified.
- **Three-session event:** an explicit stuck signal on a registered item, across three distinct sessions and tied to one unambiguous concept, creates a deduplicated local teacher-view event. A checked correct attempt closes the current episode without claiming mastery. Concurrency, distinct-session counting, learner isolation and a later episode have synthetic tests. This is an inbox event, not a delivered message or human review; the original team app has no demonstrated user-facing deletion flow for this state.
- **Post-safety regression:** 209 offline tests passed on the local working tree. The matched stub C1/C2 runs `m2_development_c1-20261103-235236` and `m2_development_c2-20261103-235240` each completed 2/2 development sessions without execution errors or timeouts, solving 1/2 tasks. Security run `m2_hashed-20261103-235244` measured eight attacks and ten controls, with two attacks unsupported and no observed measured bypass or false block. These remain non-independent engineering checks with no model calls.
- **Run provenance:** current simulator and security manifests include configuration, case-file and relevant code hashes. The later runs above were made from a working tree based on `2b72fd44` and record uncommitted changes; they must be repeated for a release commit.

## Latest local regression

- The current uncommitted safety/alert changes passed **211 offline tests** across the complete local test selection. A separate clean checkout at commit `2b72fd44` passed 202 tests before these later changes; repeat the full checkout verification after the safety/alert changes are committed.
- After the safeguard, development runs `m2_development_c1-20261103-235543` and `m2_development_c2-20261103-235547` each completed two stub sessions with no execution failures/timeouts and 1/2 task success. The follow-on `m2_latest-20261103-235551` security run again measured eight attacks and ten benign controls, with two attacks unmeasured. These are limited, non-independent checks, not live or pedagogical evidence.
- Teacher alert details are returned by the learner-overview API only to an authenticated teacher; an individual student can still retrieve their own learner model but receives an empty alert list. The new tables are added to an existing SQLite database without resetting learner rows. No external delivery or acknowledgement exists.
- The detected own-homework path now returns a fixed question instead of raw retrieved passages or a generated answer; old stored sessions recover the detection flag from earlier redacted student messages. The detector is heuristic, so unrecognized phrasings remain a safety risk. No live hint for the unregistered example is claimed.

## Bounded synthetic quadratic probe — 4 November

- Removed a few-shot tutor example that contained the assessed `x² = 5x` question and its answers. The replacement is a generic question and the prompt version changed.
- Added `scripts/m2/quadratic_probe.py`, which creates an isolated synthetic development question and defaults to a fake model. The fake-model path produced a source-linked question through the graph and code-owned leak guard. This is not human approval or a real-model result.
- The optional live mode is explicitly unexecuted pending authorization of source-passage transfer. It is limited to one generation attempt, disables retries on the actual configured synchronous client, and withholds responses that fail its conservative display screen. Details and limitations: [quadratic probe](QUADRATIC_PROBE.md).
- **214 offline tests passed** on the current working tree after these changes. The last clean-checkout commit `f99504a` passed 211 tests; the new prompt and probe are later uncommitted work until checkpointed and rechecked.

## Quiz-test reliability — 4 November

An exact-checkout rerun at `2bd4102` produced 213 passes and one failure: the quiz privacy assertion matched the ordinary word “values” inside a public problem statement. The check was corrected to inspect nested JSON field names instead of arbitrary prompt text, with a control showing that a real nested `values` field is still detected. This avoids a false failure; it is a schema check, not proof that all possible answer leakage is prevented.

## Open acceptance gates

- Real-model, cited active-problem hint and end-to-end trace: not run. Automatic approval review rejected the probe because it could transmit local textbook excerpts to the provider absent explicit approval for that transfer.
- Fresh-clone Docker/Compose on a Docker-capable machine: not verified here.
- Full single-application learner-state integration, general protection for arbitrary homework, and external/human alert delivery: not demonstrated.
- Human educational review, independent final evaluation and course participation approval: remain external requirements.

Raw development artifacts are retained under the ignored local `Directions/git_delivery/` workspace. Do not commit protected source text, session state, keys or held-out content.

## Publication integrity audit — 4 November

Synthetic tests exposed three defects: an edited set remained visible, development-only unapproved rows were served by the normal tutor, and a corrupted proposal could be republished with a stale digest. These are now guarded with digest checks, explicit fixture opt-in and atomic publication/edit transactions. A further test showed that a learner could continue a stale active question or quiz; both C1 and C2 now recheck set provenance on later turns and fail closed on check failure. The current working tree passed **230 offline tests** across all four project suites. Evaluation manifests mark unapproved fixture use. [Design, evidence and remaining race](PUBLICATION_INTEGRITY.md). This is not human review, live-provider evidence or a fresh-machine run.


## Learner-turn publication race — 4 November

Regression tests reproduced teacher edits completing after a learner turn had checked approval, and resuming an interrupted turn after its set was edited. A file-backed lock now serializes cooperating local application processes at learner-turn and question-publication boundaries, while interrupted turns revalidate referenced content before resuming. A separate subprocess test verified lock contention on Windows. The full four-suite run before the final resume-after-grade test passed 235 tests; that extra test passed separately. This is not proof of locking on other hosts, direct SQL writes, Docker or remote filesystems. See [publication integrity](PUBLICATION_INTEGRITY.md).

The final working-tree selection, including same-instance contention tests, passed **238 tests** across all four suites. The canonical app environment received `filelock==4.2.6` offline from hash-checked files already installed in the local checkout.


## Canonical workspace repair — 4 November

Direct testing exposed missing tracked application modules, development fixtures, UI files and the public practice slice, plus older source revisions and missing API packages. Missing files were restored without overwriting local files; four source files exactly matching an older tracked revision were advanced, and the CLI's two existing local adaptations were retained. The workspace's dataset paths and separate project configuration were preserved. Filelock, FastAPI, Prometheus client and annotated-doc were installed into `.venv_app` offline from already-installed, hash-verified local package files. The initial collection and subsequent test run failed; after these repairs, **238 tests passed** across all four suites from the canonical directory and `tutor.cmd --help` succeeded in stub mode. Source datasets and held-out cases were not edited.


## Mounted beta approval integration — 4 November

Two new offline end-to-end tests first demonstrated that the mounted beta accepted unapproved practice and graded a question after its set was edited. Mounted assessments now use the capstone publication service, bind each selected question to the approved set and digest, check the source payload, and cancel safely on revocation or fail closed on service failure. Tests cover cached response replay, quizzes, payload mismatch, provider outage and an edit concurrent with grading. A shutdown test also exposed and fixed unclosed tutor database connections and its event-loop thread. The standalone preview remains explicitly unapproved development practice; anonymous beta and graph learner identities remain separate. [Details](MOUNTED_BETA_APPROVAL.md).

The complete canonical working-tree selection subsequently passed **248 offline tests**. The updated beta script passed `node --check`; a visual browser walkthrough of this change remains outstanding.

After strengthening the revoked-answer test to assert no checked-answer observation is written, both canonical and team working trees passed **248 offline tests**. Full local output was retained in `Directions/git_delivery/m2_mount_canonical_tests.log` and `m2_mount_team_tests.log`.

A later assistant-operated browser check used a localhost-only synthetic fixture: no approval blocked practice, a synthetic teacher publication enabled it, and an edit changed the active question to an unavailable message without a score. A narrow in-app browser layout was inspected. The server was stopped; this did not use a provider or establish human review or cross-browser accessibility.


## Beta assessment isolation and planning — 4 November

Synthetic tests reproduced cross-session feedback during quizzes, duplicate grading across service instances, partial observations after failed saves, concurrent quiz creation, dashboard and flashcard disclosure during a quiz, early-exit score disclosure, and delayed urgent guidance while a profile was busy. Assessment transitions are transactional; profile lock stripes serialize cooperating local processes; incomplete check observations remain withheld; source cards and development reports are unavailable during a check. Recognized distress phrases return immediate unsaved guidance without claiming notification. The beta plan now includes a deterministic revision and an observation-based reason; a two-profile synthetic test confirms quiz effects are isolated. The canonical working tree passed **267 offline tests** and the updated JavaScript passed a syntax check. [Behavior and limits](BETA_QUIZ_INTEGRITY.md).

A later mounted browser walkthrough exposed multi-concept questions being attributed only to their first concept. Checked observations now retain all associated concepts in one record, and the plan explains the association without claiming a cause. A two-profile mounted API test covers teacher publication, quiz completion and profile-isolated replanning. A synthetic localhost browser walkthrough also checked the plan and paused-practice screens; it is not cross-browser or accessibility certification.

The final full offline runs passed **269 tests in each project copy**; logs are retained under `Directions/git_delivery/`. The local browser walkthrough verified the synthetic quiz-informed plan and the paused-practice screen. A later UI wording-only change replaced an internal concept ID with a learner-facing next step and passed JavaScript syntax checking.

## Graph quiz interruption recovery — 4 November

A synthetic interrupted graph turn exposed duplicate learner events and a risk of overwriting newer progress when replaying a completed quiz. A payload-bound ledger now commits quiz mastery, eligible stuck-alert resolution and replanning atomically, with replay rejection and role/learner checks. Tests cover later turns, rollback, two local database connections, preservation of a later session's mastery and plan, and a pre-upgrade completed checkpoint that cannot be safely replayed. The canonical workspace passed **275 offline tests** across the four suites with `PYTHONPATH` set for subprocesses. An initial run without that environment setting had 274 passes and one beta subprocess import failure. The graph and mounted beta still have separate learner stores; this is not a live-model, educator or independent evaluation. [Details](GRAPH_QUIZ_RECOVERY.md).
The corrected team-checkout run also passed **275 offline tests**, using the existing canonical dataset through `SOCRATES_SOURCE_WORKSPACE`; the first attempt without that variable had 241 passes and 34 missing-data setup errors. Logs for both corrected runs and the unsuccessful attempts are under ignored `Directions/git_delivery/`.

A subsequent synthetic graph test found that an unreadable quiz response was counted and moved to the next question. The graph now keeps the same question open until the deterministic checker can score the response, including on the final question. No quiz mastery or plan updates are committed for the unreadable response. The regression test was observed failing before the fix and passing afterward. [Details](GRAPH_QUIZ_RECOVERY.md).
The first full run after this change had **276 passes and one failure** because an older integration test expected an unreadable response to advance the quiz. After correcting that expectation, the canonical workspace passed **277 offline tests** across all four suites.
The team checkout also passed **277 offline tests** against the canonical local data. Logs for both corrected runs are in ignored `Directions/git_delivery/`.


## Connected graph browser journey — 4 November

The mounted beta shell now offers a student-authenticated graph conversation, teacher-published quiz and graph plan. A synthetic test first reproduced same-learner quiz bypass through a second graph session. New API-path learner reservations, active-session recovery and unscored quiz exit address that case for cooperating local processes; tests also cover simultaneous starts, a second API instance, early failure, interrupted quiz recovery, another learner and teacher edits. The localhost browser walkthrough used a synthetic passage, synthetic teacher publication and stub model; it observed conversation, quiz, an unparseable answer held open, replanning, refresh recovery and leaving an unfinished quiz. This is not a live-provider or educator review and does not merge anonymous beta identity or cover the other two assessed chapters. [Details](CONNECTED_GRAPH_JOURNEY.md).

The canonical workspace passed **285 offline tests** across all four suites, and the updated browser script passed `node --check`.
Both project copies passed **285 offline tests** across the four suites; the team run used the canonical local data path. A later focused run passed nine checks after adding explicit assertions that standalone beta does not advertise the connected journey and `/chat/active` rejects missing and teacher credentials. The documented Uvicorn startup, synthetic teacher approval and student quiz were also exercised against an isolated synthetic index. Full logs are under ignored `Directions/git_delivery/`; no real provider was called.


## Answer-key integrity and question-mode violation — 4 November

Synthetic regression tests reproduced cached unverified keys being accepted on reuse, stale keys after a question changed, and old approved sets remaining visible after their runtime item changed. Verified keys are now bound to problem and solver fingerprints, corrupted or legacy entries are recomputed, and changed runtime items hide their approved set. An initial full run had 290 passes and one isolated subprocess import failure; after fixing import order, the full canonical run had **291 passes and two strict expected failures**. A third mounted-beta policy failure was reproduced separately.

All 665 public practice questions are marked practice-only, but the graph, standalone beta and mounted beta can use them as quiz questions. This is a real remaining violation; the three strict expected failures are not passes. The browser temporarily pauses quiz/diagnostic entry points and shows the limitation, but its underlying APIs do not yet enforce the policy. A synthetic localhost browser check confirmed the notice, disabled connected quiz, typed-start pause and disabled anonymous quick checks. [Details and remediation](KEY_AND_MODE_INTEGRITY.md).

## Enforced question modes and separate development quiz — 4 November

The earlier three question-mode failures are now ordinary passing tests. The graph and both beta paths select only questions explicitly allowed in the requested mode. A separate six-item, developer-authored quadratic quiz/diagnostic pack has no saved answer keys; its six givens were checked against the project's two calculation paths and an exact symbolic solver. It remains pending human review and is not an independently authored evaluation. Teacher approvals bind mode, prompt, problem, answer contract, source/review metadata and hints. Existing unbound approvals are hidden until edited and reapproved; a legacy incompatible active check is cancelled before grading. An extra development item cannot replace a catalog ID. Development evaluation manifests now hash the catalog inputs and new pack.

An assistant-operated localhost walkthrough with a synthetic teacher and learner completed the connected development quiz with a 3/3 score and plan update, and opened the mounted beta self-check. This was a stub-model synthetic test, not educator approval or evidence of learning. The walkthrough preceded a later addition of source/review fields to approval payloads; those fields were covered by the subsequent automated tests. The final canonical four-suite run passed **303 offline tests**. [Details](KEY_AND_MODE_INTEGRITY.md).


## Chapter-scoped connected conversations — 4 November

The graph accepts and pins one of the three Class 10 chapters, searches a chapter-specific normalized card index, and keeps unavailable AP/trigonometry checked practice, quiz and plan paths separate from quadratic content. New cited messages persist the actual retrieved-reference snapshot, with available textbook identifiers, hash and page anchor; older messages are not assigned current-card snapshots retroactively. The canonical four-suite offline run passed **313 tests**. A synthetic localhost walkthrough checked AP/trigonometry conversation and chapter recovery; AP citation recovery was retested after the snapshot change. Human review, rights, live-model quality and AP/trigonometry assessments and plans remain open. [Details](CHAPTER_SCOPED_RETRIEVAL.md).

The shared checkout also passed **313 offline tests** using the canonical local data path. The final generic citation-label wording was syntax-checked in both copies after the browser walkthrough.
