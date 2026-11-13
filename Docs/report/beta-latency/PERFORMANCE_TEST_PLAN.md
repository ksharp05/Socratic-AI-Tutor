# Beta performance validation plan

## Starting point

The local Beta path already saves a cited turn and its observation in one transaction. A second experiment compared four configurations using two serial runs of the same 100 synthetic queries per configuration. All response fields matched except the measured latency. The corpus word-set cache is in the local Beta checkout. The idle SQLite connection was tested in the benchmark harness.

| Configuration | Request p95 | Retrieval p95 | Mean progress write time |
|---|---:|---:|---:|
| Combined write transaction | 15.95 ms | 2.85 ms | 7.69 ms |
| With source word-set cache | 15.18 ms | 1.93 ms | 8.63 ms |
| With idle SQLite connection | 12.89 ms | 2.67 ms | 2.24 ms |
| With both | 11.94 ms | 1.87 ms | 2.06 ms |

The p95 values above are the median of the two run-level p95 values. The tests used local SQLite and offline source replies. Hosted PostgreSQL and provider latency need their own measurements.

## Work sequence

| Order | Workstream | Lead responsibility | Deliverable |
|---|---|---|---|
| 1 | Benchmark and trace audit | R5 with a measurement subagent | Paired workloads, correct span accounting, raw receipts and repeatable commands |
| 2 | Retrieval and cache | R2 with a retrieval subagent | Result-parity tests, cold and warm latency, cache size and hit-rate measurements |
| 3 | SQLite and persistence | R6 with a persistence subagent | Lifecycle, contention, crash recovery and data deletion evidence |
| 4 | Hosted request path | R6 and R3 with an independent trace reviewer | A hosted waterfall that separates network, storage, provider calls and reply validation |
| 5 | Product and safety review | R1 and R5, with R4 for safety changes | A decision for each candidate tied to measurements and any known regressions |

### 1. Reproduce the benchmark

1. Record the commit, working diff, Python and database versions, source bundle hash, query-file hash, storage location and machine load. Capture the exact candidate configuration for each run. Use fresh synthetic profiles with the same seeded state.
2. Use the published 100-query workload for regression comparisons. Add a separate workload with paraphrases, repeated and unique topics, spelling variations, Hindi and Hinglish, and no-source queries. Include first turns, topic switches, follow-ups and sessions near the 500-turn limit. Keep the original 100 cases fixed.
3. Run the four configurations above as separate processes. Start with six 100-query runs per configuration, rotating their order across repeat blocks. Keep serial timing runs on one machine with no competing benchmarks. Record cold first-request timings separately from the standard warmed run.
4. Collect p50 and p95 by route and by stage, throughput, error rate, citations and reply fingerprints. Use at least 1,000 comparable requests when p99 is a decision metric. Report variability across runs and paired request differences. A run with a large outlier stays in the evidence, with any known cause recorded.
5. Add a load pass with 1, 4 and 16 clients. Test independent profiles and same-profile contention separately. Record lock wait, errors, throughput and p95. Count provider calls and committed writes on retries. Keep browser-visible turnaround, HTTP round trip and internal spans on their respective clocks.

From the Beta repository root, with the project environment installed:

```bash
python Docs/report/beta-latency/benchmark.py --out ./beta-latency-baseline-01
python -m pytest -q tests_beta/test_topic_navigation.py tests_beta/test_reference_notes.py tests_beta/test_pipeline_fixes.py
python -m pytest -q tests_beta
```

Use a fresh output directory per run. The benchmark runner handles the normal local route. For the idle connection comparison, use the experimental harness recorded with the previous benchmark receipts or a versioned reproduction of that harness. Run the existing PostgreSQL suite with `BETA_TEST_POSTGRES_DSN` pointed at a disposable test database.

### 2. Qualify the retrieval cache

- Compare exact response fields other than elapsed time. Compare ordered citation IDs, retrieval scores and scope against the uncached ranker. Include foundational definitions, supplemental notes, misspellings and cross-chapter boundaries.
- Test source and reference bundle changes, a cold process, warm repeated queries and unique queries after the cache fills. Confirm eviction remains bounded and check cache hits, misses and memory under load. Cache keys should come from source text and its metadata.
- Use the measured 32% retrieval p95 reduction as a hypothesis. A proposed target is at least 20% lower warmed retrieval p95 across repeated runs, with equivalent ranking and no meaningful end-to-end or cold-start regression. R1 can set the acceptable latency and memory margins before reviewing the full results.

