# Contributing

How we work in parallel without breaking `main`. The dates and what each role delivers are in the [lead roadmap](Docs/LEAD_ROADMAP.md).

## Set up

Follow **Install** in [Docs/poc/README.md](Docs/poc/README.md), then check that `pytest -q` shows 25 passed.

## Branches and pull requests

1. **`main` is protected.** It must always install and pass its tests. Nobody pushes to it directly.
2. **One branch per task**, named `r<role>/<topic>`, for example `r2/hybrid-retrieval` or `r6/compose`. Branch from the latest `main`.
3. **Push every day.** Open a draft pull request early so others can see the work.
4. **Every pull request needs one review from someone in another role**, and CI must pass. Use squash merge.
5. **Keep pull requests small** (under about 400 changed lines) and merge often. A long-lived branch turns into a painful merge.
6. **Change files you own.** If you need a change in someone else's file, ask them or tag them as reviewer. Owners: [who owns which file](Docs/LEAD_ROADMAP.md#who-owns-which-file).

## Every day

- **Contribution log:** add an entry to [Docs/CONTRIBUTIONS.md](Docs/CONTRIBUTIONS.md) with:
  - the date and your role;
  - what you did, with links to your pull requests;
  - **what was AI-assisted**;
  - any decisions.
- **Decisions:** anything that changes the plan goes in [Docs/DECISIONS.md](Docs/DECISIONS.md) the same day, with its evidence (a spike note or a `run_id`).

## Never commit

- `.env`, API keys or tokens. Copy `.env.example` and keep the key local.
- NCERT PDFs, page images or text taken from the textbook. Put PDFs in `data/ncert/`, which git ignores.
- The frozen dataset build, or held-out cases, students or queries (R5 holds them).
- Personal data of any real person.

## Separation rules

These decide whether our experiments count. They are in [07 · Team and roles](Docs/plan/07-team-and-roles.md#separation-rules).

- **R3** (who tunes the agents) never opens held-out cases or looks at held-out results before the freeze.
- **R4** (who builds the defences) does not see R5's new attacks before experiment E2.
- **R5's simulator** is written without reading the diagnosis rules in `src/tutor/mathcore.py`.

## AI coding tools

You may use them, but you must be able to explain, change and defend every line you merge. The viva is individual. Record AI-assisted work in the contribution log.

## `CODEOWNERS` (R6 sets it up)

Once the GitHub usernames are known, R6 adds `.github/CODEOWNERS` from the ownership table, for example:

```
/src/tutor/app.py           @<R3>
/src/tutor/mcp_servers/     @<R4>
/src/tutor/guards.py        @<R4>
/src/tutor_eval/            @<R5>
/eval/                      @<R5>
/src/socratic_data/         @<R5> @<R4>
```
