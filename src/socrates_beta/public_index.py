"""Reproducible beta index from committed normalized maths references only."""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import uuid
from pathlib import Path
from filelock import FileLock
from ncert_pipeline.build import SCHEMA, insert_passage
from .knowledge import DatasetRegistry, database

VERSION = "public-maths-reference-v1"
FILES = ("content/dataset-v0.10.0/corpus.jsonl", "content/dataset-v0.10.0/concepts.jsonl")
UNITS = {"quadratic_equations":4, "arithmetic_progressions":5, "introduction_to_trigonometry":8, "trigonometry":8}


def prepare_public_index(app_root: Path, data: Path):
    data=Path(data);data.mkdir(parents=True,exist_ok=True)
    with FileLock(str(data/'public-index.lock'),timeout=30):
        return _prepare_public_index(app_root,data)


def _prepare_public_index(app_root: Path, data: Path):
    app_root, data = Path(app_root), Path(data)
    inputs = {rel:hashlib.sha256((app_root/rel).read_bytes()).hexdigest() for rel in FILES}
    digest = hashlib.sha256(json.dumps({"version":VERSION,"inputs":inputs},sort_keys=True).encode()).hexdigest()
    dataset_id = VERSION + "-" + digest[:12]
    registry = DatasetRegistry(data)
    active = registry.entries().get("active")
    if active:
        entry = registry.entries()["datasets"][active]
        if active != dataset_id or entry.get("provenance",{}).get("public_input_sha256") != inputs:
            raise ValueError("Active content differs; preserve it and perform an explicit dataset migration")
        registry.knowledge()
        return registry
    target = data/"datasets"/dataset_id/"knowledge.sqlite"
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() or list(target.parent.glob("building-*.sqlite")):
        raise ValueError("Unregistered or unfinished public index exists; inspect before changing it")
    staging = target.with_name("building-"+uuid.uuid4().hex+".sqlite")
    corpus = [json.loads(line) for line in (app_root/FILES[0]).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    concepts = [json.loads(line) for line in (app_root/FILES[1]).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not corpus or not concepts:
        raise ValueError("Empty public source pack")
    try:
        with database(staging) as conn:
            conn.executescript(SCHEMA)
            conn.execute("CREATE TABLE concepts(id TEXT PRIMARY KEY,title TEXT,description TEXT,prerequisites TEXT,unit INTEGER,passage_ids TEXT)")
            for row in corpus:
                if (row["chapter"] not in UNITS or row["class"] != 10 or row["human_review_status"] != "pending"
                        or row.get("approved_for_publication") is not False
                        or row.get("authorship") != "original_normalized_mathematical_reference_not_a_pdf_transcription"):
                    raise ValueError("Public pack provenance/review scope mismatch")
                anchor = row["source_anchor"]
                insert_passage(conn, {"id":row["passage_id"],"source_id":anchor["source_id"],"book":"jemh1",
                    "subject":"Mathematics","title":row["title"],"page":anchor["source_pdf_page"],
                    "unit_file_index":UNITS[row["chapter"]],"kind":"normalized_reference","text":row["text"],
                    "source_sha256":anchor["source_sha256"],"source_url":anchor["source_url"],
                    "human_review_status":"pending"}, [10])
            for row in concepts:
                if not all(conn.execute("SELECT 1 FROM passages WHERE id=?",(pid,)).fetchone() for pid in row["supporting_passage_ids"]):
                    raise ValueError("Unbound concept reference")
                conn.execute("INSERT INTO concepts VALUES (?,?,?,?,?,?)",
                    (row["concept_id"],row["title"],row["explanation"],json.dumps(row["prerequisites"]),
                     UNITS[row["chapter"]],json.dumps(row["supporting_passage_ids"])))
            conn.execute("INSERT INTO metadata VALUES (?,?)",("public_source_pack",json.dumps({"version":VERSION,"inputs":inputs,"human_review":False})))
        os.replace(staging,target)
        registry.register(dataset_id,target,title="Class 10 maths · three-chapter beta references",activate=True,
            provenance={"adapter":VERSION,"public_input_sha256":inputs,"human_approvals":0})
        return registry
    except Exception:
        # Keep incomplete source builds for inspection, never silently rebuild them.
        raise
