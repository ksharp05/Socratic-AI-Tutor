"""Render a Markdown document to an A4 PDF with headless Chrome (no pandoc needed).

Usage (shared-checkout .venv):
  python scripts/release/build_report_pdf.py Docs/report/EVALUATION_REPORT.md OUT.pdf
HTML comments in the Markdown are dropped. Relative links stay as text targets; tables, code and lists are styled for print.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 9.6pt; line-height: 1.38; color: #1f2a44; }
h1 { font-size: 17pt; margin: 0 0 6pt; }
h2 { font-size: 12.5pt; margin: 12pt 0 4pt; border-bottom: 1px solid #c9ced8; padding-bottom: 2pt; }
h3 { font-size: 10.5pt; margin: 9pt 0 3pt; }
p, li { margin: 3pt 0; }
ul, ol { padding-left: 16pt; margin: 3pt 0; }
table { border-collapse: collapse; width: 100%; margin: 5pt 0; font-size: 8.4pt; page-break-inside: avoid; }
th, td { border: 1px solid #c9ced8; padding: 2.5pt 4pt; vertical-align: top; text-align: left; }
th { background: #eef1f5; }
code { font-family: Consolas, monospace; font-size: 8.4pt; background: #f3f4f6; padding: 0 2pt; }
pre { background: #f3f4f6; padding: 5pt; font-size: 8pt; white-space: pre-wrap; }
a { color: #1f2a44; text-decoration: none; }
"""


def find_chrome():
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"):
        if Path(p).exists():
            return p
    return shutil.which("chrome") or shutil.which("msedge") or shutil.which("chromium")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown"); ap.add_argument("pdf")
    args = ap.parse_args()
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    body = md.render(Path(args.markdown).read_text(encoding="utf-8"))
    title = Path(args.markdown).stem.replace("_", " ").title()
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"
    chrome = find_chrome()
    if not chrome:
        sys.exit("Chrome or Edge not found")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "report.html"
        page.write_text(html, encoding="utf-8")
        out = Path(args.pdf).resolve()
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", page.as_uri()], check=True, capture_output=True, timeout=120)
    try:
        from pypdf import PdfReader
        print(f"{out} · {len(PdfReader(str(out)).pages)} pages")
    except Exception:
        print(out)


if __name__ == "__main__":
    main()
