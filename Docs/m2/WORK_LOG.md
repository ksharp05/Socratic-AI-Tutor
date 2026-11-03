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

## Open acceptance gates

- Real-model, cited active-problem hint and end-to-end trace: not run. Automatic approval review rejected the probe because it could transmit local textbook excerpts to the provider absent explicit approval for that transfer.
- Fresh-clone Docker/Compose on a Docker-capable machine: not verified here.
- Full single-application learner-state integration, general protection for arbitrary homework, and external/human alert delivery: not demonstrated.
- Human educational review, independent final evaluation and course participation approval: remain external requirements.

Raw development artifacts are retained under the ignored local `Directions/git_delivery/` workspace. Do not commit protected source text, session state, keys or held-out content.
