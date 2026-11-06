# Approved PR integration

6 November 2026. The user requested merging the previously parked #1 and the newer R3 PRs. All four were reviewed together before merging: the combined tree passed 1069 regressions. GitHub confirms each PR is merged and closed. The resulting Beta tree matches the tested combined tree; the #1 documentation merge on milestone-2 also passed remote CI.

| PR | Contribution | Remaining limit |
| --- | --- | --- |
| [#1](https://github.com/ksharp05/Socratic-AI-Tutor/pull/1) | Supervisor-model decision proposal | Provisional documentation; no production model switch or live acceptance implied. |
| [#4](https://github.com/ksharp05/Socratic-AI-Tutor/pull/4) | After-last-hint revisit/fallback handling | Parallel-example tool and persistent-memory integration remain with R3. |
| [#5](https://github.com/ksharp05/Socratic-AI-Tutor/pull/5) | Catalogue loading reaches 30/30 and adds quadratic rules | Loading coverage does not establish detection accuracy or generalization; R2 review remains open. |
| [#6](https://github.com/ksharp05/Socratic-AI-Tutor/pull/6) | Specialist-equivalent design write-up | A proposal, with fake-model checks clearly marked; Lead acceptance and real tool selection remain open. |

Integrated Beta revision: `8240ce3151af76a1ab08ae58ca16ed6d4fd76903`. Exact tree: `d812b72a180cf133d62a320b7fde586782f45855`. The user asked the assistant to focus on the other final-product areas while the R3 contributor continues R3. See [TOOLS_HANDOFF.md](TOOLS_HANDOFF.md) for the R2/R4 services prepared for that integration.

Beta is published on GitHub. Private datasets, API keys, local databases and raw experiment logs remain excluded. Deployment is deferred at the user's request; the earlier Vercel preview is saved locally in stash `9cf6a27f25999be536d61eea665bc440bb9ab019` and is not deployed.
