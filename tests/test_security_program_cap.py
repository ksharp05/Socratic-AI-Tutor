"""The capped spending programme (e.g. the USD 5 security test) inside the v4 product phase."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "live_probe_run", Path(__file__).resolve().parents[1] / "scripts" / "qa" / "live_probe_run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

PROGRAM = {"cap_usd": 5.0, "batch_prefix": "v4-sec-"}


def phase(*batches):
    return {"batch_allocations": [{"batch": b, "max_usd": usd, "status": s} for b, usd, s in batches]}


def test_empty_programme_has_full_cap():
    assert runner.program_headroom(phase(("v4-models-02", 0.34, "completed")), PROGRAM) == 5.0


def test_closed_batches_count_at_sealed_spend_and_running_at_full_cap():
    data = phase(("v4-sec-01", 0.62, "completed"), ("v4-sec-02", 1.0, "running"), ("v4-router-01", 0.36, "completed"))
    assert runner.program_headroom(data, PROGRAM) == pytest.approx(3.38)


def test_other_batches_never_reduce_the_programme():
    data = phase(("hosted-vercel-live-02", 0.5, "running"), ("v4-baseline-01", 0.17, "completed"))
    assert runner.program_headroom(data, PROGRAM) == 5.0


def test_exhausted_programme_has_no_headroom():
    data = phase(*[(f"v4-sec-0{i}", 1.0, "completed") for i in range(1, 6)])
    assert runner.program_headroom(data, PROGRAM) == pytest.approx(0.0)
