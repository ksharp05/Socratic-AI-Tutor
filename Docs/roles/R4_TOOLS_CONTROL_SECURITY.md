# R4 · Tools, control and security engineer · Swati Smita Biswal

**What the guide asks** (lectures L7, L14 and L15):
- at least three FastMCP servers with typed inputs and outputs and structured errors, each tool marked read or write, with one test per tool;
- `interrupt()` approval tied to the exact payload, with pre-tool and post-tool hooks;
- a one-page threat model, input and output guardrails, and least-privilege tools.

## What exists

| Piece | Where |
|---|---|
| Four FastMCP servers: `textbook-kb`, `math-tools`, `learner-store`, `question-bank` | `src/tutor/mcp_servers/` |
| ToolBus hooks: role allowlist, own learner only, 300 calls per session, scrubbed arguments in the trace | `src/tutor/toolbus.py` |
| Approval token: HMAC over the payload's SHA-256 and the teacher ID; any edit voids it | `src/tutor/approval_token.py` |
| Input and output guards: distress, injection, answer-key and role claims, PII; leak check and retrieved-only citations | `src/tutor/guards.py`, `src/tutor/mathcore.py` |
| Live-beta safety layer: normaliser, crisis, abuse and secrecy screens | `src/socrates_beta/safety.py` |
| **Threat model v1 to v3** | `Docs/THREAT_MODEL.md` |
| **Answer rules and leak-check fixes** (empty sets, "no such term", "does not exist") | `src/tutor/mathcore.py` |
| **Distress false-alarm fix** ("hopeless at maths") | `src/tutor/guards.py` |
| **S4 guard-model spike and D-6; D-7 classifier wired in, off and fail-closed** | `src/tutor/safety_classifier.py`, `Docs/DECISIONS.md` |
| **PR #28: wider crisis screens and injection pattern, from the public tuning pool** | `src/socrates_beta/safety.py`, `guards.py` |
| **A6: four app-security fixes, one test each** | `tests_beta/test_r4_security_fixes.py` |
| **Report section 2a** | Report |

## Who built it

| Built by | What |
|---|---|
| **Swati** (19 commits, 9–13 Nov) | Everything in bold above. |
| **Lakshya (Lead)**, with Claude Code | The four MCP servers (16 commits), ToolBus, the approval token, the original guards, the live-beta safety layer of 10 Nov and the 420-case security test. |

## How it works

- **Each tool has an owner.** The question setter can only `propose`, and `publish` sits behind the teacher's approval.
- **The hooks** check role and learner before each call, and log a scrubbed record after it.
- **Answer keys** are computed in `math-tools` and are never sent to the model.
- **Crisis messages** get a fixed reply with Tele-MANAS 14416 before any provider call.
- **The classifier** fails closed: if it can't decide, it blocks.

## Likely questions

- **Show an edit voiding an approval.** `try-publish` with the old token returns FORBIDDEN, because the hash no longer matches.
- **Did the defences work (E2)?** On 420 cases, safety failures went from 118 to 10, and false blocks from 14 to 2 of 52. It was graded by deterministic checks and two AI judges.
- **Why no Llama Guard?** It is not available on the course key, so the general models were compared instead (D-7).
- **What are the A6 fixes?** A 2 s wall-clock limit on the maths checker; no published `openapi.json`; 256 lock stripes; and curly-apostrophe secrecy promises now caught.

**Files to open:** `Docs/THREAT_MODEL.md`, `src/tutor/toolbus.py`, `src/tutor/approval_token.py`, `src/tutor/guards.py`, report section 2a.
