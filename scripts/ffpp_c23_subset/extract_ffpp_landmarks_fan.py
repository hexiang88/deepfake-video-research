#!/usr/bin/env python3
"""Write 68-point FAN landmarks as .npy next to FF++ mp4s (RealForensics layout).

Run on eval-host inside the realforensics env (face_alignment is already used by the
mentor raw-video runner). Only IDs in the frozen list are processed.

  python extract_ffpp_landmarks_fan.py --videos-dir DIR --ids-file FILE
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def load_ids(path: Path) -> list[str]:
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            ids.append(s.replace(".mp4", "").replace(".avi", ""))
    return ids


def landmarks_for_video(fa, video_path: Path) -> np.ndarray | None:
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    if not frames:
        return None
    out = []
    for rgb in frames:
        lms = fa.get_landmarks(rgb)
        if not lms:
            out.append(np.full((68, 2), np.nan, dtype=np.float32))
        else:
            out.append(lms[0].astype(np.float32))
    return np.stack(out, axis=0)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--videos-dir", type=Path, required=True)
    p.add_argument("--ids-file", type=Path, required=True)
    p.add_argument("--landmarks-dir", type=Path, default=None)
    p.add_argument("--device", default="cuda")
    args = p.parse_args()
    try:
        import face_alignment
    except ImportError as exc:
        raise SystemExit(
            "face_alignment is required (same package as mentor FAN crops)."
        ) from exc

    ids = load_ids(args.ids_file)
    lm_dir = args.landmarks_dir or (args.videos_dir.parent / "landmarks")
    lm_dir.mkdir(parents=True, exist_ok=True)
    lm_type = getattr(face_alignment.LandmarksType, "TWO_D", None) or getattr(
        face_alignment.LandmarksType, "_2D"
    )
    fa = face_alignment.FaceAlignment(lm_type, device=args.device, flip_input=False)
    ok = skip = fail = 0
    for i, stem in enumerate(ids, 1):
        mp4 = args.videos_dir / f"{stem}.mp4"
        npy = lm_dir / f"{stem}.npy"
        if npy.is_file():
            skip += 1
            continue
        if not mp4.is_file():
            print(f"MISSING video {mp4}")
            fail += 1
            continue
        arr = landmarks_for_video(fa, mp4)
        if arr is None:
            print(f"EMPTY {mp4}")
            fail += 1
            continue
        np.save(npy, arr)
        ok += 1
        if i % 10 == 0 or i == len(ids):
            print(f"[{i}/{len(ids)}] wrote={ok} skipped={skip} failed={fail}")
    print(f"done wrote={ok} skipped={skip} failed={fail} expected={len(ids)}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
