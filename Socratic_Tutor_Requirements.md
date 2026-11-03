# Socratic Tutor - Capstone Requirements Checklist

Prepared on 20 October 2026 from the user's programme email and the 17-page guide dated 16 October 2026. The user confirmed that the assigned project is **Socratic Tutor**.

Source PDF: `D:\Work\IITB\Socratic Tutor\reference\Capstone_Project_Guide.pdf`.

Source map: common architecture and requirements, pages 1-3; roles and stack, pages 4-5; evaluation and submission, pages 5-6; Socratic Tutor brief, pages 11-12; viva preparation, page 17. Dates below come from the email.

Unchecked boxes represent requirements to address, not a claim that the team has made no progress. Suggestions and unresolved choices are identified separately.

Second constraint audit completed on 20 October 2026 against the common requirements, Socratic Tutor brief and viva instructions. Page references below refer to printed PDF page numbers. Mandatory features, approximate targets, stack defaults and optional extensions are distinguished in section 15.

## 1. Dates, team rules and allocation

| Item | Requirement or status |
| --- | --- |
| Assigned project | Socratic Tutor, confirmed by the user |
| Team | Six members; distribute work fairly and ensure every member contributes |
| Communication | Connect using the group introduction email thread |
| Final submission | **12 November 2026, EOD**; the email says there will be no extension |
| Review and live viva | **15 November 2026**; all six members must be prepared |
| Campus immersion | **22 November 2026**; completion certificates to be distributed |

- [ ] Assign names to the six roles at the start.
- [ ] Maintain a contribution log and decision/experiment log from the first day.
- [ ] Work on the assigned project.

The email refers to a "Group Details" section, but this PDF contains no such section or group-member allocation. It also refers to a separate cohort rubric; exact marks are not supplied here. EOD's precise time/timezone and the submission destination are not specified in the supplied material.

## 2. Product goal and scope

Build an NCERT-grounded tutor for a Class 9 or 10 student, with a teacher view. It must identify misunderstandings, give Socratic hints, check student work, and plan subsequent practice using the learner's history.

Scope decision confirmed by the user on 20 October 2026: **Class 10 Maths - Quadratic Equations, Arithmetic Progressions, Introduction to Trigonometry**. The proposed source/data plan is in `Socratic_Tutor_Data_Plan.md` beside this checklist.

Data preparation update: `socratic_tutor_dataset/README.md` describes the extracted sources and machine-validated review-ready dataset. Human approval, independent evaluation ownership and actual application-run evidence remain open; dataset creation does not complete the implementation requirements below.

- [ ] Select **one subject and three or four chapters**.
- [ ] Use NCERT textbooks and exemplar problems.
- [ ] Create a prerequisite graph of **about 25 concepts**.
- [ ] Write **8-12 misconceptions per chapter**, ideally with a teacher.
- [ ] Provide student chat, separate practice and quiz modes, and a teacher view.
- [ ] Preserve equations when processing textbook sections.
- [ ] Keep class, chapter and section metadata, plus source/date metadata required by the common minimum bar.
- [ ] Keep NCERT source PDFs out of the repository; the guide allows their use within the project but prohibits redistribution in the repository.

- [ ] Deliver a working end-to-end minimum across every common layer, then develop both signature challenges in depth. Focusing on signature areas does not waive other minimum requirements (page 1).

Science and Maths examples in the guide are examples, not an instruction to cover both subjects. The user has selected the three Maths chapters listed above.

## 3. Both signature challenges are required

### A. A learner model that changes teaching

- [ ] Track mastery by concept, observed misconceptions and explanations that worked.
- [ ] Use that information to choose hints, practice difficulty and next concepts.
- [ ] Revise the study plan **after every quiz**.
- [ ] Return to prerequisite concepts when needed.
- [ ] Demonstrate two students asking the same question receiving different teaching based on their learner models.

### B. Measure teaching using simulated students

- [ ] Build **40 simulated students**, each played by an LLM with a hidden card specifying knowledge state, a persona and one or two seeded misconceptions.
- [ ] Measure misconception identification, answer leaks and change in quiz score.
- [ ] Separate development students from held-out students; do not tune and test on the same students.
- [ ] After each development session, have an evaluator score it and a reflection step produce a lesson linked to the misconception and stating when it applies.
- [ ] Have a person review each lesson before admission to the playbook.
- [ ] Retrieve relevant lessons for later sessions and freeze the playbook before held-out testing.
- [ ] Keep simulated-student cards hidden from the tutor, including the knowledge state and seeded misconceptions (page 12).
- [ ] State explicitly that simulated-student results are not evidence from real students.

