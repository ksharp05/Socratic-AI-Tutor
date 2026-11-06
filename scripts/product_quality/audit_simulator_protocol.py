"""No-network public task/format preflight, separate from any C1/C2 study.

python scripts/product_quality/audit_simulator_protocol.py --output PRIVATE_NEW_DIRECTORY
Outputs are refused if the directory already exists. Raw per-item rows stay private.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from tutor import mathcore
from tutor.question_catalog import graph_items, allowed
from tutor_eval import protocol_v2, simulator, harness
from tutor_validation import exact_reference as reference


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def audit(items):
    rows=[]
    for item in items:
        problem=item["problem"];key=mathcore.compute_key(problem)
        supported=protocol_v2.support(problem)
        row={"question_id":item["question_id"],"task_type":problem["task_type"],
             "problem_sha256":digest(problem),"support":supported}
        if not key["verified"] or reference.validate(problem,key["key"])["status"]!="verified":
            raise ValueError("Unverified public key: "+item["question_id"])
        for name,renderer in (("legacy",simulator.render),("v2",protocol_v2.render)):
            message=renderer(key["key"]);parsed=mathcore.parse_answer(message,key["key"])
            matches=bool(parsed["ok"] and mathcore.grade(parsed["typed"],key["key"])["correct"])
            row[name]={"message":message,"parsed":parsed["ok"],"matches_expected":matches}
        rows.append(row)
    inputs=sorted([{"id":i["question_id"],"problem":i["problem"]} for i in items],key=lambda r:r["id"])
    return {"protocol":protocol_v2.VERSION,"scope":"Public eligible practice canonical-answer roundtrip; no learner sessions or learning/diagnosis estimate",
            "items":len(rows),"task_counts":{t:sum(r["task_type"]==t for r in rows) for t in sorted({r["task_type"] for r in rows})},
            "input_manifest_sha256":digest(inputs),
            "mathematical_support":sum(r["support"]["supported"] for r in rows),
            "legacy_roundtrip":sum(r["legacy"]["matches_expected"] for r in rows),
            "v2_roundtrip":sum(r["v2"]["matches_expected"] for r in rows),
            "unsupported_ids":[r["question_id"] for r in rows if not r["support"]["supported"]],
            "source_sha256":{module.__name__:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                             for module in (protocol_v2,simulator,harness,reference,mathcore)},
            "legacy_harness_modified":False,"provider_calls":0,"human_review":False,"rows":rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing an existing output directory")
    items=[i for i in graph_items() if allowed(i,"practice")]
    if not items:
        raise SystemExit("No public practice inputs; refusing an empty qualification")
    report=audit(items)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"rows.json").write_text(json.dumps(report.pop("rows"),indent=2)+"\n",encoding="utf-8")
    (args.output/"SUMMARY.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report))
    if report["v2_roundtrip"]!=report["items"] or report["mathematical_support"]!=report["items"]:
        raise SystemExit("Protocol preflight failed; unsupported inputs retained")


if __name__=="__main__":
    main()
