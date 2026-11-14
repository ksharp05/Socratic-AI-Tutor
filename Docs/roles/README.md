# Role handover notes (viva, 15 November 2026)

The guide assigns six roles. Each role owns part of the architecture, and in the viva each person is asked about their own part. On this team, the Lead (with Claude Code) built much of the work that sits in other people's role areas. These notes hand that work over, so that each person can explain everything in their area, whoever built it.

**How to read them.** Each note has six parts:
1. what the guide asks of the role;
2. what exists in the repository for that area;
3. who built each piece, taken from `git log` authors and `Docs/CONTRIBUTIONS.md`;
4. how it works, in a few lines;
5. likely viva questions, with short answers;
6. the files to have open.

**Honesty rule.** These notes do not change who did the work. If an examiner asks who built something, give the answer in the "Who built it" table. Saying "the Lead built it, and I reviewed and can explain it" is a good answer. Claiming someone else's work is not. Where the record is thin, the note says "confirm with <name>".

| Role | Person | Note |
|---|---|---|
| R1 Domain and product lead | Lakshya (Lead) | [R1_DOMAIN_PRODUCT.md](R1_DOMAIN_PRODUCT.md) |
| R2 Knowledge and memory | Rizwan Farooq | [R2_KNOWLEDGE_MEMORY.md](R2_KNOWLEDGE_MEMORY.md) |
| R3 Agents and orchestration | Poonam Prajapati | [R3_AGENTS_ORCHESTRATION.md](R3_AGENTS_ORCHESTRATION.md) |
| R4 Tools, control and security | Swati Smita Biswal | [R4_TOOLS_CONTROL_SECURITY.md](R4_TOOLS_CONTROL_SECURITY.md) |
| R5 Evaluation and red team | Lakshya (Lead); Shivam Srivastava proposed as R5b | [R5_EVALUATION_REDTEAM.md](R5_EVALUATION_REDTEAM.md) |
| R6 Deployment and operations | Sharath S Nadig (from 13 Nov); Poonam stood in on 11 Nov | [R6_DEPLOYMENT_OPERATIONS.md](R6_DEPLOYMENT_OPERATIONS.md) |

**Commit counts (all branches, 14 Nov):**
- ksharp05 (Lead): 204
- Poonam: 30
- Swati: 19
- Rizwan: 1

Several teammates' changes arrived through PRs that the Lead merged. Commit counts therefore understate their work, and the contribution log is the better record.

**Everyone should be able to:**
- redraw the architecture from memory (`Docs/report/ARCHITECTURE.md`);
- trace the `walk-1` request through it;
- say which decisions code, the model and a person make.
