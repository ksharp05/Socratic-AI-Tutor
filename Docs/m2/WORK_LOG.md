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

## Open acceptance gates

- Real-model, cited active-problem hint and end-to-end trace: not run. Automatic approval review rejected the probe because it could transmit local textbook excerpts to the provider absent explicit approval for that transfer.
- Fresh-clone Docker/Compose on a Docker-capable machine: not verified here.
- Full single-application learner-state integration and external/human alert delivery: not demonstrated.
- Human educational review, independent final evaluation and course participation approval: remain external requirements.

Raw development artifacts are retained under the ignored local `Directions/git_delivery/` workspace. Do not commit protected source text, session state, keys or held-out content.
