# New independent data acquisition plan

No external material was downloaded and no recruitment messages were sent. Current synthetic data is an engineering and review resource, not a substitute for human-authored teaching situations.

## Proposed new collection

- **60 new adult teacher-led role-play conversations:** 20 per chapter, distinct problems and teaching situations. Recruit consenting adults through the team; record consent scope, allowed reuse and deletion process. A teacher authors the teaching decisions; an adult learner voices their reasoning. Keep human, role-play and model-assisted origins explicit.
- **300 independently written contextual learner messages:** cover all 20 intents, including ambiguity, corrections, informal English and longer reasoning. Preserve needed prior context. Do not ask the author to paraphrase an existing synthetic row.
- **150 failure-driven multi-step contexts:** select after the first review pass. Prioritize mathematical reasoning, context repair, repeated failed hints and correct-but-unusual attempts. The source roadmap's 30 reasoning variants per chapter total only 90; explicitly allocate the other 60 as contextual recovery, cross-turn dependency or teacher-handoff situations. The 150 target is a proposal, not existing data.
- **New misconception evidence:** compare new explanations with the canonical catalogue. Record an unmatched observation instead of forcing it into the nearest numerical ID. Review genuine new rules before extending scope.
- **Final evaluation:** separate authors create 30 dialogues and 120 messages outside all tuning. These are different records from the 60/300 development collection. The runtime implementer must not author or inspect that private set.

## Source decisions before any acquisition

| Source | Current evidence | Action now | Gate before content import |
|---|---|---|---|
| MathDial | Supplied register flags repository/card licence conflict | Research metadata only | Pin exact artifact, hash and terms; resolve conflict and retain source partitions |
| MRBench | Register says CC BY-SA, with differing version dimensions | Rubric/evaluator methodology | Check exact release and obligations; detect overlap with MathDial/Bridge; keep official tests out of tuning |
| MathTutorBench | Register requires per-repository review | Research reference only | Verify exact task artifacts, licences and access conditions before acquisition |
| SocraticMATH | Register reports a noncommercial card; Chinese primary-school scope | Metadata reference only | Independently verify terms; do not bulk merge into English Class 10 data |
| NCERT | Official chapters already held locally | Checked references only | Subject owner verifies edition, page/section IDs, notation and permitted use; exclude answer appendices |

These are gated register entries, not a claim that every external licence was freshly verified. The optional MathDial script was not executed. Never interpret an acknowledgement flag as resolution of conflicting terms. Retain third-party material in a separate attributed store and never mirror copyrighted content into review reports by default.

## Collection ledger

Record source/participant pseudonym, adult-consent reference, authoring method, date, allowed uses, policy version, problem/context root, chapter, misconception, reviewer decisions, original/revision hashes and intended partition. Store identities and consent evidence separately from prompt-visible text. Remove personal data before model calls or shared logging.

R1 recruits and reviews pedagogy; R2 checks maths and source scope; R4 reviews consent/privacy controls; R5 commissions the separate final authors; R6 maintains hashes and access. No independent final authors or teacher reviewers have been assigned by this tool run.
