from __future__ import annotations

from pathlib import Path
from typing import Any

from src.video_eval.adapters.base import BaseAdapter
from src.video_eval.parse import parse_auc_lines, parse_score_csv
from src.video_eval.schema import ResultRecord

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RUNNER = _REPO_ROOT / "scripts" / "pwtf_dvd_dataset_eval.py"


class PwtfDvdAdapter(BaseAdapter):
    """Wraps rama0126/PwTF-DVD official per-video inference.

    README entry::

        python inference/test_on_raw_video.py --video VIDEO --out_dir OUT --model_path WEIGHTS

    Default ``eval_command`` loops that script over a dataset directory via
    ``scripts/pwtf_dvd_dataset_eval.py``, then prints video-level AUC.
    Cross-dataset JSON is also the temporal track; do not merge FTCN.
    """

    name = "pwtf_dvd"

    def build_command(
        self,
        cfg: dict[str, Any],
        model_cfg: dict[str, Any],
        *,
        track: str,
        test_set: str,
        smoke: bool,
        extra: dict[str, Any] | None = None,
    ) -> list[str]:
        extra = extra or {}
        template = model_cfg.get(
            "eval_command",
            "{python} {runner} --repo-dir {repo_dir} --weights {weights_file} "
            "--dataset-dir {dataset_dir} --out-dir {output_dir} "
            "--dataset-name {test_set} --smoke-limit {smoke_limit}",
        )
        output_dir = extra.get("output_dir") or str(
            Path(cfg.get("results_dir", "results")) / "pwtf_dvd" / test_set
        )
        return self.format_cmd(
            template,
            python=model_cfg.get("python", "python"),
            runner=str(_RUNNER),
            repo_dir=model_cfg["repo_dir"],
            weights_file=self.weights_file(model_cfg, "pwtf_dvd.pth"),
            weights_dir=model_cfg["weights_dir"],
            dataset_dir=extra.get("dataset_dir", ""),
            output_dir=output_dir,
            test_set=test_set,
            smoke_limit=cfg.get("smoke_limit", 16) if smoke else 0,
        )

    def parse(
        self,
        stdout: str,
        *,
        cfg: dict[str, Any],
        model_cfg: dict[str, Any],
        track: str,
        test_set: str,
        extra: dict[str, Any] | None = None,
    ) -> list[ResultRecord]:
        extra = extra or {}
        commit = self.git_commit(model_cfg["repo_dir"])
        notes = "时序赛道与跨数据集共用本结果，不与 FTCN 混表。"
        if test_set == "dfdc_preview":
            notes += " test_set 为 preview，不是全量 DFDC。"
        records = parse_auc_lines(
            stdout,
            track=track,
            model=self.name,
            train_domain=cfg.get("train_domain", "ffpp_c23"),
            compression=cfg.get("default_compression", "c23"),
            granularity="video",
            default_test_set=test_set,
            notes=notes,
            commit=commit,
            gpu=cfg.get("gpu"),
        )
        score_file = extra.get("score_file")
        if not records and score_file and Path(score_file).exists():
            records = parse_score_csv(
                Path(score_file),
                track=track,
                model=self.name,
                train_domain=cfg.get("train_domain", "ffpp_c23"),
                test_set=test_set,
                compression=cfg.get("default_compression", "c23"),
                granularity="video",
                notes=notes,
                commit=commit,
                gpu=cfg.get("gpu"),
            )
        if not records:
            records = [
                ResultRecord(
                    track=track,
                    model=self.name,
                    train_domain=cfg.get("train_domain", "ffpp_c23"),
                    test_set=test_set,
                    compression=cfg.get("default_compression", "c23"),
                    granularity="video",
                    metric="auc",
                    value=None,
                    status="parse_failed",
                    notes=notes,
                    commit=commit,
                    extra={"stdout_tail": stdout[-2000:]},
                )
            ]
        return records
