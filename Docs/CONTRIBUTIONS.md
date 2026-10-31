# Contribution log

Every member adds an entry for each day they work, newest first. The course guide asks us to show who did what and where AI tools were used.

**Format:**

```
### YYYY-MM-DD · <name> (<role>)
- **Work:** what you did, with PR links
- **AI-assisted:** which parts, and which tool
- **Decisions:** any, with a link to Docs/DECISIONS.md
```

---

### 2026-10-31 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:**
  - Merged the proof of concept, roadmap and live-model setup into `main`.
  - Updated the [lead roadmap](LEAD_ROADMAP.md): team names, what we found on 31 Oct (the NCERT files and the course keys), re-dated milestones, and an R5b role for the sixth member.
  - Recorded the role names as [D-2](DECISIONS.md).
  - Wrote the [R1 and R5 work plan](roles/R1_R5_WORK_PLAN.md): deliverables by day, hand-offs, inputs needed, decisions for the meeting and outside research. Fixed the vendored kernel's line endings so its hashes match, and git-ignored `eval/private/`.
  - Set up live model access with the course keys: a `.env` template; `tutor check-llm`, which tests a key against one model or every course model; a warning, and an eval report count, when a live call fails and a template is used; the course model list in `config/app.toml`; 5 tests using a local fake server.
- **AI-assisted:** code, tests and docs written with Claude Code, then reviewed and tested.
- **Decisions:**
  - [D-2](DECISIONS.md): role names, proposed in the group; confirmed at the 1 Nov meeting.
  - Open questions added to [DECISIONS.md](DECISIONS.md#still-open): the plan models the course keys don't reach, whether one key may be a GitHub secret, and D-3 and D-4 for the meeting.

### 2026-10-30 · ksharp05 (Lead, R1, R5)
- **Work:** pushed the proof of concept to branch `poc/walking-skeleton`; wrote the [lead roadmap](LEAD_ROADMAP.md), the contributing guide and the pull request template; added the tutor-visible dataset content.
- **AI-assisted:** written with Claude Code, then reviewed and tested.
- **Decisions:**
  - [D-1](DECISIONS.md): takes R1 and R5 alongside Lead, with hand-offs for the separation rules.
  - Proposes running the rest of Phase 1 from the POC (open decision Q9).

### 2026-10-24 · ksharp05 (Lead)
- **Work:**
  - Wrote the proposed project plan ([Docs/plan](plan/README.md)) and updated it to use faculty-provided API keys.
  - Built proof of concept v0: the session and approval graphs, four MCP servers with hooks, guardrails, learner model, a simulated-student smoke test and 25 tests ([Docs/poc](poc/README.md)).
- **AI-assisted:** research, code and documents written with Claude Code, then reviewed and tested.
- **Decisions:** none. The plan remains proposed.
