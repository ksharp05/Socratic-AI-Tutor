# Versioned simulator scope and canonical messages

public-practice-protocol-v2 is an opt-in formatting adapter and preflight. It does not change the legacy Student, frozen run_session, misconception rules, random choices, mastery updates or clearing probabilities. Existing harness defaults and historical reports are unchanged. A future C1/C2 comparison must explicitly select and record its protocol; no new study result is claimed here.

## What the audit established

The dataset solver and separate reference checker already agree on exact answers for all 331 public practice items across nine families. Canonical text compatibility is a separate check:

| Public practice preflight | Passed / total |
|---|---:|
| Exact mathematical reference support | 331 / 331 |
| Legacy message -> tutor parser -> same typed answer | 322 / 331 |
| V2 canonical message -> tutor parser -> same typed answer | 331 / 331 |

The nine legacy failures are empty AP counts rendered as “there is no such term”. V2 renders these as “no valid term count”; nonempty counts retain explicit term units. It preserves deliberately wrong values rather than correcting them. Other answer kinds keep legacy formatting.

A read-only audit of the already completed C2 baseline finds all 18 unchecked attempts use the legacy empty-count phrase and take the tutor route. They remain counted as unchecked in the original reports. This isolates the unchecked-attempt issue to this language path; it does not establish that all diagnosis/gain changes are caused by formatting.

## Product gap and R3 handoff

The learner phrase “there is no such term” still needs R3's input-language review. Canonical simulator wording is not evidence that the product handles that natural paraphrase. No runtime parser/router change was made here.

The new protocol has an actual synthetic TutorApp test showing its canonical empty count reaches deterministic grading, without quiz scoring. It also tests identical typed answers and RNG state across 30 old/new Student decisions. The fixture's publication actor is explicitly an automated test, never a human review record.

336 focused tests pass. Mathematical/formatting support does not establish misconception-rule coverage, free-form language coverage, multi-turn reliability or learner validity. Those require separate trajectories and review. No teacher/independent-author review is inferred.

## Reproduce without altering history

The no-network script scripts/product_quality/audit_simulator_protocol.py creates a new directory only and refuses an existing output. Store raw outputs under ignored Directions or var. The recorded completed run and source hashes are under Directions/product_quality/v3/simulator_scope_01/audit_01; SIMULATOR_SCOPE.json contains safe aggregates and the exact public-input manifest hash.

No private cards, held-out tasks or provider requests were used for the public preflight. The cached audit reads old turn outcomes only; it does not tune R3 rules or rewrite old results. Keep the legacy empty-count behavior/version visible when comparing future protocols.
