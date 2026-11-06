# Boundary-preserving parallel examples

The service is now parallel-example-v3. It retains declared mathematical cases while checking a different answer, disjoint quadratic roots, exact proof/presentation binding and the existing active-answer guard. It invokes the separately implemented published-maths oracle as an enforced gate, in addition to the existing two calculation routes. R3 learner-route integration is still pending.

## Public practice coverage

| Family | Checked examples available | Safe fallback |
|---|---:|---:|
| Quadratic roots | 9 / 11 | 2 |
| AP count | 28 / 40 | 12 |
| AP first term | 39 / 40 | 1 |
| AP difference, ledger, mean, sum, term and triangle ratios | 240 / 240 | 0 |
| Total | 316 / 331 | 15 |

The 15 fallbacks are deliberate. Preserving no-real or zero-root cases would share the active empty set or a root; an invalid/one-term AP count or zero first term also fixes the answer. These cases return unavailable without a proof or key. The existing last-hint fallback remains the controller's responsibility.

V2 could provide examples for all 331 items because it did not preserve these cases. Do not compare that availability number without its different contract.

## Declared cases

Quadratics preserve discriminant class, rational/irrational roots, leading sign/unit magnitude, a missing linear term, zero-root status and root-sign pattern. Repeated rational roots use a repeated-factor explanation with one distinct value; irrational roots use the signed quadratic formula.

AP examples preserve direction, zero/sign cases and first-position conditions. Difference tasks retain index ordering, adjacency, inclusion of the first position, known-value signs and fractional/integral difference. Counts preserve valid-count/first-position conditions; means retain endpoint order, signs and integrality; ledgers retain prefix/increment signs. Triangles retain the ratio, reference angle and leg ordering.

This is the explicit parallel-cases-v1 signature, not every possible mathematical property, matched difficulty or assessment equivalence. Number sizes and wording differ. Teaching quality remains unreviewed.

## Qualification

387 focused service/case/tool tests pass. The final four-suite and CI results are recorded in BOUNDARY_EXAMPLES.json and the current checkpoint.

A seeded audit covers 900 distinct valid synthetic inputs, 100 per family. It returns 782 checked examples, 117 invariant-answer fallbacks and one bounded-search/guard fallback. Available examples have zero case mismatches, independent-answer failures or active-guard failures; all 782 appended-text mutations are rejected. Audit-row timing is median 3.492 ms, p95 282.611 ms, maximum 357.283 ms; this includes verification and corruption checks and is not hosted learner latency.

An initial reversed-index test exposed a fixed gap equal to the active answer. Candidate generation now varies nonadjacent gaps while preserving orientation, signs and fractional differences. The first failure, earlier audits, protocol, source hashes and final raw records remain privately preserved. No guard was weakened.

No provider calls, changed R3 routing, human approval, independent final evaluation or learning result. The new presentation/numbers must not inherit v2's AI clarity scores. See [reference validation](REFERENCE_VALIDATION.md), [R3 service contract](TOOLS_HANDOFF.md) and BOUNDARY_EXAMPLES.json.
