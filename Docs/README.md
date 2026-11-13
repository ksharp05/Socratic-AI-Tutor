# Docs: where to find things

The latest version of each document lives here. Earlier milestone notes, superseded results and drafts were removed on 14 Nov 2026; every one of them is still readable at the tag [`docs-archive-2026-11-14`](https://github.com/ksharp05/Socratic-AI-Tutor/tree/docs-archive-2026-11-14/Docs), and links to them point there.

## Start here
| Need | Read |
|---|---|
| What we built and how well it works | [report/EVALUATION_REPORT.md](report/EVALUATION_REPORT.md) |
| How it is put together | [report/ARCHITECTURE.md](report/ARCHITECTURE.md) |
| Where the project stands today | [m3/CHECKPOINT.md](m3/CHECKPOINT.md) (top section) |
| Who does what next | [m3/TEAM_ROLE_PLAN_2026-11-13.md](m3/TEAM_ROLE_PLAN_2026-11-13.md) |
| Install and run | [SETUP.md](SETUP.md), [INSTALL_CHECKLIST.md](INSTALL_CHECKLIST.md), [RUN_GUIDE.md](RUN_GUIDE.md) |

## Living logs (add to these, never rewrite them)
| File | What it records |
|---|---|
| [DECISIONS.md](DECISIONS.md) | Every decision, with evidence and who made it (D-1 to D-9) |
| [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) | Every evaluation run and freeze, with hashes |
| [CONTRIBUTIONS.md](CONTRIBUTIONS.md) | Who did what each day, and where AI tools helped |

## By topic
| Folder or file | What it holds |
|---|---|
| [report/](report/) | The submitted evaluation report, architecture, Hinglish screening results, latency review |
| [policy/](policy/) | Teaching policy and scenarios, safe-messaging audit, DPDP readiness |
| [THREAT_MODEL.md](THREAT_MODEL.md), [MEMORY_POLICY.md](MEMORY_POLICY.md) | Security threat model (v3) and learner-memory policy |
| [testing/](testing/) | The independent public test set |
| [deploy/](deploy/) | Live beta on Vercel, key guide, leak alert evidence |
| [beta/](beta/) | Browser beta guide and the development results the app shows (`EVALUATION_RESULTS.json` is read by the app) |
| [m3/](m3/) | Current work: checkpoint, team plan, decision briefs, reviews (F2, C2, PRs) |
| [m4/](m4/) | Experiment E1–E4 results cited by the report |
| [m2/](m2/) | The three Milestone 2 evidence files the report cites |
| [releases/](releases/) | Release notes (v1.0 on 12 Nov) |
| [datasets/](datasets/) | Dataset report and NCERT catalogue |
| [plan/](plan/) | The original design plan (24 Oct); code comments cite it |
| [spikes/](spikes/) | Spikes S3, S4 and S6, cited by decisions |
| [demo/](demo/) | Demo script for the viva |
| [LEAD_ROADMAP.md](LEAD_ROADMAP.md) | Team table and the original roadmap |

## Rules for new docs
- Put a new review or note in the folder for its topic, or in `m3/` for current work. Do not start a new milestone folder.
- When a document is superseded, delete it in the same PR as its replacement, and point any link at its last commit.
- Never commit keys, NCERT PDFs or page images, course material, held-out data or personal data.
