#!/usr/bin/env python3
"""Download official FaceForensics++ c23 TEST videos (stdlib only).

URL scheme copied from https://kaldir.vc.in.tum.de/faceforensics_download_v4.py
(per-file HTTP, not zip):

    {server}v3/{dataset_path}/{compression}/{type}/{filename}.mp4

Default IDs: official test.json (140 original + 140 fake per method).
Do NOT use v4 --num_videos N: that takes the filelist.json PREFIX, not test.

Example (Windows):

    py -3 scripts\\ffpp_c23_subset\\download_ffpp_test_c23.py
"""
from __future__ import annotations

import argparse
import json
import random
import ssl
import sys
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
IDS_DIR = SCRIPT_DIR / "ids"
REPO_ROOT = SCRIPT_DIR.parents[1]

SERVERS = {
    "EU2": "http://kaldir.vc.in.tum.de/faceforensics/",
    "EU": "http://canis.vc.in.tum.de:8100/",
    "CA": "http://falas.cmpt.sfu.ca:8100/",
}

DATASETS = {
    "original": "original_sequences/youtube",
    "Deepfakes": "manipulated_sequences/Deepfakes",
    "Face2Face": "manipulated_sequences/Face2Face",
    "FaceSwap": "manipulated_sequences/FaceSwap",
    "NeuralTextures": "manipulated_sequences/NeuralTextures",
}

METHODS = ("Deepfakes", "Face2Face", "FaceSwap", "NeuralTextures")
FAKE_SEED = 20260818
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def load_pairs(name: str) -> list[list[str]]:
    path = IDS_DIR / name
    pairs = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(pairs, list) or not pairs:
        raise SystemExit(f"bad split file: {path}")
    return pairs


