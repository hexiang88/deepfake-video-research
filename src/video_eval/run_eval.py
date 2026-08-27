"""CLI: wrap official model eval and write per-track JSON. Never merge tracks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.video_eval.adapters import get_adapter
from src.video_eval.adapters.base import BaseAdapter
from src.video_eval.schema import ResultRecord, TRACK_FILES, append_results


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("PyYAML is required: pip install -r requirements.txt") from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} is not a YAML mapping")
    return data


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_test_set(test_set: str, manifest: dict[str, Any]) -> str:
    datasets = manifest.get("datasets", {})
    if test_set == "dfdc":
        entry = datasets.get("dfdc", {})
        if entry.get("preview_only") or (
            "dfdc_preview" in datasets and not Path(entry.get("path", "")).exists()
        ):
            if "dfdc_preview" in datasets:
                return "dfdc_preview"
    return test_set


def dataset_exists(manifest: dict[str, Any], key: str) -> bool:
    entry = manifest.get("datasets", {}).get(key)
    if not entry or not entry.get("path"):
        return False
    return Path(entry["path"]).exists()


def dataset_dir(manifest: dict[str, Any], key: str) -> str:
    entry = manifest.get("datasets", {}).get(key) or {}
    return str(entry.get("path", ""))


def remap_preview(records: list[ResultRecord], requested: str) -> None:
    if requested != "dfdc_preview":
        return
    for rec in records:
        if rec.test_set == "dfdc":
            rec.test_set = "dfdc_preview"
        if "preview" not in rec.notes:
            rec.notes = (rec.notes + " test_set 为 preview，不是全量 DFDC.").strip()


def plan_jobs(
    cfg: dict[str, Any],
    model_cfg: dict[str, Any],
    *,
    track: str,
    manifest: dict[str, Any],
    smoke: bool,
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    if track == "cross_manipulation":
        for manip in model_cfg.get("manipulations", []):
            jobs.append(
                {
                    "test_set": manip,
                    "manifest_key": "ffpp",
                    "extra": {"manipulation": manip, "granularity": "video"},
                }
            )
        return jobs
    test_sets = list(model_cfg.get("test_sets", []))
    if smoke:
        test_sets = test_sets[:1]
    eval_once = bool(model_cfg.get("eval_once", False))
    if eval_once and any(str(name).startswith("mentor_swap_200") for name in test_sets):
        # Official RealForensics eval.py has no --dataset-dir; mentor keys must loop.
        eval_once = False
    if eval_once:
        jobs.append(
            {
                "test_set": test_sets[0] if test_sets else "unknown",
                "manifest_keys": test_sets,
                "eval_once": True,
                "extra": {
                    "granularity": "frame" if track == "vlaforge_frame" else "video",
                    "all_test_sets": test_sets,
                },
            }
        )
        return jobs
    for name in test_sets:
        reported = resolve_test_set(name, manifest)
        jobs.append(
            {
                "test_set": reported,
                "manifest_key": reported,
                "extra": {
                    "granularity": "frame" if track == "vlaforge_frame" else "video"
                },
            }
        )
    return jobs


def execute_job(
    adapter: BaseAdapter,
    cfg: dict[str, Any],
    model_cfg: dict[str, Any],
    job: dict[str, Any],
    *,
    track: str,
    smoke: bool,
    dry_run: bool,
    results_dir: Path,
) -> list[ResultRecord]:
    extra = dict(job.get("extra") or {})
    test_set = job["test_set"]
    compression = cfg.get("default_compression", "c23")
    train_domain = cfg.get("train_domain", "ffpp_c23")
    granularity = extra.get("granularity", "video")
    miss_metric = "ap@0.5" if track == "tfl" else "auc"
    if track in {"talking_face", "tfl"}:
        compression = str(model_cfg.get("compression", "n/a"))
        train_domain = str(model_cfg.get("train_domain", train_domain))
    manifest = cfg["_manifest"]

    missing_keys: list[str] = []
    if job.get("eval_once"):
        for key in job.get("manifest_keys", []):
            resolved = resolve_test_set(key, manifest)
            if not dataset_exists(manifest, resolved):
                print(f"SKIP data_missing: {resolved}", file=sys.stderr)
                missing_keys.append(resolved)
        present = [
            resolve_test_set(k, manifest)
            for k in job.get("manifest_keys", [])
            if dataset_exists(manifest, resolve_test_set(k, manifest))
        ]
        extra["dataset_dir"] = dataset_dir(manifest, present[0]) if present else ""
    else:
        key = job["manifest_key"]
        if not dataset_exists(manifest, key):
            print(f"SKIP data_missing: {key}", file=sys.stderr)
            rec = adapter.missing(
                track=track,
                train_domain=train_domain,
                test_set=test_set,
                compression=compression,
                granularity=granularity,
                metric=miss_metric,
            )
            rec.notes = f"data_missing: {key} path is absent or not applied"
            return [rec]
        extra["dataset_dir"] = dataset_dir(manifest, key)

    extra["output_dir"] = str(results_dir / "logs" / adapter.name / track / test_set)
    extra["score_file"] = str(Path(extra["output_dir"]) / "scores.csv")
    extra["smoke_limit"] = cfg.get("smoke_limit", 16) if smoke else 0

    require_all = bool(model_cfg.get("require_all_datasets"))
    blocked = bool(job.get("eval_once")) and (
        not extra.get("dataset_dir") or (require_all and missing_keys)
    )
    if blocked and not dry_run:
        names = list(job.get("manifest_keys") or [test_set])
        records = []
        for name in names:
            rec = adapter.missing(
                track=track,
                train_domain=train_domain,
                test_set=name,
                compression=compression,
                granularity=granularity,
                metric=miss_metric,
            )
            rec.notes = (
                f"data_missing: {name}; official eval needs datasets "
                f"{job.get('manifest_keys') or [test_set]}"
            )
            records.append(rec)
        return records

    cmd = adapter.build_command(
        cfg, model_cfg, track=track, test_set=test_set, smoke=smoke, extra=extra
    )
    workdir = model_cfg.get("workdir", model_cfg["repo_dir"])
    if model_cfg.get("eval_cwd") == "workspace":
        workdir = str(Path.cwd())

    print("CMD:", " ".join(cmd), file=sys.stderr)
    if dry_run:
        missing_records = [
            adapter.missing(
                track=track,
                train_domain=train_domain,
                test_set=name,
                compression=compression,
                granularity=granularity,
                metric=miss_metric,
            )
            for name in missing_keys
        ]
        for rec in missing_records:
            rec.notes = f"dry-run; data_missing: {rec.test_set}"
        return missing_records

    if job.get("eval_once") and not extra.get("dataset_dir"):
        return [
            adapter.missing(
                track=track,
                train_domain=train_domain,
                test_set=name,
                compression=compression,
                granularity=granularity,
                metric=miss_metric,
            )
            for name in (job.get("manifest_keys") or [test_set])
        ]

    log_path = Path(extra["output_dir"]) / "eval.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        cmd,
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = (proc.stdout or "") + "\n--- stderr ---\n" + (proc.stderr or "")
    log_path.write_text(combined, encoding="utf-8")
    records = adapter.parse(
        combined,
        cfg=cfg,
        model_cfg=model_cfg,
        track=track,
        test_set=test_set,
        extra=extra,
    )
    if any(
        resolve_test_set(k, manifest) == "dfdc_preview"
        for k in job.get("manifest_keys", [test_set])
    ):
        remap_preview(records, "dfdc_preview")
    else:
        remap_preview(records, test_set)
    records = [rec for rec in records if rec.test_set not in set(missing_keys)]
    if proc.returncode != 0:
        for rec in records:
            if rec.value is None:
                rec.status = "eval_failed"
            rec.extra["returncode"] = proc.returncode
            rec.extra["log"] = str(log_path)
    if missing_keys:
        for name in missing_keys:
            miss = adapter.missing(
                track=track,
                train_domain=train_domain,
                test_set=name,
                compression=compression,
                granularity=granularity,
                metric=miss_metric,
            )
            miss.notes = f"data_missing: {name} path is absent or not applied"
            records.append(miss)
    return records


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run official video-eval entrypoints and write per-track JSON."
    )
    parser.add_argument("--config", required=True, help="Path to video_eval.yaml")
    parser.add_argument(
        "--track",
        required=True,
        choices=sorted(TRACK_FILES),
        help="One track per run; files are never merged.",
    )
    parser.add_argument("--model", required=True, help="Adapter name, e.g. lipforensics")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Limit to smoke_limit videos / first test set.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands only; do not write JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = load_yaml(Path(args.config))
    manifest_path = Path(cfg.get("manifest", "configs/datasets.manifest.json"))
    if not manifest_path.exists():
        raise SystemExit(
            f"missing {manifest_path}; copy configs/datasets.manifest.example.json"
        )
    cfg["_manifest"] = load_manifest(manifest_path)
    if args.model not in cfg.get("models", {}):
        raise SystemExit(f"model {args.model} not in {args.config}")
    model_cfg = cfg["models"][args.model]
    allowed = model_cfg.get("tracks", [])
    if args.track not in allowed:
        raise SystemExit(f"{args.model} is not registered for track {args.track}")
    results_dir = Path(cfg.get("results_dir", "results"))
    adapter = get_adapter(args.model)
    jobs = plan_jobs(
        cfg, model_cfg, track=args.track, manifest=cfg["_manifest"], smoke=args.smoke
    )
    records: list[ResultRecord] = []
    for job in jobs:
        records.extend(
            execute_job(
                adapter,
                cfg,
                model_cfg,
                job,
                track=args.track,
                smoke=args.smoke,
                dry_run=args.dry_run,
                results_dir=results_dir,
            )
        )
    if args.dry_run:
        return 0
    if not records:
        print("no records to write", file=sys.stderr)
        return 1
    path = append_results(results_dir, records)
    print(f"wrote {path} ({len(records)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
