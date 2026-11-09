"""Summarise judged probe runs: pass rates by area for each judge, both judges, agreement and mean scores.

Usage: python summarise_runs.py SLUG LABEL [SLUG LABEL ...] [--json OUT]
"""
from __future__ import annotations
import json, sys, collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_probe_run as h  # noqa: E402

AREAS = ["language", "tone", "topics", "out_of_context", "foul_language", "safety", "system_prompt"]
DIMS = ["expected_behaviour", "language_fit", "tone", "pedagogy", "accuracy", "relevance"]


def load(slug, label):
    folder = h.CAN / "Directions/product_quality/v4/runs" / slug
    run = json.loads((folder / f"{label}.json").read_text(encoding="utf-8"))
    judges = {}
    for f in sorted(folder.glob(f"{label}.judge-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        judges[d["judge"]] = {j["id"]: j for j in d["judgements"]}
    return run, judges


def summarise(slug, label):
    run, judges = load(slug, label)
    rows = {r["id"]: r for r in run["results"]}
    out = {"label": label, "meta": run["meta"], "judges": list(judges), "areas": {}, "dims": {}, "agreement": None, "issues": {}}
    names = list(judges)
    for area in AREAS + ["all"]:
        ids = [i for i, r in rows.items() if area == "all" or r["area"] == area]
        entry = {"n": len(ids)}
        for name in names:
            v = [judges[name].get(i, {}).get("verdict") for i in ids]
            entry[name] = sum(x == "pass" for x in v) / max(1, sum(x in ("pass", "fail") for x in v))
        both = [all(judges[n].get(i, {}).get("verdict") == "pass" for n in names) for i in ids]
        entry["both_pass"] = sum(both) / max(1, len(ids))
        safety_fail = [any(judges[n].get(i, {}).get("safety") == "fail" for n in names) for i in ids]
        entry["any_safety_fail"] = sum(safety_fail)
        out["areas"][area] = entry
    if len(names) == 2:
        a, b = names
        pairs = [(judges[a][i].get("verdict"), judges[b][i].get("verdict")) for i in rows if i in judges[a] and i in judges[b]]
        out["agreement"] = sum(x == y for x, y in pairs) / max(1, len(pairs))
    for dim in DIMS:
        vals = [j.get(dim) for name in names for j in judges[name].values() if isinstance(j.get(dim), (int, float))]
        out["dims"][dim] = round(sum(vals) / len(vals), 2) if vals else None
    issues = collections.Counter()
    for name in names:
        for j in judges[name].values():
            if j.get("verdict") == "fail" and j.get("issue"):
                issues[j["issue"].lower()[:60]] += 1
    out["issues"] = issues.most_common(15)
    return out


def main():
    args = sys.argv[1:]
    out_file = None
    if "--json" in args:
        k = args.index("--json"); out_file = args[k + 1]; args = args[:k] + args[k + 2:]
    results = [summarise(args[i], args[i + 1]) for i in range(0, len(args), 2)]
    for s in results:
        print(f"\n=== {s['label']}  judges: {', '.join(s['judges'])}  agreement: {s['agreement']}")
        print("area".ljust(16) + "n".rjust(4) + "".join(n.split('/')[-1][:14].rjust(16) for n in s["judges"]) + "both_pass".rjust(11) + "safety_fail".rjust(13))
        for area, e in s["areas"].items():
            print(area.ljust(16) + str(e["n"]).rjust(4) + "".join(f"{e[n]:16.0%}" for n in s["judges"]) + f"{e['both_pass']:11.0%}" + str(e["any_safety_fail"]).rjust(13))
        print("mean scores:", s["dims"])
    if out_file:
        Path(out_file).write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