def originals_from_pairs(pairs: list[list[str]]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for a, b in pairs:
        for x in (a, b):
            if x not in seen:
                seen.add(x)
                out.append(x)
    return out


def fakes_from_pairs(pairs: list[list[str]]) -> list[str]:
    names: list[str] = []
    for a, b in pairs:
        names.append(f"{a}_{b}")
        names.append(f"{b}_{a}")
    return names


def select_pairs(extra_from_val: int) -> list[list[str]]:
    test = load_pairs("test.json")
    if extra_from_val <= 0:
        return test
    val = load_pairs("val.json")
    n_pairs = extra_from_val // 2
    if extra_from_val % 2 != 0:
        raise SystemExit("--extra-from-val must be even (each val pair = 2 originals)")
    if n_pairs > len(val):
        raise SystemExit("not enough val pairs")
    rng = random.Random(FAKE_SEED)
    extra = rng.sample(val, n_pairs)
    print(
        f"Using official TEST ({len(test)*2} originals) plus "
        f"{n_pairs} VAL pairs ({extra_from_val} originals), seed={FAKE_SEED}. "
        "Train IDs are never used.",
        flush=True,
    )
    return test + extra


def tos_gate(server: str, skip: bool) -> None:
    tos = SERVERS[server] + "webpage/FaceForensics_TOS.pdf"
    print("By continuing you confirm you agreed to the FaceForensics terms of use:")
    print(tos)
    print("Press Enter to continue, or Ctrl+C to exit.")
    if skip:
        print("( --yes : skipping keyboard wait )")
        return
    input()


def dest_dir(root: Path, dataset: str) -> Path:
    return root / DATASETS[dataset] / "c23" / "videos"


def file_url(server: str, dataset: str, filename: str) -> str:
    base = SERVERS[server] + "v3/"
    return f"{base}{DATASETS[dataset]}/c23/videos/{filename}"


def download_one(url: str, out_file: Path, timeout: int) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    if out_file.is_file() and out_file.stat().st_size > 0:
        return
    tmp_path = out_file.with_suffix(out_file.suffix + ".part")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ffpp-c23-subset/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            data = resp.read()
        if len(data) < 1024:
            raise RuntimeError(f"tiny response ({len(data)} bytes) from {url}")
        tmp_path.write_bytes(data)
        tmp_path.replace(out_file)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def try_download(filename: str, dataset: str, root: Path, servers: list[str], timeout: int) -> str:
    out = dest_dir(root, dataset) / filename
    if out.is_file() and out.stat().st_size > 0:
        return "skip"
    last_err: Exception | None = None
    for server in servers:
        url = file_url(server, dataset, filename)
        try:
            download_one(url, out, timeout)
            return server
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.4)
    raise RuntimeError(f"failed {dataset}/{filename}: {last_err}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "datasets" / "ffpp_c23_subset",
        help="FaceForensics++-layout output root",
    )
    p.add_argument("--server", choices=list(SERVERS), default="EU2")
    p.add_argument(
        "--extra-from-val",
        type=int,
        default=0,
        help="Only if you insist on n=200: add this many originals from VAL "
        "(use 60). Even number. Seed 20260818. Never train.",
    )
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--yes", action="store_true", help="Do not wait for TOS Enter")
    p.add_argument("--check", action="store_true", help="Only count local files vs ID list")
    p.add_argument(
        "--datasets",
        nargs="+",
        default=["original", *METHODS],
        choices=["original", *METHODS],
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    pairs = select_pairs(args.extra_from_val)
    orig = originals_from_pairs(pairs)
    fake = fakes_from_pairs(pairs)
    print(
        f"IDs: {len(orig)} original, {len(fake)} fake-stems; "
        f"methods={ [d for d in args.datasets if d != 'original'] }",
        flush=True,
    )
    print(f"Output: {args.out}", flush=True)
    print(
        "v4 --num_videos is NOT used (it is an arbitrary filelist prefix).",
        flush=True,
    )
    id_dest = args.out / "ids"
    id_dest.mkdir(parents=True, exist_ok=True)
    for src in IDS_DIR.glob("*"):
        if src.is_file():
            shutil.copy2(src, id_dest / src.name)
    (id_dest / "used_originals.txt").write_text("\n".join(orig) + "\n", encoding="utf-8")
    (id_dest / "used_fakes.txt").write_text("\n".join(fake) + "\n", encoding="utf-8")
    (id_dest / "used_pairs.json").write_text(
        json.dumps(pairs, indent=1) + "\n", encoding="utf-8"
    )
    jobs: list[tuple[str, str]] = []
    if "original" in args.datasets:
        jobs.extend((vid + ".mp4", "original") for vid in orig)
    for method in METHODS:
        if method in args.datasets:
            jobs.extend((name + ".mp4", method) for name in fake)

    if args.check:
        present = missing = 0
        for filename, dataset in jobs:
            path = dest_dir(args.out, dataset) / filename
            if path.is_file() and path.stat().st_size > 0:
                present += 1
            else:
                missing += 1
                if missing <= 12:
                    print(f"missing {dataset}/{filename}")
        print(f"check: present={present} missing={missing} expected={len(jobs)}")
        return 0 if missing == 0 else 2

    tos_gate(args.server, skip=args.yes)
    servers = [args.server] + [s for s in ("EU2", "EU", "CA") if s != args.server]

    ok = skip = fail = 0
    failed: list[str] = []
    for i, (filename, dataset) in enumerate(jobs, 1):
        try:
            status = try_download(filename, dataset, args.out, servers, args.timeout)
            if status == "skip":
                skip += 1
            else:
                ok += 1
            if i % 10 == 0 or i == len(jobs):
                print(
                    f"[{i}/{len(jobs)}] downloaded={ok} skipped={skip} failed={fail} "
                    f"last={dataset}/{filename}",
                    flush=True,
                )
        except Exception as exc:  # noqa: BLE001
            fail += 1
            failed.append(f"{dataset}/{filename}: {exc}")
            print(f"FAIL {dataset}/{filename}: {exc}", flush=True)

    print(f"Done. downloaded={ok} skipped={skip} failed={fail} total={len(jobs)}")
    if failed:
        print("Failures:")
        print("\n".join(failed[:20]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
