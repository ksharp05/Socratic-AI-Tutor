"""Build the NCERT section index: `python -m tutor.retrieval.ingest`.

Reads data/ncert/jemh104.pdf, jemh105.pdf and jemh108.pdf (copy them there; they are git-ignored),
extracts each page with `pdftotext -layout -enc UTF-8` (spike S3), chunks by section and writes
data/ncert/index/chunks.jsonl and manifest.json. With dense vectors on (the default when fastembed is
installed), it also writes dense.npy for the chunks. Nothing here ever enters git.

Only chapters 4, 5 and 8 are accepted; the answers appendix (jemh1an) and every other file are refused
(decision D-4).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

from ..config import ROOT
from .chunk import chunk_pages
from .sources import ALLOWED, RefusedSource, resolve, sha256_file

DEFAULT_PDF_DIR = ROOT / "data" / "ncert"
DEFAULT_INDEX_DIR = DEFAULT_PDF_DIR / "index"


def extractor_version() -> str:
    exe = shutil.which("pdftotext")
    if not exe:
        raise RuntimeError("pdftotext (poppler) is not on PATH; see Docs/spikes/S3.md")
    out = subprocess.run([exe, "-v"], capture_output=True, text=True)
    return (out.stderr or out.stdout).splitlines()[0].strip()


def extract_pages(pdf: Path) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"],
                         capture_output=True, check=True)
    pages = out.stdout.decode("utf-8").split("\f")
    return pages[:-1] if pages and not pages[-1].strip() else pages


def ingest(pdfs: list[Path], index_dir: Path, *, dense: bool = True, model: str = "BAAI/bge-small-en-v1.5",
           model_cache: Path | None = None) -> dict:
    sources = [(resolve(p), p) for p in pdfs]  # refuses before anything is read or written
    rows, manifest_sources = [], []
    for source, pdf in sources:
        digest = sha256_file(pdf)
        if digest != source.sha256:
            print(f"warning: {pdf.name} SHA-256 {digest[:12]} differs from the recorded "
                  f"{source.sha256[:12]}; NCERT may have reissued it", file=sys.stderr)
        chunks = chunk_pages(extract_pages(pdf), stem=source.stem, chapter=source.chapter,
                             chapter_number=source.chapter_number)
        for c in chunks:
            rows.append({**c.to_dict(), "kind_group": "section", "class": 10, "subject": "mathematics",
                         "source_id": source.source_id, "source_url": source.url, "source_sha256": digest})
        manifest_sources.append({"stem": source.stem, "source_id": source.source_id, "sha256": digest,
                                 "sha256_matches_record": digest == source.sha256, "chunks": len(chunks),
                                 "sections": sorted({c.section for c in chunks})})
    index_dir.mkdir(parents=True, exist_ok=True)
    with (index_dir / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {"created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "extractor": extractor_version(), "extractor_args": "-layout -enc UTF-8",
                "formula_check": "none: formulas are cited from cards (TP-T2)", "chunks": len(rows),
                "sources": manifest_sources, "dense": None}
    dense_path = index_dir / "dense.npy"
    if dense:
        from .dense import DenseEncoder, available
        if available():
            import numpy as np
            encoder = DenseEncoder(model, model_cache, allow_download=True)
            np.save(dense_path, encoder.embed_passages([r["text"] for r in rows]))
            manifest["dense"] = {"model": model, "dim": encoder.dim, "file": "dense.npy"}
        else:
            print("fastembed is not installed; building BM25 only", file=sys.stderr)
    if manifest["dense"] is None and dense_path.exists():
        dense_path.unlink()
    (index_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    from ..config import SETTINGS
    cfg = SETTINGS.raw.get("retrieval", {})
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdfs", nargs="*", type=Path,
                        help=f"PDFs to index (default: {', '.join(sorted(ALLOWED))} in --pdf-dir)")
    parser.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR)
    parser.add_argument("--out", type=Path, default=ROOT / cfg.get("index_dir", "data/ncert/index"))
    parser.add_argument("--no-dense", action="store_true", help="skip dense vectors")
    args = parser.parse_args(argv)
    pdfs = args.pdfs or [args.pdf_dir / f"{stem}.pdf" for stem in sorted(ALLOWED)]
    try:
        for p in pdfs:
            resolve(p)
    except RefusedSource as exc:
        print(exc, file=sys.stderr)
        return 2
    missing = [str(p) for p in pdfs if not p.exists()]
    if missing:
        print(f"missing PDFs: {', '.join(missing)}", file=sys.stderr)
        return 1
    manifest = ingest(pdfs, args.out, dense=not args.no_dense and cfg.get("dense", True),
                      model=cfg.get("dense_model", "BAAI/bge-small-en-v1.5"),
                      model_cache=ROOT / cfg.get("model_cache", "data/models"))
    print(json.dumps({"index": str(args.out), "chunks": manifest["chunks"], "dense": manifest["dense"],
                      "sources": [{k: s[k] for k in ("stem", "chunks", "sections")} for s in manifest["sources"]]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
