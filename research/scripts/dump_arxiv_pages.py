"""Dump full text of pages that mention experimental tables."""

from __future__ import annotations

import os
from pathlib import Path

import fitz

pdf_dir = Path(os.environ.get("TEMP", "/tmp")) / "av-arxiv-pdfs"
out_dir = pdf_dir / "pages"
out_dir.mkdir(exist_ok=True)

targets = {
    "2110.01200": [2, 3, 4],
    "2107.12710": [4, 5, 6],
    "2107.12212": [4, 5, 6],
    "2409.09272": [6, 7, 8, 9, 10],
    "2405.04880": [6, 7, 8, 9, 10, 11],
    "2601.02944": [6, 7, 8, 9],
    "2605.23201": [3, 4, 5, 6],
    "1809.00888": [3, 4, 5, 6],
    "2012.07657": [5, 6, 7, 8],
    "2201.07131": [5, 6, 7, 8],
    "2108.06693": [5, 6, 7],
    "2307.08317": [5, 6, 7, 8],
    "2307.07036": [4, 5, 6, 7],
    "2403.06592": [5, 6, 7, 8],
    "2501.01184": [5, 6, 7, 8],
    "2507.02398": [5, 6, 7, 8],
    "2411.10193": [5, 6, 7, 8, 9],
    "2511.18993": [5, 6, 7, 8],
    "2511.10212": [5, 6, 7, 8],
    "2603.24454": [5, 6, 7, 8],
}

for stem, pages in targets.items():
    pdf = pdf_dir / f"{stem}.pdf"
    if not pdf.exists():
        print("MISS", stem)
        continue
    doc = fitz.open(pdf)
    parts = [f"FILE {stem} pages={doc.page_count}"]
    for p in pages:
        if p > doc.page_count:
            continue
        text = doc[p - 1].get_text("text")
        parts.append(f"\n\n===== PAGE {p} =====\n{text}")
    dest = out_dir / f"{stem}.txt"
    dest.write_text("".join(parts), encoding="utf-8")
    print(f"WROTE {stem} chars={dest.stat().st_size}")