Optional sanity check from the guide: try the tutor with three to five real students, with consent. This is not part of the minimum required scope.

## 4. Student and teacher behaviour

- [ ] Check inputs for age suitability, personal information and prompt injection.
- [ ] Load the learner model before routing the request.
- [ ] Ask a probing question to diagnose a misconception.
- [ ] Retrieve the relevant NCERT section, filtered by class and chapter, and give a cited Socratic hint.
- [ ] Prohibit complete worked solutions in practice mode through hooks.
- [ ] Prevent answer-key extraction in quiz mode, including a student's claim to be the teacher.
- [ ] Select practice questions at the appropriate difficulty.
- [ ] Calculate numeric answer keys using a solver before showing questions.
- [ ] Grade numeric/algebraic responses with solver, equivalence or tolerance checks; grade explanations using a rubric.
- [ ] Update mastery, misconceptions, useful explanations and the study plan.
- [ ] Let teachers approve new question sets before publication to the shared question bank.
- [ ] Keep only approved sets in the published question bank (Figure 4, page 11).
- [ ] Alert the teacher when a student remains stuck on the same concept for **three sessions**.
- [ ] Hand off signs of distress to a human immediately.

## 5. Architecture, agents and MCP tools

Use a LangGraph supervisor/study planner plus four specialists:

| Agent | Responsibility |
| --- | --- |
| Diagnostician | Probe the student's understanding and identify misconceptions |
| Tutor | Produce textbook-grounded Socratic hints |
| Grader | Check work with solver tools and a rubric |
| Question setter | Select appropriate questions and propose new question sets |

- [ ] Give each agent only its own necessary tools and use typed hand-off messages.
- [ ] Allow only the question setter to propose items to the shared question bank.
- [ ] Build a single-agent baseline using the same tools and budget.

The common minimum is three MCP servers; the Socratic Tutor brief specifically names **four**, so implement these four:

| FastMCP server | Tools or capabilities |
| --- | --- |
| `textbook-kb` | Search, get section, get exemplar |
| `math-tools` | Solve, check equivalence, numeric check with tolerance |
| `learner-store` | Read learner state and update mastery |
| `question-bank` | Propose questions and publish an approved set |

- [ ] Use typed tool inputs/outputs and structured error results.
- [ ] Mark tools as read or write, enforce permissions and provide **one test per tool**.
- [ ] Place question-set publication behind the approval gate.
- [ ] Explain why the internal learner mastery update needs no separate human approval, as requested explicitly in the tutor brief. This is a specific exception to the general approval rule; publishing a question set still requires approval (page 12).
- [ ] Use pre-tool hooks for mode rules, permissions and budgets; use post-tool hooks for logging and scrubbing.
- [ ] Treat retrieved passages, pasted homework and tool results as data rather than instructions.
- [ ] Put numeric calculations, answer checks and permission enforcement in code.

## 6. Common technical minimum and required evidence

| Area | Build requirement | Review evidence |
| --- | --- | --- |
| Prompting, L1-L3 | Use all six slots (role, context, task, constraints, format, examples) for every agent, critic, judge and reflection prompt. Set context length and temperature deliberately. | Versioned prompts and model configuration |
| Retrieval, L4-L6 | BM25 plus vector search combined with Reciprocal Rank Fusion, a reranker, one query-side technique, source/date metadata and passage-ID citations | Recall@5 on **30+ labelled queries**, before and after one change |
| Tools, L7 | FastMCP, typed schemas, structured errors, least privilege | Tool inventory, schemas, one test per tool |
| Orchestration, L8 | Typed LangGraph state, conditional edges, one self-correction loop, persistent checkpointing | Own graph diagram; live stop-and-resume demonstration |
| Memory, L9 | Trim/summarise short-term context and add a long-term store | **One-page memory policy** and memory-on versus memory-off comparison |
| Planning, L10 | Display a plan object, replan on contradictory tool results, ReAct inside specialists | A trace showing a replan |
| Multi-agent, L11 | Supervisor and at least three specialists; tutor brief uses four | Comparison with a single agent under the same tools and budget |
| Improvement, L12 | Reflexion on development data, code-first scoring, human-reviewed lessons, relevant retrieval, frozen playbook | Held-out before/after results, playbook, one rejected lesson and its rejection reason |
| Evaluation/monitoring, L13 | Golden set, outcome/trajectory/tool checks, calibrated different-family judge, traces, Grafana | Evaluation report, judge agreement and dashboard |
| Human control, L14 | `interrupt()` with approve/edit/reject for external actions; approval bound to exact payload | Live edit invalidates the prior approval |
| Security, L15 | Input/output guardrails, least privilege and **30+ attacks**, including injection through the data path | **One-page threat model**; attack success and false blocks with defences off/on |
| Deployment, L16 | Streaming FastAPI; `docker compose up` starts app, MCP servers, vector store, Prometheus and Grafana; prompts and exact model IDs in one versioned config; CI fails below an evaluation threshold; working alert | Clean-machine installation and one failed CI run with explanation |

