# Isolated quadratic development probe

`python scripts/m2/quadratic_probe.py` defaults to a **synthetic model and no network**. It creates an isolated local SQLite state folder under ignored `Directions/m2_candidate_runs/`, inserts one synthetic development-only quadratic item, obtains its source reference and exercises the existing graph, contextual hint adapter and answer guard. The fixture is explicitly labelled **not human approved**; it does not publish to the real question bank or demonstrate the teacher workflow.

The development problem is `x² = 5x`. The default fake-model run generated a source-ID-bearing question and recorded model/guard/tool decisions. It is a code-path check, not evidence that a real model was called, a citation's pedagogy was independently reviewed, or arbitrary homework is safe.

## Proposed live call — approval required

The optional `--live` mode has **not** been run. It uses the configured model provider and sends a synthetic question, recent synthetic turns and one retrieved course-card excerpt, together with the tutor instructions, to that provider and potentially its downstream model host. The local environment was observed to select OpenRouter and `openai/gpt-4.1-mini`; confirm the configuration before running. No real learner record or API key is deliberately included in the prompt. A provider call may incur charges.

A wrapper permits at most one generation attempt. The probe verifies that both the model wrapper and its underlying synchronous client have retries disabled, sets a 22-second timeout and caps output at 240 tokens. If the configured SDK cannot verify that retry policy, the probe stops before making a request. An additional conservative display screen withholds hints containing digits or common number words outside source identifiers. This screen can reject safe hints and is not a complete semantic leak detector.

The program records `synthetic_model` versus `live`, counts provider calls separately from fake generations, and refuses to present a guarded fallback as an accepted model response. Local evidence contains a redacted event summary and code hashes. Human review, complete output-leak protection and the teacher/learner integrated UI flow remain separate work.

Automatic approval review rejected the original live probe because the proposed request could transmit local source passages without explicit authorization. Do not run `--live` until the authorized user approves that specific data transfer.


A later [integrated signature API path](SIGNATURE_API_PATH.md) supports the registered equation through normal teacher publication and an explicit contextual-adapter option. Its synthetic-only smoke command has no live mode. This older probe remains isolated and unapproved; its synthetic publication now includes explicit supporting reference IDs to match the active-question reference contract. Its one-attempt live budget and the API adapter's normal SDK retry policy are different. Neither path has an authorized live-provider result.
