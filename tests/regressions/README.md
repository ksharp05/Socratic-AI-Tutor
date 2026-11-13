# Regression tests: every real failure becomes a test

This folder is the top of our testing pyramid (team plan, testing workstream, 14 Nov 2026). The rule:

1. **Within 24 hours** of finding a failure (a production incident, a review finding, a probe that slips past a
   screen, a teammate's bug report), add a test here that **fails on the current code**.
2. If the fix is not ready, mark the test `@pytest.mark.xfail(strict=True, reason="<finding id>: <one line>")`.
   Strict means the test turns red the day the bug is fixed, as a reminder to remove the mark.
3. The fix and the removal of the mark go in the same pull request.
4. Name each test after the finding (`test_f2_...`, `test_c2_2_...`, `test_as01_...`) and say in its docstring
   where the finding is written up.

What may go here:
- Development data only: fixtures under `eval/fixtures/`, or short messages written in the test itself.
- **Never** items from the sealed safety set (B1), `heldout_private/`, or the 4,000-message public core.
  A sealed item that runs in CI is no longer held out.
- No model calls and no keys: these tests run on every pull request.

The broader safety gate, `python -m tutor_eval.beta_front_door`, runs about 500 development cases through the
beta's front door and fails when any case that passed in `eval/baselines/beta_front_door_v1.json` now fails.
`test_front_door_gate.py` runs it inside pytest. When a change makes cases pass that used to fail, the gate
says so: run `python -m tutor_eval.beta_front_door --write-baseline` and commit the new baseline in the same PR.

Owner: R5. Each role adds the regressions for its own findings.
