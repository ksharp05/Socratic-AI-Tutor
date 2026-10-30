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
