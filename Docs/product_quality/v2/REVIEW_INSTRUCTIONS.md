# Review instructions — actual human review pending

These are public development fixtures authored by the assistant. They are not held-out final evaluation, and the A/B presentation does not make them independent. The private source-version mapping is retained under Directions/product_quality/v2/PAIR_KEY.json.

Review `SOURCE_REVIEW.jsonl` first: check each definition against the stated original PDF, printed/PDF page and source grade; inspect the follow-up question for mathematical correctness and learner usefulness. Leave a reviewer identifier, date, explicit judgments and reasons. Blank fields are intentional. Do not infer approval from a matching source hash or the assistant's page inspection.

Then review `PAIRED_REVIEW.jsonl`: read each whole journey and both responses; mark source faithfulness, mathematics, helpfulness and safety for A/B, plus preference and concrete notes. Consider whether the reply answers the actual question, asks a useful next question, preserves quiz/privacy boundaries, and avoids awarding mastery without checked work. Do not treat the mechanical test's pass as a semantic judgment.

Use two actual independent raters for agreement analysis; reconcile differences separately and retain both original ratings. One person with two project roles is one rater. Supply independently authored final content separately; these development forms cannot substitute for it.

No form publishes a lesson or question set, confirms R3/R2 approval, or changes the tutor's reference metadata automatically. Changes need a new reviewed candidate, qualified source lock and version-bound publication decision. No ratings have been entered by the assistant.
