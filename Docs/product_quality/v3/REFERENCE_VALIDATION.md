# Separate exact mathematics validation

6 November 2026. This adds an offline beta-qualification tool, not a new learner route or a teacher approval.

## Scope and implementation

src/tutor_validation/exact_reference.py independently checks exact answers for the nine connected task families: quadratic roots, AP term/sum/first term/difference/count/mean/prefix-ledger term, and right-triangle ratios. It uses only the Python standard library and imports neither the runtime solver nor the dataset solver or SymPy.

The implementation uses repeated addition/subtraction for AP terms and sums, exact Fraction arithmetic for ratios/counts, and polynomial substitution plus completeness checks for real quadratic roots. A bounded expression parser accepts a small arithmetic/square-root language without executing input code. Invalid inputs fail closed; tasks outside the declared scope return unsupported.

Source definitions:
- [Quadratic equations](https://openstax.org/books/algebra-and-trigonometry-2e/pages/2-5-quadratic-equations)
- [Arithmetic sequences](https://openstax.org/books/algebra-and-trigonometry-2e/pages/13-2-arithmetic-sequences)
- [Arithmetic series](https://openstax.org/books/algebra-and-trigonometry-2e/pages/13-4-series-and-their-notations)
- [Right-triangle trigonometry](https://openstax.org/books/algebra-and-trigonometry-2e/pages/7-2-right-triangle-trigonometry)

OpenStax did not review or endorse this tutor. The checker is separately implemented by the same coding assistant, not independently authored final evaluation.

## Qualification

355 focused tests and all 1,789 full four-suite regressions pass locally. Every one of the 331 eligible public practice keys is accepted and one deliberately altered key per item is rejected. Additional independently specified cases cover every task family, negative progressions, distinct/repeated/non-real/irrational quadratic roots, invalid units/shapes, executable expressions, iteration limits and rational/expression resource bounds.

This is agreement on exact answers and known-error controls. It does not validate teaching steps, relevance, diagnosis, semantic faithfulness of citations or learning outcomes. The existing worked-example renderer still has its own checks; it has not been connected to this new checker and remains parallel-example-v2.

## Release direction

No teacher is available for this beta. Use published mathematical references, this second implementation, proof/presentation checks, permissions, regression controls and clearly reported AI-review limitations as the beta validation basis. Preserve all historical blank human-review records. Any beta publication policy must identify machine/reference validation explicitly; do not fill teacher-approved fields to bypass existing runtime gates. A labelled beta is distinct from formal M3/M4 acceptance or an independent efficacy study.

Next non-R3 work is boundary-case-preserving examples and explicitly versioned simulator task support. R3 owns graph integration of the existing example and revisit services. Deployment preparation now targets the user's chosen full beta with persistent learner progress. The saved stateless reference preview is not equivalent.

No new model calls, provider-budget changes, production routing or model switches were made for this checker.
