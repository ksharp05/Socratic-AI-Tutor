# NCERT Mathematics textbooks: Classes 8–12

Acquired on 3 November 2026 from the [official NCERT catalogue](https://ncert.nic.in/textbook.php). English medium. **Complete: eight volumes, all 69 listed chapters, 88 original PDFs and 1,995 source pages.** Page counts include prelims, appendices, supplementary material and answers where supplied.

Collection folder: `D:\Work\IITB\Socratic Tutor\Directions\ncert_maths_8_12\2026-11-03`. The entire collection is inside the existing Git-ignored `Directions/` directory.

The reading copies below are locally assembled for convenient reading, with chapter bookmarks. They are not NCERT single-file downloads. Official ZIP archives and all original PDF members are preserved byte-for-byte beside each reading copy.

| Class | Book | Observed edition/reprint | Chapters | Pages | Reading PDF | Official source |
|---|---|---|---:|---:|---|---|
| 8 | Ganita Prakash Part-I | Reprint 2026-27 | 7 | 263 | [Open PDF](<D:/Work/IITB/Socratic Tutor/Directions/ncert_maths_8_12/2026-11-03/class_08/hegp1/NCERT_Class_08_Ganita_Prakash_Part_I.pdf>) | [NCERT ZIP](https://ncert.nic.in/textbook/pdf/hegp1dd.zip) |
| 8 | Ganita Prakash Part-II | First edition December 2025 | 7 | 192 | [Open PDF](<D:/Work/IITB/Socratic Tutor/Directions/ncert_maths_8_12/2026-11-03/class_08/hegp2/NCERT_Class_08_Ganita_Prakash_Part_II.pdf>) | [NCERT ZIP](https://ncert.nic.in/textbook/pdf/hegp2dd.zip) |
| 9 | Ganita Manjari Part-I | First edition April 2026 | 8 | 220 | [Open PDF](<D:/Work/IITB/Socratic Tutor/Directions/ncert_maths_8_12/2026-11-03/class_09/iemh1/NCERT_Class_09_Ganita_Manjari_Part_I.pdf>) | [NCERT ZIP](https://ncert.nic.in/textbook/pdf/iemh1dd.zip) |
| 9 | Ganita Manjari PART-II | First edition August 2026 | 6 | 184 | [Open PDF](<D:/Work/IITB/Socratic Tutor/Directions/ncert_maths_8_12/2026-11-03/class_09/iemh2/NCERT_Class_09_Ganita_Manjari_Part_II.pdf>) | [NCERT ZIP](https://ncert.nic.in/textbook/pdf/iemh2dd.zip) |
| 10 | Mathematics | Reprint 2026-27 | 14 | 276 | [Open PDF](<D:/Work/IITB/Socratic Tutor/Directions/ncert_maths_8_12/2026-11-03/class_10/jemh1/NCERT_Class_10_Mathematics.pdf>) | [NCERT ZIP](https://ncert.nic.in/textbook/pdf/jemh1dd.zip) |
| 11 | Mathematics | Reprint 2026-27 | 14 | 376 | [Open PDF](<D:/Work/IITB/Socratic Tutor/Directions/ncert_maths_8_12/2026-11-03/class_11/kemh1/NCERT_Class_11_Mathematics.pdf>) | [NCERT ZIP](https://ncert.nic.in/textbook/pdf/kemh1dd.zip) |
| 12 | Mathematics Part-I | Reprint 2026-27 | 6 | 236 | [Open PDF](<D:/Work/IITB/Socratic Tutor/Directions/ncert_maths_8_12/2026-11-03/class_12/lemh1/NCERT_Class_12_Mathematics_Part_I.pdf>) | [NCERT ZIP](https://ncert.nic.in/textbook/pdf/lemh1dd.zip) |
| 12 | Mathematics Part-II | Reprint 2026-27 | 7 | 248 | [Open PDF](<D:/Work/IITB/Socratic Tutor/Directions/ncert_maths_8_12/2026-11-03/class_12/lemh2/NCERT_Class_12_Mathematics_Part_II.pdf>) | [NCERT ZIP](https://ncert.nic.in/textbook/pdf/lemh2dd.zip) |

## Verification performed

- Selected book codes and chapter counts from NCERT’s live class-specific Mathematics dropdown, not from guessed older titles. The catalogue HTML and hash are retained.
- Downloaded eight full-book ZIPs over HTTPS with TLS verification enabled; verified all ZIP CRCs and archived source URL, final URL, retrieval time, size and hash receipts. One interrupted connection was retried successfully.
- Verified all 69 numbered chapter files, eight prelim files and the additional supplied appendices/answers/supplementary file. No chapter or volume is missing.
- Parsed all 88 PDFs, checked page dimensions and decoded every page content stream. All 1,995 assembled-page content stream hashes match their original source pages. Bookmarks preserve continued chapter numbering for Classes 9 and 12 Part II.
- Independently opened all eight reading copies with Poppler; rendered and visually checked a title and first chapter page for each volume. This is sampled layout QA, not a proof of every mathematical assertion.
- Sixteen Class 10 source PDFs carry encryption metadata but open without a supplied password. Those official source bytes remain unchanged.
- Rechecked the earlier nine-source Class 10 pool: unchanged. The tutor, its teaching scope and its knowledge-admission workflow were not modified by acquisition.

## Storage and provenance

Each `class_XX/book_code/` folder contains the original official `book_codedd.zip`, `archive_receipt.json`, `original_pdfs/`, `volume_manifest.json`, and the assembled reading PDF. `MANIFEST.json` at the collection root binds all PDFs and assembled-page mappings. `book_selection.json` records catalogue evidence. `qa/` contains the rendered samples and their check record.

The metadata-only shareable inventory is `Docs/knowledge_acquisition/NCERT_MATHS_8_12_ACQUISITION.json`. Book sources remain local project reference material; no source PDF or extracted text was placed in the shared documentation folder. Answers contained in the collected books must be separated before any future tutor retrieval export.

## Re-run commands

Run from `D:\Work\IITB\Socratic Tutor`. The acquisition reuses and checks receipted archives, preserving the pinned snapshot. It does not silently replace an archive with a newer remote revision. These commands need Python with `pypdf` for validation/assembly, plus Windows `curl.exe`; rendering also needs Poppler and Pillow. The bundled runtime was used for this acquisition.

```powershell
Set-Location -LiteralPath 'D:\Work\IITB\Socratic Tutor'
$bookPython = 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $bookPython -X utf8 tools\knowledge_acquisition\acquire_ncert_maths_8_12.py
& $bookPython -X utf8 tools\knowledge_acquisition\verify_assemble_ncert_maths_8_12.py
& $bookPython -X utf8 tools\knowledge_acquisition\render_ncert_maths_8_12.py
```

Inspect newly rendered pages before renewing a visual-inspection claim. Existing sources, snapshots and manifests are retained; a future NCERT update belongs in a new dated acquisition, not an overwrite of this collection.
