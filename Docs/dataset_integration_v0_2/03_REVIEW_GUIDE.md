# Human review and promotion guide

Start with `03_REVIEW_QUEUE.csv`: 29 active seed misconceptions times four paths, selecting the first variant for each. There are exactly 116 source-bound rows; all decisions and rubric scores are blank. Review extra shape outliers from `evidence/dialogue_outliers.json` separately. One reviewed example never approves a whole template family.

Two distinct registered people, one qualified for subject review and one for pedagogy, must inspect the full source dialogue by ID. Check public givens, the learner's actual work, the proposed move and all later turns. Private references stay in the verifier/review process; do not copy them into generation prompts, learner exports or logs. The queue shows learner error text and candidate-move metadata, not private reference answers.

Score each 0, 1 or 2: mathematical correctness; misconception diagnosis; actionable scaffolding; clarity/tone; answer protection; context fidelity. The proposed promotion rule is math=2, answer protection=2, context=2, and the other dimensions at least 1, with all accepted teaching rules satisfied. R1/R2/R4 must ratify the rule; machine checks do not ratify it.

Use `approve`, `revise` or `reject`, with reviewer identities, zoned timestamp, comments and revision hash. An approval must bind the exact active policy content with `policy_sha256` as well as its policy ID. A revised record is new content and needs review of that exact revision. T08 cannot be promoted through this workflow. Neither critic-only records nor invented AI approvals qualify.

The code validates declared review evidence and registry membership; it is not a human-identity authentication service. The registry and active policy must be maintained by authorized owners, outside learner control. Defaults are unratified with an empty registry, so promotion fails closed. Unit-test people and approvals are explicitly authored fixtures and are not project approvals.

The active policy must contain explicit `thresholds` for all six rubric fields, ratification evidence and an owner. The pending policy only records proposed thresholds; start a new owner-maintained policy from `review_templates/active_policy.template.json`. The code supports the stated minimum thresholds or stricter values up to 2. Weaker rules need an explicit implementation/policy change, not a silent policy-ID reuse.

`promotion.py` performs copy-on-write projection. It writes the runtime's `examples.jsonl` and `MANIFEST.json` separately from `<destination>.review_evidence/review_ledger.json`. The private ledger preserves the reviewed revision, source attribution, parent/revision hashes, reviewer roles/identities, actual date, scores and exact ratified policy. The runtime manifest binds the review-record hashes; it does not contain identities or scores. Protect the ledger with staff-only filesystem/access controls; physical separation does not install permissions automatically.

Both versioned outputs reject conflicting overwrites and partial/unknown contents. Identical re-publication is idempotent. The runtime projection is bounded to 2 MB, with 2 to 40 alternating messages per example and bounded tutor turns. Nothing writes into the source snapshot. The runtime reads only a strict projection pinned by an administrator-held manifest hash and policy ID. It receives no reviewer identities, private reference fields or rejected responses. Only the first reviewed student/probe exchange is eligible as a prompt example; later corrected answers are not passed into the prompt.

## Independent intent annotation

`review_views/rater_A.csv` and `rater_B.csv` each contain 480 tasks with opaque IDs and context. They omit candidate intent/route labels. Raters work separately, then an adjudicator preserves original labels, disagreements and the decision. Do not prefill missing human labels using an LLM. CSV cells starting with spreadsheet formula markers are escaped for display; the exact original wording remains in the source record.

At 8 to 12 minutes each, 116 dialogue reviews require approximately 15.5 to 23.2 person-hours per complete pass, excluding editing, second review and adjudication. If capacity permits only 58 balanced reviews, disclose reduced coverage. Never fill the remaining scores automatically.