The memory policy must cover what is saved, when, who can read it, correction and deletion. For this project, explain what is retained about a minor and omit student names/personal details from traces.

The reference architecture includes authentication and sessions. The serving stack must support the student and teacher interfaces and the required approval/resume flows.

## 7. Evaluation datasets and separation of responsibilities

| Set | Required size and purpose |
| --- | --- |
| Golden questions | **At least 60 questions with verified answers**, for grading and retrieval; the tutor brief says 60 and the common minimum is 60+ cases |
| Development/held-out golden split | About **20 development** and **at least 40 held-out** cases; keep related scenario variants together |
| Retrieval labels | **30+ labelled retrieval queries** for Recall@5 |
| Simulated students | **40**, with separate development and held-out students; the guide does not prescribe an exact student split |
| Rubric-assessed transcripts | **20**, assessed using a teacher's rubric and compared with the judge. The guide does not explicitly say a teacher must personally score all 20; human labels are separately required for judge calibration. |
| Judge calibration | **20+ human-labelled outputs**, report Cohen's kappa; judge must be from a different model family |
| Red-team attacks | **30+**, including homework injection and answer extraction |

These are different evaluation requirements. Sixty questions do not replace the student or security evaluations. If a case or transcript serves more than one measurement, document that reuse and preserve the development/held-out separation; reusing a development case does not make it valid held-out evidence.

- [ ] Write expected outcomes before running the agent.
- [ ] Keep held-out cases in a location the agent cannot read.
- [ ] Keep gold answers out of prompts and tools used to solve evaluation cases.
- [ ] Use code first for answer correctness, citation existence, tool use, forbidden actions and database state; use a judge only where code cannot decide.
- [ ] Check outcomes, trajectories and tool use, and do not assess teaching solely through an LLM judge (pages 3 and 12).
- [ ] The person tuning the agent must not author held-out cases.
- [ ] The person implementing defences must not author the attacks.
- [ ] Evaluation owner owns held-out cases and attacks; domain lead checks held-out cases against written policy.
- [ ] If the design is changed after viewing held-out results, disclose it and treat those cases as development data.

## 8. Four required experiments

Use one harness and a configuration file per experiment, rather than separate code branches.

| Experiment | Required comparison |
| --- | --- |
| E1: Value of agents | C0 fixed workflow or single retrieval prompt with no agent decisions; C1 one agent with tools; C2 multi-agent team. Hold model, tools and budget constant. |
| E2: Security | Defences off versus on, on both attacks and clean tasks; measure attack success and legitimate tasks blocked. |
| E3: Improvement | Held-out performance before versus after the reviewed playbook; include lesson-generation cost and identify harmful lessons. |
| E4: Tutor signature ablation | Learner memory off versus on, and direct answers versus Socratic hints; compare answer leaks with simulated-student quiz gains. |

- [ ] Repeat the final held-out comparison **three times** and report variability.
- [ ] For every configuration report task-success counts, policy violations, attack success, false blocks, cost/case, median latency, p95 latency and errors.
- [ ] Include failed and timed-out runs.
- [ ] Measure tutor-specific outcomes: misconception detection, answer leakage and quiz-score gain.
- [ ] Record outcomes, cost, latency and errors in traces/metrics for each run.
- [ ] Report the spread across the three final runs, not only a selected or averaged success result.

## 9. Teacher dashboard and alerts

- [ ] Show misconceptions by concept across the class.
- [ ] Show answer leaks and changes in mastery.
- [ ] Show waiting question-set approvals and cost per session.
- [ ] Configure a working alert for a spike in answer leaks.
- [ ] Implement the three-session stuck-student alert and immediate human distress handoff.
- [ ] Keep traces for every LLM and tool call without student names or personal details.

