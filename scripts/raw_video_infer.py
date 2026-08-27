"""Shared raw-video helpers for LipForensics / RealForensics mentor-set wrappers.

Does not rewrite official models. Face crops use FAN (face_alignment, SFD detector).
dlib is optional and not required for the default path.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[1]

FACE_ALIGN_HINT = (
    "Install into this conda env (do not upgrade torch):\n"
    "  python -m pip install face-alignment==1.3.5 scikit-image==0.19.3 "
    "opencv-python==4.5.5.64 numba==0.56.4 llvmlite==0.39.1 matplotlib==3.5.3 "
    "filterpy==1.4.5 imageio==2.19.5 tifffile==2023.7.10 PyWavelets==1.4.1 "
    "networkx==2.8.8 --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple "
    "--default-timeout=1000\n"
    "SFD (default) does not need dlib. If you later switch detector=dlib:\n"
    "  conda install -c conda-forge dlib   # pip install dlib often needs cmake"
)
OPENCV_HINT = (
    "Install opencv-python==4.5.5.64 (py3.8 wheel) with --no-deps so torch stays put."
)
SKIMAGE_HINT = (
    "Install scikit-image==0.19.3 (LipForensics mouth warp uses skimage.transform)."
)


def require_module(name: str, hint: str) -> ModuleType:
    try:
        return importlib.import_module(name)
    except ImportError:
        print(f"ERROR: missing Python package '{name}'.\n{hint}", file=sys.stderr)
        raise SystemExit(5) from None


def load_frames_rgb(video_path: Path, max_frames: int) -> list[np.ndarray]:
    cv2 = require_module("cv2", OPENCV_HINT)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {video_path}")
    frames: list[np.ndarray] = []
    while len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    if not frames:
        raise RuntimeError(f"no frames decoded: {video_path}")
    return frames


def _landmarks_enum(face_alignment: Any) -> Any:
    lt = face_alignment.LandmarksType
    return getattr(lt, "_2D", None) or getattr(lt, "TWO_D")


def landmarks_68(
    frames: list[np.ndarray],
    *,
    device: str,
) -> list[np.ndarray | None]:
    """68-point FAN landmarks. Default detector is SFD (torch), not dlib."""
    fa_mod = require_module("face_alignment", FACE_ALIGN_HINT)
    require_module("skimage", SKIMAGE_HINT)
    runtime = "cuda" if str(device).startswith("cuda") else "cpu"
    try:
        fa = fa_mod.FaceAlignment(
            _landmarks_enum(fa_mod),
            flip_input=False,
            device=runtime,
            face_detector="sfd",
        )
    except Exception as exc:
        print(
            "ERROR: failed to init face_alignment (SFD). "
            f"{exc}\n{FACE_ALIGN_HINT}",
            file=sys.stderr,
        )
        raise SystemExit(5) from exc
    out: list[np.ndarray | None] = []
    last: np.ndarray | None = None
    for frame in frames:
        lms = fa.get_landmarks_from_image(frame)
        if lms is None or len(lms) == 0:
            out.append(last.copy() if last is not None else None)
            continue
        chosen = max(lms, key=lambda arr: _face_area(arr))
        last = np.asarray(chosen, dtype=np.float32)
        out.append(last.copy())
    return out


def _face_area(lm: np.ndarray) -> float:
    xs, ys = lm[:, 0], lm[:, 1]
    return float((xs.max() - xs.min()) * (ys.max() - ys.min()))


def align_frames_and_landmarks(
    frames: list[np.ndarray],
    landmarks: list[np.ndarray | None],
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Forward/backward-fill 68-d landmarks so crop pipelines see a dense sequence."""
    filled: list[np.ndarray | None] = list(landmarks[: len(frames)])
    last: np.ndarray | None = None
    for i, lm in enumerate(filled):
        if lm is not None:
            last = lm
        elif last is not None:
            filled[i] = last.copy()
    last = None
    for i in range(len(filled) - 1, -1, -1):
        if filled[i] is not None:
            last = filled[i]
        elif last is not None:
            filled[i] = last.copy()
    keep_frames: list[np.ndarray] = []
    keep_lms: list[np.ndarray] = []
    for frame, lm in zip(frames, filled):
        if lm is None:
            continue
        keep_frames.append(frame)
        keep_lms.append(lm)
    if not keep_lms:
        raise RuntimeError("no face landmarks in this video")
    return keep_frames, keep_lms


