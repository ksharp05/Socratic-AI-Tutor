# Fresh v3 development results

6 November 2026. Two frozen builds each completed 360 fresh one-turn synthetic cases in stub mode: 720 sessions, zero tutor-provider calls. Baseline de36397; merged R3 candidate 8240ce3. No diagnosis changes were authored from these cases.

| Build | Hits / proposed incorrect claims | False labels / proposed no-error messages | Checked citations | Guard rejections / unexpected mastery |
| --- | --- | --- | --- | --- |
| before | 16/120 | 3/240 | 324 (0 errors) | 0 / 0 |
| merged | 19/120 | 6/240 | 318 (0 errors) | 0 / 0 |

Loading 30/30 catalogue types has not produced broad diagnosis accuracy. The merged build adds three target hits and three false labels on proposed labels. This does not establish product quality or learning. R3 owns diagnosis changes. Citation identity/hash/chapter checks do not establish semantic faithfulness.

GPT-6-Luna authored the cases; Gemini reviewed shuffled opaque IDs and messages with the public chapter catalogue, without target labels, generator rationales or tutor outputs. There are 347 label agreements, 6 disagreements and 7 uncertain/unusable rows (1 invalid quote, 6 ambiguous). The first review job stopped at the invalid quote; the continuation sent only untouched groups. No received request was repeated.

| Build | Hits / AI-agreed incorrect claims | False labels / AI-agreed no-error messages |
| --- | --- | --- |
| before | 16/116 | 3/231 |
| merged | 19/116 | 6/231 |

Two-model agreement is a development screen, not ground truth. This subset excludes disputed cases and may be easier; full proposed-label results remain visible. Human reviews remain zero. No learning, C2 advantage, independent-final or teaching-approval claim is supported.

Product-phase provider-reported spend: USD 0.0732038; accounted spend: USD 0.1232978, including the conservative reservation for an earlier failed request with unknown actual billing. Total historical/current provider attempts: 1158. The USD 10 ceiling remains enforced. All five original wallets are byte-identical; unused caps were released and no paid job remains scheduled.

Reproduce without network calls: scripts/product_quality/report_v3_fresh_cases.py --check. Raw cases, responses, databases and wallets stay under ignored Directions; only aggregate reports and source are published. See [DATA_SUFFICIENCY.md](DATA_SUFFICIENCY.md) and [TOOLS_HANDOFF.md](TOOLS_HANDOFF.md).
