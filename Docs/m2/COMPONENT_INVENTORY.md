# Milestone 2 component inventory

Inspection baseline: team checkout `milestone-2`, parent commit `b3f0d6d4ee958e4498c16a0aaeca84b141ffdfe0`; 3 November 2026. Subsequent working-tree changes are not included in that commit. Status is based on source inspection and the checks noted here, not an acceptance sign-off.

| Component | Actual entry point | Status and evidence |
|---|---|---|
| Original capstone API and teacher interface | `src/tutor_api/main.py`, `ui/app.py` | Basic separate student and teacher routes; authenticated principals, graph and payload-bound approval. API and UI acceptance in the M2 journey remains to be demonstrated. |
| LangGraph and four tools | `src/tutor/app.py`, `src/tutor/mcp_servers/` | Typed session graph, SQLite checkpoint and in-memory MCP transport; not evidence of the full planned distributed stack. |
| Browser beta | `src/socrates_beta/api.py`, `src/socrates_beta/static/` | Separate anonymous-browser sessions and dialogue/assessment services. Mounted at `/beta` only when the team API is explicitly configured. Its learner state is not the team graph's learner state. |
| Shared integration boundary | `src/tutor_api/beta.py` | Optional mount under the team FastAPI process. Mounted beta assessments now use the teacher-published question bank and version checks. Session models, graph learner state and traces remain separate. See [integration](MOUNTED_BETA_APPROVAL.md). |
| Beta knowledge | `src/socrates_beta/knowledge.py`, `src/socrates_beta/bootstrap.py` | Versioned SQLite registry and source IDs. Prepared-index registration has been tested in an isolated local workspace on the same computer; second-machine setup and rights for transfer remain open. |
| Maths | `src/socrates_beta/maths.py`, `src/tutor/mathcore.py` | Beta wraps existing checked-maths kernel with 665 public practice items. Code checks supported answers; teaching quality is not inferred. |
| Dialogue/model | `src/socrates_beta/dialogue.py`, `src/socrates_beta/language.py`, `src/tutor/llm.py` | Live provider adapters and labelled fallback exist. The beta's own active-problem branch currently uses deterministic coaching instead of a model call. |
| Contextual graph preview | `src/v02_integration/runtime.py` | Opt-in candidate adds guarded generation to active graph items; not enabled in the shared application and not human-approved. Do not represent prior development probe as milestone acceptance. |
| Evaluation | `src/tutor_eval/harness.py`, `src/tutor_eval/arms.py` | C2 POC and a provisional C1 single-controller development baseline now run both development cards offline. They share deterministic components and simulator; no live or independent comparison has been made. |
| Deployment | `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` | API and UI configuration exist, monitoring is an optional profile, and default model is a stub. Docker and clean-clone acceptance not verified in this environment. |

Baseline regression: 115 passed in the local beta, book-pipeline, v0.2 integration and original API suites before M2 code changes. Test scope is engineering behavior, not independent teaching evaluation.
