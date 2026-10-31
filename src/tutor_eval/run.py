"""`tutor eval`: the evaluation pipeline's smoke run on the development cards (eval/configs/dev_smoke.toml).

Every number here is a smoke test, not a result. The full harness is `python -m tutor_eval.harness`; see eval/README.md.
"""
from __future__ import annotations

from tutor.config import ROOT
from tutor_eval import harness


def main(seeds: int = 1, defences: bool = True) -> None:
    run_dir = harness.run(ROOT / "eval" / "configs" / "dev_smoke.toml", seeds=list(range(1, seeds + 1)), defences=defences)
    print((run_dir / "report.md").read_text(encoding="utf-8").split("## Sessions")[0])
    print(f"Full report with every transcript: {run_dir / 'report.md'}")