## 10. Six roles to assign

| Role | Responsibility in this project |
| --- | --- |
| Domain and product lead | Define student/teacher needs, scope, written teaching policies and golden-set content; coordinate teacher input and own the demo |
| Knowledge and memory engineer | NCERT ingestion, retrieval/reranking, concept-linked learner memory and privacy policy |
| Agents and orchestration engineer | LangGraph, planner, four specialists and Reflexion loop |
| Tools, control and security engineer | Four MCP servers, solver integration, hooks, approval gate, guardrails and threat model |
| Evaluation and red-team engineer | Harness, held-out questions/students, attacks, judge calibration and experiment reporting |
| Deployment and operations engineer | FastAPI, student/teacher UI, Docker Compose, CI, tracing, dashboards and alerts |

All six must explain their own contribution in depth and redraw/explain the full architecture. Fair distribution and active participation are explicit email requirements.

## 11. Submission package

- [ ] Repository with a README that starts the system with **one command**.
- [ ] Team's own redrawn architecture diagram.
- [ ] Numbered walkthrough tracing a request through the architecture.
- [ ] One-page threat model.
- [ ] One-page memory policy.
- [ ] **4-6-page evaluation report** with fair experiments, metrics and limitations.
- [ ] Experiment log.
- [ ] Contribution log.
- [ ] Presentation slides.
- [ ] Backup recording demonstrating the working project.
- [ ] Exclude API keys, private data and material that cannot be redistributed, including the NCERT PDFs.
- [ ] Identify the real intended user, measure an outcome and state limitations; trace a request through the architecture and present results with context (page 6).

## 12. Demonstration and viva

The Socratic Tutor brief asks for these demonstrations:

