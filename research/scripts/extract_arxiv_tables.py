"""Extract table-like windows from downloaded arXiv PDFs. Local-only; no network."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import fitz

pdf_dir = Path(os.environ.get("TEMP", "/tmp")) / "av-arxiv-pdfs"
out_dir = pdf_dir / "extracts"
out_dir.mkdir(exist_ok=True)

table_re = re.compile(r"Table\s+\d+", re.I)
metric_re = re.compile(r"\b(EER|AUC|AP@|t-DCF|Accuracy)\b", re.I)

summaries: dict[str, object] = {}
for pdf in sorted(pdf_dir.glob("*.pdf")):
    doc = fitz.open(pdf)
    lines: list[str] = []
    for i, page in enumerate(doc):
        lines.append(f"===== PAGE {i + 1} =====")
        lines.extend(page.get_text("text").splitlines())

    hits: list[str] = []
    for idx, line in enumerate(lines):
        if table_re.search(line) or metric_re.search(line):
            start = max(0, idx - 1)
            end = min(len(lines), idx + 20)
            chunk = "\n".join(lines[start:end]).strip()
            if chunk not in hits:
                hits.append(chunk)

    extract_path = out_dir / f"{pdf.stem}.txt"
    extract_path.write_text("\n\n----- TABLE WINDOW -----\n\n".join(hits[:50]), encoding="utf-8")
    first = next((ln.strip() for ln in lines if ln.strip() and not ln.startswith("=====")), "")
    summaries[pdf.stem] = {
        "pages": doc.page_count,
        "windows": len(hits),
        "extract": extract_path.name,
        "first_line": first[:200],
    }
    print(f"{pdf.stem}: pages={doc.page_count} windows={len(hits)}")

(out_dir / "_index.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
print("DONE", len(summaries), "->", out_dir)
