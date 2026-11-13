# R3 specialists: item 1 as a documented equivalent

**Status:** proposed by R3 (Poonam) on 6 November 2026. Not yet accepted by the Lead.

The tutor does not use `create_agent`. It is a LangGraph graph: code picks the route and the tools, each specialist runs under a role allowlist, and the model writes wording and can propose a diagnosis. R3 proposes this as the "equivalent" in item 1 of [R3_AGENTS.md](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/specs/R3_AGENTS.md). The main gap is that the model never chooses a tool.

## Who does what

| Specialist | Graph nodes | Tools allowed | What the model does | What code decides |
|---|---|---|---|---|
| Planner | `planner` | None | Nothing | The route, by rules |
| Diagnostician | `diagnose`, `propose_diagnosis`, `verify_diagnosis`, `clarify_evidence`, `check_reasoning` | `textbook-kb.search`, `learner-store.read_learner`, `math-tools.diagnose_response`, triangle checks | Picks from the catalogue and writes one question. Proposes a diagnosis with `TUTOR_MODEL_DIAGNOSIS=1` | `_safe_question`, `diagnostic_workflow.verify`, and the catalogue probe as fallback |
| Tutor | `tutor`, `tutor_extension` | `textbook-kb.search`, `textbook-kb.get_section` | Writes the turn | Reply shape (TP-T1), real citations (TP-T2), hint stages, after the last hint |
| Grader | `grade`, `quiz_answer` | `math-tools.check_equivalence`, `parse_answer`, `diagnose_response` | Rewords wrong-attempt feedback, only with `TUTOR_CONTEXTUAL_HINTS=1` | Every verdict |
| Question setter | `set_question`, `quiz_start` | `question-bank.list_published`, `candidate_items`, `propose_set`, `math-tools.solve` | Nothing | Which published item to use |
| Output guard | `output_guard` | `math-tools.leak_check` | Nothing | Leak and citation checks |
| Study planner | `load_learner`, `update_memory` | `learner-store` writes | Nothing | Mastery and plans |

Permissions are enforced in `PERMISSIONS` in `src/tutor/toolbus.py`.

## Model calls per turn

Measured with a fake model on Beta `df0ab94` plus PRs #4 and #5, so no provider was called.

| Student turn | Route | Default | `TUTOR_CONTEXTUAL_HINTS=1` |
|---|---|---|---|
| General question | `tutor` | 1 | 1 |
| Described mistake | `diagnose` | 1 | 1 |
| "practice" | `set_question` | 0 | 0 |
| "hint" on an active item | `tutor` | 0 | 1 |
| Wrong answer | `grade` | 0 | 1 |
| Question on an active item | `tutor` | 0 | 1 |

So "every tutor-route turn calls the model" holds only with `TUTOR_CONTEXTUAL_HINTS=1`, and the default is 0. [TEAM_ACTIONS.md](v3/TEAM_ACTIONS.md) reports 10 of 10 tutor-route turns making model calls in the pilot.

## Why not `create_agent`

- The spec keeps grading, keys, mastery, planning and permissions in code, so an agent could only choose among read tools and wording.
- An agent loop would add model decisions and calls per turn. Any benefit has not been measured.
- `langchain` is not a project dependency, and adding one was never approved.

## Gaps

1. The model never chooses a tool. Tool selection is code, so this is not agent behaviour.
2. The question setter makes no model call. An intro line was tried and dropped, because three tests expect no call on a practice turn.
3. Hint and wrong-answer turns reach the model only with `TUTOR_CONTEXTUAL_HINTS=1`.
4. `eval/configs/dev_live.toml` no longer runs: the harness now needs a `[provider_budget]` and template voice, so R3 has not run a live acceptance check. The nearest evidence is the Lead's v3 pilot on `a9ee2ba` with `contextual = true`: in the c2 arm, 5 of 5 tutor-route turns made model calls, with 0 errors and 0 detected full leaks. It did not exercise the `diagnose` route and predates PRs #4 and #5.

## Decisions for the Lead

1. Accept this as the equivalent for item 1, or ask for real agents?
2. Should `TUTOR_CONTEXTUAL_HINTS=1` become the default?
3. If real agents are wanted, the smallest step is the tutor alone, choosing between its two read tools.
