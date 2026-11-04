# Isolated quadratic development probe

`python scripts/m2/quadratic_probe.py` defaults to a **synthetic model and no network**. It creates an isolated local SQLite state folder under ignored `Directions/m2_candidate_runs/`, inserts one synthetic development-only quadratic item, obtains its source reference and exercises the existing graph, contextual hint adapter and answer guard. The fixture is explicitly labelled **not human approved**; it does not publish to the real question bank or demonstrate the teacher workflow.

The development problem is `x² = 5x`. The default fake-model run generated a source-ID-bearing question and recorded model/guard/tool decisions. It is a code-path check, not evidence that a real model was called, a citation's pedagogy was independently reviewed, or arbitrary homework is safe.

## Live call

The optional `--live` mode uses the configured model provider and sends a synthetic question, recent synthetic turns and one retrieved course-card excerpt, together with the tutor instructions, to that provider and potentially its downstream model host. The local environment was observed to select OpenRouter and `openai/gpt-4.1-mini`; confirm the configuration before running. No real learner record or API key is deliberately included in the prompt. A provider call may incur charges.

A wrapper permits at most one generation attempt. The probe verifies that both the model wrapper and its underlying synchronous client have retries disabled, sets a 22-second timeout and caps output at 240 tokens. If the configured SDK cannot verify that retry policy, the probe stops before making a request. An additional conservative display screen withholds hints containing digits or common number words outside source identifiers. This screen can reject safe hints and is not a complete semantic leak detector.

The program records `synthetic_model` versus `live`, counts provider calls separately from fake generations, and refuses to present a guarded fallback as an accepted model response. Local evidence contains a redacted event summary and code hashes. Human review, complete output-leak protection and the teacher/learner integrated UI flow remain separate work.

Automatic approval review rejected the original live probe because the proposed request could transmit local source passages without explicit authorization. The user explicitly approved one call on 4 November 2026; any further `--live` run needs fresh approval.

## Live result — 4 November 2026

Run `quadratic-f9459b4ad19e` on clean commit `c143b53` made **one provider call** to `openai/gpt-4.1-mini` through OpenRouter: 478 input and 22 output tokens, 1.9 seconds, no retries. The prompt carried the project's own one-sentence `normalized:qe03` card (roots verified by substitution), not a PDF transcription. The fixture lists qe03, qe04 and qe05; the adapter sends only the first. Monetary cost was not exposed and is not measured.

The saved tutor reply was:

> Which signed coefficients remain when every term is on one side of the equation [normalized:qe03]?

The buffered leak check and output guard both passed, and the generation was accepted. The trace records the model call, the textbook and leak-check tools and the guard decisions. The probe's extra display screen then **withheld** the hint because "on one side" contains the number word "one". The probe therefore exited as incomplete, as designed. The reply text was read from the local conversation checkpoint; its hash matches the trace's response hash.

Assistant observations, not human review: the reply asks one question, names the source before the question mark and states no root, factor or value. The cited card is about checking roots by substitution, while the question is about collecting terms on one side, so the citation is present but only loosely supports this step.

This is one sample from an isolated probe. It does not show the hint to a learner, exercise the integrated UI or the registered signature API path, or establish teaching quality. No rerun was made after seeing the result. [Projected evidence](QUADRATIC_LIVE_EVIDENCE.json); raw evidence stays in ignored `Directions/m2_candidate_runs/quadratic-f9459b4ad19e/`.


A later [integrated signature API path](SIGNATURE_API_PATH.md) supports the registered equation through normal teacher publication and an explicit contextual-adapter option. Its synthetic-only smoke command has no live mode. This older probe remains isolated and unapproved; its synthetic publication now includes explicit supporting reference IDs to match the active-question reference contract. Its one-attempt live budget and the API adapter's normal SDK retry policy are different. Only this isolated probe has a live-provider result; the signature API path has none.