def load_py_module(path: Path, name: str) -> ModuleType:
    if not path.is_file():
        print(f"ERROR: official file missing: {path}", file=sys.stderr)
        raise SystemExit(6)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        print(f"ERROR: cannot load {path}", file=sys.stderr)
        raise SystemExit(6)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clip_starts(n_frames: int, frames_per_clip: int, max_frames: int) -> list[int]:
    n = min(n_frames, max_frames)
    n_clips = n // frames_per_clip
    return [i * frames_per_clip for i in range(n_clips)]


def crop_mouths_lipforensics(
    frames: list[np.ndarray],
    landmarks: list[np.ndarray],
    repo_dir: Path,
) -> list[np.ndarray]:
    """Align + crop 96x96 mouths using official preprocessing/utils.py."""
    require_module("skimage", SKIMAGE_HINT)
    prep = load_py_module(repo_dir / "preprocessing" / "utils.py", "lf_prep_utils")
    mean_path = repo_dir / "preprocessing" / "20words_mean_face.npy"
    if not mean_path.is_file():
        print(f"ERROR: missing mean face {mean_path}", file=sys.stderr)
        raise SystemExit(6)
    mean_face = np.load(str(mean_path))
    stable = [33, 36, 39, 42, 45]
    std_size = (256, 256)
    window = 12
    start_idx, stop_idx = 48, 68
    half_h, half_w = 48, 48
    mouths: list[np.ndarray] = []
    trans = None
    n = min(len(frames), len(landmarks))
    for i in range(n):
        lo = max(0, i - window // 2)
        hi = min(n, i + window // 2 + 1)
        smoothed = np.mean(landmarks[lo:hi], axis=0)
        try:
            warped, trans = prep.warp_img(
                smoothed[stable, :], mean_face[stable, :], frames[i], std_size
            )
            trans_lm = trans(landmarks[i])
            crop = prep.cut_patch(warped, trans_lm[start_idx:stop_idx], half_h, half_w)
        except Exception:
            if trans is None:
                continue
            try:
                warped = prep.apply_transform(trans, frames[i], std_size)
                trans_lm = trans(landmarks[i])
                crop = prep.cut_patch(warped, trans_lm[start_idx:stop_idx], half_h, half_w)
            except Exception:
                continue
        if crop.ndim == 3:
            crop = (
                0.299 * crop[:, :, 0] + 0.587 * crop[:, :, 1] + 0.114 * crop[:, :, 2]
            ).astype(np.uint8)
        mouths.append(crop.astype(np.uint8))
    return mouths


class _RFCropArgs:
    window_margin = 12
    start_idx = 15
    stop_idx = 68
    crop_height = 150
    crop_width = 150


def crop_faces_realforensics(
    frames: list[np.ndarray],
    landmarks: list[np.ndarray],
    repo_dir: Path,
) -> list[np.ndarray]:
    """150x150 aligned faces using official preprocessing/extract_faces.py."""
    require_module("cv2", OPENCV_HINT)
    extract = load_py_module(
        repo_dir / "preprocessing" / "extract_faces.py", "rf_extract_faces"
    )
    mean_path = repo_dir / "preprocessing" / "20words_mean_face.npy"
    if not mean_path.is_file():
        print(f"ERROR: missing mean face {mean_path}", file=sys.stderr)
        raise SystemExit(6)
    reference = np.load(str(mean_path))
    lm_arr = np.stack(landmarks[: len(frames)], axis=0)
    try:
        sequence = extract.crop_patch(frames[: len(lm_arr)], lm_arr, reference, _RFCropArgs())
    except Exception as exc:
        raise RuntimeError(f"RealForensics face crop failed: {exc}") from exc
    return [np.asarray(frame) for frame in sequence]


def ensure_src_on_path() -> None:
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
