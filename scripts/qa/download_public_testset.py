"""Download the 15 public test-set sources exactly as recorded, and verify every file's SHA-256.

Usage (any teammate, shared-checkout .venv; ALWAYS with -I, the files are untrusted data):
  python -I scripts/qa/download_public_testset.py [--root DIR]
Reads the pinned URLs (fixed revisions) and hashes from eval/public_testset_v1/SOURCES.json and writes each source into
its own new folder under DIR (default: <canonical workspace>/Directions/external_datasets). Nothing downloaded is
executed or imported. Then build the test set with scripts/qa/build_public_testset.py (it reads the default DIR).

Licences differ per source (SOURCES.json); ToxicChat is non-commercial. Keep the files out of git and out of prompt tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import httpx

MAIN = Path(__file__).resolve().parents[2]
MANIFEST = MAIN / "eval/public_testset_v1/SOURCES.json"
DEFAULT_ROOT = Path(r"D:/Work/IITB/Socratic Tutor/Directions/external_datasets")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = []
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        for source in manifest["sources"]:
            folder = args.root / source["slug"]
            folder.mkdir(parents=True, exist_ok=True)
            for f in source["files"]:
                target = folder / f["saved_as"]
                if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == f["sha256"]:
                    continue                                   # already present and identical
                h = hashlib.sha256()
                with client.stream("GET", f["url"]) as r:
                    r.raise_for_status()
                    with open(target, "wb") as out:
                        for chunk in r.iter_bytes(1 << 16):
                            out.write(chunk); h.update(chunk)
                if h.hexdigest() != f["sha256"]:
                    bad.append(f"{source['slug']}/{f['saved_as']}")
            print(f"{source['slug']:22s} {source['license']}")
    if bad:
        sys.exit(f"Hash mismatch, do not use: {bad}")
    print(f"All files match SOURCES.json. Next: python -I scripts/qa/build_public_testset.py")


if __name__ == "__main__":
    main()