### 3. Qualify the idle SQLite connection and combined writes

- Compare idle connection on and off with the same cache setting. Measure connection open, SQL execution, commit and close independently. Track WAL size over a long run with periodic idle periods and concurrent readers and writers.
- Exercise startup and shutdown in standalone and mounted API configurations. Cover repeated starts, abnormal exit, restart, contention and file access after shutdown. Verify that the idle connection has no active read transaction and that ordinary durable commits and checkpoints still complete.
- Seed synthetic progress, then exercise Forget my data before and after restart and during concurrent activity. Check application-visible data, WAL behavior and the applicable retention policy. Use synthetic marker data to check whether the change extends retention in database sidecar files. Cover multiple profiles and verify the other profile survives.
- Inject failure between the turn write and the observation write. Verify rollback of the turn, observation and session state. Retry the same request and verify exactly one committed turn and observation. Check older request replay and the session limit. Run the persistence checks against SQLite and the disposable PostgreSQL fixture.
- A proposed target is at least 10% lower local request p95 in repeated runs, with no loss of durability or unacceptable WAL growth or deletion behavior. Keep the idle connection as an experiment if lifecycle or retention evidence is incomplete.

### 4. Locate the hosted bottleneck

Capture spans for ingress, profile and session locks, PostgreSQL connection and queries, retrieval, each provider call, response validation and any repair, persistence commit, and response transmission. Record a request ID, route, model, provider-call count, cache outcome, elapsed time and fallback reason. Use synthetic prompts and metadata suitable for the existing observability policy.

Compare accepted model replies, deterministic replies and provider fallbacks as separate cohorts, with cold and warm requests identified. Run a small trace verification batch first, then the fixed workload against a suitable hosted test deployment within its existing model budget. Record the deployment revision, network vantage point, request counts, errors and provider usage. Check that the recorded stage durations reconcile to total request time. Use hosted evidence to decide whether the next change belongs to persistence, retrieval, the provider, or the browser.

## How to use subagents each cycle

- **Measurement agent** owns the workload, trace checker and serial benchmark schedule. It reports the size of the gain, spread across runs and exact commands. It reviews candidate comparisons without changing the component under test.
- **Retrieval agent** proposes one change at a time and supplies a minimal diff, expected effect and ranking invariants. **Persistence agent** does the same for transactions, connections and locks. They can investigate in parallel using the same frozen traces. Use separate worktrees for independent edits and merge only candidates the coordinator has reviewed.
- **Verification agent** checks failure cases and looks for regressions the implementer might miss. R5 retains the held-out evaluation cases. Agents working on component changes receive development cases and aggregate held-out results.
- **Coordinator** owns integration, serial timing runs and the decision log. Each agent returns the hypothesis, code location, verification command, evidence, limitations and recommended decision. The coordinator integrates changes one at a time, then tests the combined configuration for interactions.

Start with a measurement agent and two component agents. Use the verification role for a focused review before accepting a persistence or safety change. Time-box each investigation to one measurable hypothesis, then use the evidence to choose the next one.

## Runtime subagent experiment

Once hosted traces identify independent work on the critical path, test parallel execution of that work in the existing request flow. Use the current single route as the control. A plausible experiment is parallelizing independent read-only retrieval tasks when they need distinct sources, then joining both results before one tutor reply. If a specialist model agent is proposed, measure it as a separate arm and record its extra calls, tokens, costs, timeouts and fallbacks.

Use the same input and response requirements for both arms. Accept added runtime coordination only if it improves the measured target or yields a quality gain that R1 considers worth its latency and cost. Include cancellation, partial failures and citation ordering. The engineering subagents can keep identifying and testing improvements while the tutor request path remains an explicit benchmark decision.

## Review packet

Publish a short decision for each candidate with the before/after table, workload counts, paired trace links, relevant regression results and next owner. Include both the typical query waterfall and the slowest representative trace. Label results by environment. Record any skipped PostgreSQL checks, missing deletion evidence or unmeasured hosted stages with the action needed to resolve them.

## Tool-assisted hint quality test

The 32-case triangle pilot measured hint-category selection. The direct checker matched 24/24 structured cases and 3/8 natural-wording cases. It asked for clarification on five natural-wording cases that were checkable. The model selected the optional tool zero times. Use those cases for development and exercise the actual learner-visible replies in the next run.

### Freeze the comparison

