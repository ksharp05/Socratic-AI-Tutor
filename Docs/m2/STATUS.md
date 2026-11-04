# Milestone 2 status and engineering decision

**Date:** 4 November 2026. **Evaluated code:** `b11c2bbce623022fe81882260bccb4fff3b65dc3` on local branch `milestone-2`. **Decision:** continue local development testing; **Milestone 2 acceptance is not verified**. This is an engineering assessment, not teacher sign-off or a course decision. Nothing was pushed during this work.

## What works in the local development path

The authenticated connected graph supports English-medium Class 10 Quadratic Equations, Arithmetic Progressions and Introduction to Trigonometry. It has chapter-pinned references and saved citations, selected checked practice, payload-bound teacher publication, separate development quizzes, saved learner observations and quiz-driven chapter plans. The mounted anonymous beta is a separate identity/state path; its presence does not unify the two learner stores. See the [run guide](../RUN_GUIDE.md) for the actual startup and authentication flow.

Ambiguous registered right-triangle answers can now lead to a short reasoning exchange: the learner states the reference angle and side lengths, chooses the ordered sides for the ratio, and finally submits a numeric value to the checker. Reasoning statements do not create correctness scores or mastery gains. This is a bounded English parser, not arbitrary reasoning or general conversational understanding. [Supported forms and limits](TRIANGLE_REASONING.md).

The final source tree passed **387 offline tests in each project copy**, using existing Windows Python environments, synthetic identities and the stub model. Those suites ran before the code commit; no code changed between the passing runs and that commit. They do not prove a clean installation, container behavior, educational quality or live-model performance.

## Evidence on the clean committed build

The shared checkout was clean at `b11c2bb` during all three runs. C1/C2 have matching data, code, maths-engine and development-fixture hashes. Full manifests, transcripts and local synthetic state remain in ignored `Directions/git_delivery/m2_b11c2bb_smoke/`. The [projected evidence record](ACCEPTANCE_EVIDENCE.json) retains run IDs, results and manifest/test-log hashes without exporting raw source excerpts or private data.

| Development check | Actual observation | Interpretation |
|---|---|---|
| C1 single-agent configuration | 2 synthetic sessions, 16 turns; no execution failures/timeouts; 0 of 6 submitted practice attempts checked correct; quadratic seeded cause named, trig cause not named. | The execution gate passes. Teaching success, human learning and model quality are not established. |
| C2 graph configuration | Same session/turn/attempt outcomes and seeded-cause findings as C1. | No superiority claim. Both arms share substantial code and a developer-authored simulator. |
| Provider use | Zero tutor or simulated-voice model calls in both runs. | These runs do not test the live cited-hint requirement. |
| Security | 20 synthetic cases: 8 measurable attacks, 10 measurable controls, 2 unmeasured homework attacks; no observed measured bypass, false block or execution error. | Two cases remain unmeasured; a zero observed rate is not comprehensive safety. |

The unchanged two-card simulator does not produce angle/side-definition reasoning. Its 0/6 result was not improved by tuning the fixture to the new parser, and the parser's passing examples must not be substituted for evaluation of teaching effectiveness. Historical results and failures are retained in [verification](VERIFICATION.md) and the [work log](WORK_LOG.md).

## Remaining acceptance work

| Requirement | Next evidence needed | Dependency |
|---|---|---|
| M2-01: clean Compose startup | Build/start from a fresh clone, supply an authorized hash-pinned index, verify services, readiness and restart behavior; retain logs. | Docker/Podman are unavailable on this machine. The [integrated overlay](INTEGRATED_COMPOSE.md) has local subprocess checks, not an actual container pass. |
| M2-02: live cited hint | Execute the bounded `x² = 5x` probe, then the integrated learner walkthrough; inspect the question, citation and model/tool trace. Report buffered SSE honestly. | Explicit authorization for the specified excerpt transfer, usable provider access and credits. Automatic approval review rejected the earlier live probe because retrieved local textbook excerpts could be sent to the provider without that authorization. [Payload and call limit](QUADRATIC_PROBE.md). |
| M2-03: two learners/replanning | Capture the two-history and three-topic journey on the accepted integrated live build, including quiz result, plan reason and recovery. | Offline synthetic API/browser evidence exists; the live build remains unverified. External alert delivery and acknowledgement are not proven by a local alert event. |
| M2-04: teacher control | A real educator reviews the actual content and exercises edit, invalidation, reapproval and publication on the accepted build. | Synthetic teacher workflow tests establish mechanics, not human content review. |
| M2-05: comparison | Review the committed two-card smoke artifacts and run any authorized live comparison with failures/costs counted. Arrange independently authored final cases separately. | Current comparison is a non-independent, stub-model development result. |
| M2-06: safety/decision | Preserve unmeasured homework cases, inspect integrated traces and alerts, complete live safety demonstrations and record human acceptance or explicit exceptions. | Current observations cover limited synthetic cases; the engineering decision remains no acceptance claim. |

Source-transfer/redistribution rights, actual educator approval, independent evaluation ownership and the program's solo-participation/viva requirements are human decisions. None is inferred from generated data or checked mathematical answers. The wider Classes 8-12 textbook collection is outside this milestone's assessed teaching scope.

No final held-out material, frozen dataset, source original or completed review was changed. Do not mark the milestone complete merely because the local regression suite or execution-only gates pass.
