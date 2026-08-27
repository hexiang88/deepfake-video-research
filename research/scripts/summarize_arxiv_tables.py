"""Write compact table captions and numeric rows from PDF extracts."""

from __future__ import annotations

import os
import re
from pathlib import Path

extract_dir = Path(os.environ.get("TEMP", "/tmp")) / "av-arxiv-pdfs" / "extracts"
out_path = extract_dir / "_summary.txt"
names = {
    "2110.01200": "AASIST",
    "2405.04880": "Codecfake",
    "2601.02944": "XLSR-MamBo",
    "2107.12212": "Raw-PC-DARTS",
    "2409.09272": "SafeEar",
    "2605.23201": "MixFake",
    "2107.12710": "RawGAT-ST",
    "1809.00888": "MesoNet",
    "2012.07657": "LipForensics",
    "2201.07131": "RealForensics",
    "2108.06693": "FTCN",
    "2307.08317": "AltFreezing",
    "2411.10193": "DiMoDif",
    "2507.02398": "PwTF-DVD",
    "2511.18993": "AuViRe",
    "2403.06592": "StyleFlow",
    "2307.07036": "GenConViT",
    "2501.01184": "FakeSTormer",
    "2511.10212": "NextFrame-Anshul",
    "2603.24454": "VLAForge",
}

caption_re = re.compile(r"Table\s+\d+[:.\s].{0,160}", re.I)
num_re = re.compile(r"\d+\.\d+")
chunks: list[str] = []

for stem, label in names.items():
    path = extract_dir / f"{stem}.txt"
    chunks.append("\n" + "=" * 80)
    chunks.append(f"{label} {stem}")
    chunks.append("=" * 80)
    if not path.exists():
        chunks.append("MISSING")
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    captions = caption_re.findall(text)
    seen: list[str] = []
    for c in captions:
        c = re.sub(r"\s+", " ", c).strip()
        if c not in seen:
            seen.append(c)
    for c in seen[:12]:
        chunks.append("CAP: " + c)
    windows = text.split("----- TABLE WINDOW -----")
    shown = 0
    for w in windows:
        if re.search(r"Table\s+\d+", w, re.I) and num_re.search(w):
            shown += 1
            compact = re.sub(r"[ \t]+", " ", w)
            compact = re.sub(r"\n{2,}", "\n", compact).strip()
            chunks.append("\nWINDOW:")
            chunks.append("\n".join(compact.splitlines()[:32]))
            if shown >= 4:
                break

out_path.write_text("\n".join(chunks), encoding="utf-8")
print(f"WROTE {out_path} chars={out_path.stat().st_size}")
