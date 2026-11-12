# Socrates Beta latency benchmark

Extract the report ZIP and open `latency-report.html` in a browser. The report works offline and includes a selector for every measured request. `timings-detailed.csv` contains one row per query. `traces-detailed.json` contains the timed spans and checkout provenance.

The original run used 100 synthetic Class 10 maths questions through the local Beta HTTP application, SQLite and the offline source fallback. It included 70 first turns and 30 follow-ups. Three warmups and session setup were outside the measured sample. The published portable runner preserves the workload and timing methods and accepts a fresh output directory.

With the Beta development environment installed, run from the repository root:

```bash
python Docs/report/beta-latency/benchmark.py --out ./beta-latency-rerun
```

The command writes a new CSV and JSON receipt. The HTML in the bundle displays the original run. The hosted comparison comes from archived receipts carried in the published trace. The local benchmark makes no provider calls.