- [ ] Identify and address the concave-mirror misconception with hints (the guide's Science example).
- [ ] Show a quiz answer verified by the solver.
- [ ] Refuse answer-key extraction when a student claims to be the teacher.
- [ ] Show a teacher approving a question set and viewing class misconceptions.

Also demonstrate the common requirements: checkpoint resume, contradictory evidence causing replanning, two learner profiles receiving different teaching, and an edit invalidating an earlier approval.

Implementation interpretation, not an additional explicit instruction: because Maths is an allowed subject, an equivalent Maths misconception is a reasonable adaptation of the Science demo. The guide itself specifies only the concave-mirror example; record the chosen adaptation and account for any separate cohort demo instructions.

Prepare every team member to explain:

1. A complete request path and what each architecture box decides.
2. Which decisions belong to the model, code or a person.
3. The single-agent baseline and multi-agent quality/cost trade-off.
4. An experiment that changed the design.
5. Traces for missing evidence, a failed tool and an injected instruction.
6. What memory retains, why and how it can be deleted.
7. Which lessons improved unseen cases and the evidence for that claim.
8. What is needed before a supervised pilot with real users.

The guide describes roughly equal emphasis on scope/impact, technical depth/execution, presentation and individual viva; exact percentages are governed by the separate cohort rubric. AI coding tools may help implement, but learners must own problem framing, design, evaluation and interpretation.

## 13. Guide defaults and optional items

The guide's common stack defaults are OpenRouter; LangGraph with a SQLite/Postgres checkpointer and a LangGraph store for long-term memory; FastMCP with `langchain-mcp-adapters`; Chroma or Qdrant, `rank-bm25` and a cross-encoder reranker; layered content/injection guards; pytest and a JSONL evaluation runner; LangSmith or Langfuse traces; Prometheus/Grafana; FastAPI and Streamlit, Chainlit or Gradio; Docker Compose and GitHub Actions.

Additional stack directions on page 5: use `interrupt()` and `Command(resume=...)` for approvals, stdio for MCP during development and HTTP inside Docker. The guardrail defaults name Llama Guard 4, a small injection classifier such as Llama Prompt Guard 2, and rules in hooks; several layers are called for, rather than a single filter. The observability default connects FastAPI's `prometheus_client` to Prometheus and Grafana. These are guide directions/defaults; any replacement should be recorded with its rationale rather than silently omitted from the design.

It suggests specialist models such as `openai/gpt-4o-mini` or `openai/gpt-4.1-mini`, a stronger supervisor/planner, and a judge from a different family. These are guide defaults, not a fresh availability or pricing check. Fix models during controlled comparisons and record exact IDs.

DSPy is optional, RAGAS may be useful, and no GPU is required. The approved architecture and minimum functionality take priority over optional extensions.

## 14. Decisions and details still to confirm

- [x] Class, subject and chapters: Class 10 Maths; Quadratic Equations, Arithmetic Progressions, Introduction to Trigonometry.
- [ ] Names assigned to the six roles.
- [ ] Teacher/domain expert involvement and transcript rubric.
- [ ] Mastery update rule, concept graph and written mode policies.
- [ ] Development/held-out split for simulated students.
- [ ] Approval identity/permissions and memory retention/correction/deletion policy.
- [ ] Models, deployment environment and project budget.
- [ ] CI pass/fail threshold and alert trigger definitions; the guide requires an evaluation gate and working alerts but does not prescribe their numerical values.
- [ ] Submission portal, precise EOD interpretation and any slide/video duration limits.
- [ ] Separate cohort rubric and any additional programme-level rules.

These are planning choices or missing administrative details, not extra requirements invented by this checklist.

## 15. Constraint audit: how to interpret the guide

| Constraint or nuance | Classification and source |
| --- | --- |
| Every common layer must work, and both signature challenges must be completed | Required; pages 1, 3, 6 and 12. The two challenges carry most of the technical marks; exact weight is not given. |
| One subject, three or four chapters | Required scope; page 11. The Science examples list only two chapter titles, but do not explicitly relax the stated three/four-chapter scope. |
| About 25 concepts; 8-12 misconceptions per chapter | Approximate concept count and stated misconception range, respectively; pages 11-12. |
| Four named tutor specialists and four MCP servers | Tutor-specific build specification; page 12. The general three-specialist/three-server minimum does not replace the tutor specification. |
| Internal mastery update versus publishing a question set | The brief explicitly asks why the mastery write needs no approval; publication must be gated. Do not treat every memory update as a teacher approval request or extend the exception to publication; page 12. |
| Practice-mode full solutions and quiz-mode answer extraction | Both need controls; pages 11-12. A user's claim to be a teacher is an explicit attack case, not proof of permission. |
| Memory use must change behaviour, not only store history | Show different responses for two learners asking the same question and replan after every quiz; page 12. |
| Three sessions stuck versus any sign of distress | The former triggers a teacher alert; the latter requires immediate human handoff, without waiting three sessions; pages 11-12. |
| At least 60 golden cases, 40 simulated students, 20 rubric-assessed transcripts and 30+ attacks | Distinct evaluation obligations, not interchangeable counts; pages 3, 5 and 12. The exact development/held-out student split is not specified. |
| Evaluation independence | Expected outcomes must predate agent runs; keep related variants in one split; hide held-out cases and gold answers from the solving agent; separate tuning from held-out authorship and defence construction from attack authorship; page 5. |
| Prompt structure, judge family and fair baselines | All agent/critic/judge/reflection prompts use six slots; judge uses a different model family; C0/C1/C2 use the same model, tools and budget; pages 1, 3, 5-6. |
| Lesson evidence | Human review for every accepted lesson, one rejected lesson with a reason, freeze before held-out evaluation, include generation cost and identify harmful lessons; pages 3 and 6. |
| Failed runs and repeated results | Count failures/timeouts, repeat the final held-out comparison three times, report spread and disclose post-held-out tuning; page 6. |
| Required operational demonstrations | Live checkpoint resume, replan trace, edit invalidating approval, clean-machine install, one explained failed CI run and a working alert; page 3. |
| Real students, DSPy, RAGAS and GPU | Three to five consenting real students are an optional sanity check; DSPy is optional; RAGAS is suggested if useful; no GPU is needed; pages 3, 5 and 12. |
| Avatars, on-device delivery, multilingual support and other projects' domain rules | Avatars/on-device delivery describe a previous team, not this build. Multilingual verdicts, insurance two-level approval and incident shell restrictions belong to other project briefs, not additional Socratic Tutor requirements. General security/least-privilege rules still apply. |
| Source material and authorship | Do not redistribute NCERT PDFs, expose private data or commit API keys. AI coding tools are permitted, but learners own framing, design, evaluation and interpretation; pages 6, 12 and 17. |
| Administrative gaps | Exact rubric weights, submission destination, precise EOD definition and slide/video limits are absent; consult the separate cohort instructions rather than inventing them. Dates come from the user's email. |

This audit covers the supplied email and PDF. Separate programme guidelines or later instructor instructions may add constraints that are not present in these sources.
