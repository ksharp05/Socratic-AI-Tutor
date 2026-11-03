# Milestone 2: requirements and prerequisites

**Status:** planning and requirements only. **Target:** Wednesday, 4 November 2026, according to the [revised team roadmap](https://github.com/ksharp05/Socratic-AI-Tutor/blob/milestone-1/Docs/LEAD_ROADMAP.md). We are treating the project as a single active implementation effort; the responsibilities below are work areas, not separate people.

## 1. What Milestone 2 means

The milestone is **“all features basic”**: an integrated version of the required capstone layers works at a basic level and can be demonstrated. The exit review tests the complete flow; a large dataset, isolated tests, or a working beta screen alone is not enough.

The assessed project scope remains **Class 10 Mathematics in English**, covering Quadratic Equations, Arithmetic Progressions, and Introduction to Trigonometry, unless the project scope is explicitly revised. The broader Class 8–12 corpus and other subjects are useful extensions; their presence does not mean the complete capstone workflow is implemented or assessed for them.

The current implementation status and evidence are tracked in [the milestone matrix](m2/REQUIREMENT_MATRIX.md) and [work log](m2/WORK_LOG.md); the baseline below describes the starting point.

## 2. Where we are starting

| Area | Available now | Gap for this milestone |
|---|---|---|
| Local tutor | A Socrates-style browser beta, source-backed conversation, local session history, checked maths practice and study features. | Show the required capstone flow end to end, including its relationship to the existing graph, tools, teacher interface and traces. The browser beta and the original team application are separate paths today. |
| Source data | 145 textbook volumes; local beta index of 10,878 passages/references; 665 public practice items across the three maths chapters. | Data is excluded from Git, and a portable, authorized setup on another machine has not been validated. Source availability does not mean content or teaching has been independently reviewed. See [dataset report](datasets/DATASET_REPORT.md). |
| Tests | The last local engineering check passed 115 tests across beta, ingestion, integration and API suites. | Repeat relevant checks on the actual milestone build and retain evidence; automated tests do not replace the integrated demo or pedagogy review. |
| Deployment | Dockerfile, Compose, FastAPI, Streamlit, Prometheus and Grafana configuration exist. | Docker is not available on the current computer; no fresh-clone Compose acceptance run has been verified here. Default Compose uses the stub model. |
| Conversation and evidence | The local beta has recorded live-model development scenarios and source citations. | Demonstrate the milestone's specific cited hint, with model identity and an end-to-end trace. Current API SSE chunks an already-completed response; it is not evidence of model-token streaming. |
| Security and approvals | Code exists for guards, tool permissions and a payload-bound teacher approval graph. | Verify the complete teacher-page edit/approval invalidation and security demo on the integrated build. |
| Evaluation | A development harness and simulator exist; 34 beta scenarios have been run. | Show C1 versus C2 on two development student cards, with complete logs. Current beta results are development results, not an independent final score. |
| Git and CI | `milestone-1` is on GitHub; a local `milestone-2` branch has been created from it. CI configuration exists. | Review any incoming changes before integration, run the relevant checks, and obtain actual CI evidence. No Milestone 2 implementation or push is implied by this document. |

## 3. What must be demonstrated to finish Milestone 2

These are the project's own M2 exit checks in the revised roadmap. A check should be marked done only when the actual integrated build produces repeatable evidence.

1. **Clean start:** from a fresh clone, start the required services using `docker compose up`; confirm service health and document the setup. Demonstrate how the local authorized data is supplied without putting protected content or credentials in the repository.
2. **Real, cited Socratic hint:** use the example `x² = 5x` and show a live-model hint that asks a useful question instead of revealing the solution. Show the citation and an end-to-end trace, including the model and tool decisions. Show streaming behaviour honestly: server-sent chunks after generation and true model-token streaming are different.
3. **Personalized learning:** demonstrate two learners receiving different teaching, then submit a quiz and show the resulting plan change and its reason in a trace.
4. **Human approval:** from the teacher interface, show that editing a proposed question set invalidates the previous approval, and that publication requires approval of the exact current payload.
5. **Evaluation smoke run:** run the C1 single-agent and C2 multi-agent configurations on two development simulated-student cards. Record the configurations, run IDs, observations, failures and timeouts; do not present the result as a final independent comparison.
6. **Safety and decision:** demonstrate the input/output guardrails, quiz-answer protection, citation checks and tool permissions. Prepare at least 10 additional development attacks with matching benign controls, record their provenance and limitations, and document the milestone go/no-go and any cuts.

The general bar is an honest end-to-end implementation of the guide's required layers, not only the five demonstration flows. See [capstone requirements](plan/01-requirements.md) and [delivery and cut lines](plan/09-delivery.md).

## 4. Technical work needed

### A. Integration and deployment

- Decide and document how the browser beta and existing capstone application connect: tutor/graph, checked maths, retrieval, sessions, teacher approvals, and observability must be exercised as one described flow. Preserve clear boundaries between the two paths while integrating.
- Provide a reproducible clean-checkout setup with versioned dependencies, a documented local data preparation/registration path, health checks and a one-command Compose start. Do not commit textbook content, source extracts, held-out cases or secrets to provide convenience.
- Validate the Compose services actually required by the capstone, including the application, tool/retrieval dependencies and observability components. Document any gaps or substitutes rather than claiming the present Compose file already supplies the entire planned stack.
- Run the end-to-end check on a Docker-capable machine. Keep a local non-Docker path for development and document differences.

### B. Socratic conversation and learner model

- Make the selected demo path use an authorized live model and source-grounded context. Show focused, natural English questions, correct citations, bounded context and a clear fallback when the model or evidence is unavailable.
- Preserve active-problem and quiz boundaries: no full solution or hidden answer key for the question being worked on; code checks supported mathematical answers.
- Verify learner state, misconception/diagnosis, planning, and replan after quiz results. Demonstrate two different learner histories and explain what data is retained and deleted.
- Verify that model, tool and guard decisions appear in a useful trace. Do not call buffered response chunking real-time token streaming.

### C. Teacher control and safety

- Connect and test the teacher approval workflow, with authentication and approval bound to the exact question-set payload. Test that edits invalidate old approvals.
- Exercise mode-specific tool permissions, injection handling, role-claim refusal, citation validation and answer-leak protection. Keep known gaps visible and count false blocks as well as attacks.
- Demonstrate the teacher-facing view and alert paths. The brief calls for an alert when a learner is stuck on a concept for three sessions and a human handoff for distress; an internal event is not proof that a human was actually notified.

### D. Evaluation and observability

- Confirm the development simulator, C1/C2 configurations and harness execute consistently; store run IDs, configuration/data hashes, model names, latency, cost when available, failure counts and output artifacts.
- Prepare a versioned development security set with matching benign controls. Because the same active implementer may also author the tests and defences, explicitly label the resulting evaluation **non-independent**. Do not use hidden or final held-out cases for tuning.
- Exercise the API/UI trace, relevant dashboard and alert. Verify what is actually emitted; an untested configuration file alone is not evidence of a working alert.
- Run the appropriate automated suites and the CI evaluation gate for the actual milestone commit, plus a real-model smoke test with a bounded call budget.

## 5. What we need before or during implementation

| Need | Why it is needed | Current position / action |
|---|---|---|
| Docker Desktop or another compatible Docker/Compose environment | Required for the clean-clone milestone demonstration. | Docker CLI is not available on this computer as checked on 3 November. A suitable environment must be installed/configured or another authorized machine used. |
| An authorized model key and internet access | Required for the real-model hint and live smoke test. | Use the existing personal course/provider setup if it works. Never paste a key into chat, Git, logs or screenshots. Live calls may consume credits. |
| Access to the local source collection and beta index | Needed to reproduce source-grounded answers and data versioning. | Existing data is on the project computer under ignored `Directions/`. A fresh machine needs a tested and authorized data setup; copying an existing registry alone is not portable because it contains absolute paths. |
| Runtime and disk resources | Needed for a clean install, indexes, containers and optional monitoring. | Confirm sufficient disk, memory and a compatible Python 3.12 environment; record actual build requirements during the clean run. |
| A teacher/reviewer for actual approval and assessment | A simulated teacher can test workflow mechanics, but cannot stand in for required real human review. | Reviewers were to be assigned later. Prepare a review queue and evidence; do not claim human approval before it occurs. |
| Independent assessment ownership | Required to make final held-out evaluation credible. | A single implementer can run development checks, but cannot make their own seen cases or tuning independently authored. Arrange an independent person or disclose the unmet requirement; keep final cases separate. |
| Clarification from the program if only one person remains active | The user-provided course instructions require six members to explain their contributions in the viva. | Confirm the program's expectations and any approved change to team participation. Do not assume the solo-working arrangement changes course requirements. |

## 6. Data and evaluation constraints

- Do not redistribute NCERT PDFs, extracted text or derived indexes until the applicable permissions/terms are established. Keep provenance, source hashes and review status with any authorized data transfer.
- The current broader collection is not automatically usable for every subject, language, formula, table or diagram. Preserve the Class 10 maths capstone boundary for the assessed demo.
- Keep source originals, frozen builds and completed review records unchanged. Do not place answer keys, private student material or held-out cases in model prompts or Git.
- Mathematical checking can verify supported answer forms; it does not verify the educational quality of a hint, source interpretation or a human review.
- Protect final held-out material from tuning and report prior exposure. Human rubric labels and reviewer approval cannot be fabricated or inferred from generated records.
- Report code checks, citation/source checks, safety results, teaching-quality judgments and learning outcomes separately. Count failures and abstentions, and do not call development completion an independent accuracy score.

## 7. Recommended execution order after approval

1. **Freeze the target and inventory the two existing app paths:** identify what each M2 demonstration uses, how they integrate, and which current features are only partial.
2. **Make the clean setup reproducible:** application dependencies, authorized local data registration, configuration and Compose; test it in an isolated clean environment.
3. **Deliver the live cited maths walkthrough:** model connection, correct topic, source citation, Socratic hint, trace and honest streaming status.
4. **Complete the learner and teacher demonstrations:** two learners, quiz replan, approval, edit invalidation and teacher-visible state.
5. **Exercise safety and evaluation:** guarded modes, controlled attack/benign pairs, C1/C2 development runs, logs, costs, dashboard and alerts.
6. **Run milestone checks and document the decision:** retain test output, build/trace/run IDs, known failures and a short go/no-go record. Arrange any human or independent review that cannot be done by the implementer.

Do not cut either signature challenge, final held-out separation, payload-bound approval, failure accounting, the required one-command start, or an honest limitations section to make the milestone appear complete. Existing cuts and the evaluation plan are documented in the project plan.

## 8. Later submission requirements to keep in view

These are not all required to be completed as part of the M2 smoke demo, but must not be mistaken for work already finished:

- A golden set of at least 60 cases, approximately 20 development and at least 40 held out; the project evaluation plan proposes a larger split.
- The simulated-student challenge (40 student cards in the brief), E1–E4 comparisons, code-first checks, and required repeated held-out comparisons with failures counted.
- A different-family judge calibrated against at least 20 human labels, teacher transcript review, and appropriately reviewed lessons/playbook.
- A one-page threat model and memory policy, numbered architecture walkthrough, evaluation report, experiment and contribution logs, slides, recorded demonstration and functioning repository.
- Final submission by **12 November 2026, end of day**, and project review/viva on **15 November 2026** as communicated by the program.

## References

- [Capstone requirements and traceability](plan/01-requirements.md)
- [Team schedule](plan/08-schedule.md) — older dates conflict with the revised roadmap; use the revised milestone date above.
- [Evaluation plan](plan/05-evaluation.md)
- [Delivery, risks and cut lines](plan/09-delivery.md)
- [Dataset report](datasets/DATASET_REPORT.md)
- [Run guide](RUN_GUIDE.md)
- [Beta design](beta/ARCHITECTURE.md) and [recorded development results](beta/EVALUATION_RESULTS.json)