| Route | What it tests |
|---|---|
| Current Beta | The existing response on the same registered exercise and learner turn |
| Direct checker | Application code calls the existing checker once for eligible practice. It uses a bounded hint for a clear result and a focused clarification for an ambiguous result |
| Direct checker with one tuning change | Add the smallest measured improvement to parsing or hint selection. Evaluate one change at a time |
| Model-selected tool, exploratory | Measure whether the model chooses the tool at the right time and calls it with valid arguments. Record outcomes and latency separately if this route is tested |

Use identical approved exercise IDs, learner wording, prior context, and mode in each arm. Preserve the current quiz isolation, source scope, and answer-checking policy. When a route uses a model, keep its version and settings fixed across comparable arms. Pin the checkout and exact prompt or hint templates. Bind exercise identity and learner input on the server. The tool should return a diagnosis category without the numerical answer.

### Cases and labels

Start with 24 smoke cases from development to verify the integration and trace fields. Use a development set of at least 80 cases, including the original pilot, to diagnose failures and tune one change at a time. R5 then holds a fresh, frozen set of 320 paired cases:

| Cohort | Cases | Coverage |
|---|---:|---|
| Structured practice | 80 | Correct side labels, swapped sides, wrong reference angle, wrong ratio order |
| Checkable free-form practice | 160 | English, Hindi, Roman Hinglish and mixed-script wording, with units, paraphrases and reordered labels |
| Ambiguous practice | 40 | Missing angle, contradictory labels, unclear references and partial work |
| Out-of-scope controls | 40 | Quiz isolation, revoked or absent exercise, open chat, unrelated tutoring and existing safety routes |

Balance language and error categories within the applicable cohorts. Use different exercise families and independently written wording in development and holdout so paraphrases of the same case do not cross the split. Record the expected next teaching move and acceptable alternatives before running either route. Keep ambiguous cases marked as such. Have two reviewers score the actual replies independently, blind to route and with randomized presentation. Calibrate the rubric on development examples, record agreement, and adjudicate disagreements before computing final scores.

### Measure quality and cost

- **Primary quality metric.** Share of checkable practice cases where the actual reply addresses the learner's specific mistake or confirms the intended reasoning move and asks one useful next question. Score supported facts and citations when used, language fit, and whether the hint preserves the learner's work.
- **Clarification and coverage.** Report correct hints among all checkable turns, correct hints among answered turns, unnecessary clarifications among checkable turns, and appropriate clarifications among ambiguous turns. Count malformed replies, timeouts and empty responses in the workload denominator.
- **Policy checks.** Count final-answer leaks, incorrect math assertions, tool execution in an ineligible mode, wrong-exercise use, and unauthorized changes to grade or mastery. Check missing or revoked exercises, retries, and tool failure. Report each failure by case ID and category.
- **Timing.** Report learner-visible request p50 and p95, with spans for lookup, checker, reply selection or generation, validation, and persistence. Record model calls, tool calls, tokens, and fallback reasons. Use the fixed serial latency runner for timing and report isolated tool duration separately.
- **Uncertainty.** Report paired wins, losses and ties, per-cohort denominators, reviewer agreement and 95% confidence intervals. Resample by exercise family or conversation to account for related cases. Use a separate pilot pass to estimate how much evidence is needed for a reliable decision on a small effect.

### Tune, confirm, and hand off

1. After each development run, rank errors by frequency and impact. For example, a checker that abstains on clear units needs a narrow parsing fix. A correct diagnosis with a vague hint needs a hint-template change. Rerun the same development cases plus a regression case for the specific fix.
2. Freeze one candidate before opening the holdout. Proposed review targets are a **10 percentage point gain** on checkable free-form hints, **zero observed answer leaks or ineligible tool calls**, and **no more than 10 ms added local p95**. Confirm a paired improvement with its interval and examine each language subgroup before deciding. A wide interval or sparse subgroup warrants more independent cases. Zero observed failures describes this sample.
3. Give the measurement agent the paired harness, receipt schema and timing. Give the retrieval or tutoring agent one parser or hint change at a time. Give an independent verification agent the policy and failure tests. R5 owns held-out access, R1 owns the hint rubric, and the coordinator integrates candidates and runs timings serially.
4. Deliver a scorecard by route and cohort, reviewer notes for disagreements, request waterfalls for typical and slow cases, and a short decision with the next owner. Further tuning after viewing the holdout uses a new confirmation set.
