from __future__ import annotations

from pathlib import Path
from typing import Any

from src.video_eval.adapters.base import BaseAdapter
from src.video_eval.dataset_io import runner_smoke_limit, uses_custom_raw_runner
from src.video_eval.parse import parse_auc_lines, parse_score_csv
from src.video_eval.schema import ResultRecord

# Official evaluate.py --dataset choices (never use CelebDF for mentor keys).
TEST_SET_FLAGS = {
    "celebdf_v2": "CelebDF",
    "dfdc": "DFDC",
    "dfdc_preview": "DFDC",
    "faceshifter": "FaceShifter",
    "deeperforensics": "DeeperForensics",
    "ffpp": "FaceForensics++",
}

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RUNNER = _REPO_ROOT / "scripts" / "lipforensics_dataset_eval.py"
_RAW_TEMPLATE = (
    "{python} {runner} --repo-dir {repo_dir} --weights {weights_file} "
    "--dataset-dir {dataset_dir} --out-dir {output_dir} "
    "--dataset-name {test_set} --smoke-limit {smoke_limit} --device {device}"
)


class LipForensicsAdapter(BaseAdapter):
    """Wraps ahaliassos/LipForensics ``evaluate.py`` or the raw-video runner.

    Official example::

        python evaluate.py --dataset FaceShifter --weights_forgery ./models/weights/lipforensics_ff.pth

    Mentor / real+fake dirs use ``scripts/lipforensics_dataset_eval.py`` so
    parse.py never labels the set as CelebDF.
    """

    name = "lipforensics"

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
        if uses_custom_raw_runner(test_set, extra):
            output_dir = extra.get("output_dir") or str(
                Path(cfg.get("results_dir", "results")) / "lipforensics" / test_set
            )
            template = model_cfg.get("raw_eval_command", _RAW_TEMPLATE)
            return self.format_cmd(
                template,
                python=model_cfg.get("python", "python"),
                runner=str(_RUNNER.as_posix()),
                repo_dir=model_cfg["repo_dir"],
                weights_file=self.weights_file(model_cfg, "lipforensics_ff.pth"),
                weights_dir=model_cfg.get("weights_dir", ""),
                dataset_dir=extra.get("dataset_dir", ""),
                output_dir=output_dir,
                test_set=test_set,
                smoke_limit=runner_smoke_limit(test_set, smoke=smoke, cfg=cfg),
                device=cfg.get("gpu", "cuda:0"),
            )
        template = model_cfg.get(
            "eval_command",
            "{python} evaluate.py --dataset {dataset_flag} "
            "--weights_forgery {weights_file} --compression {compression}",
        )
        return self.format_cmd(
            template,
            python=model_cfg.get("python", "python"),
            dataset_flag=TEST_SET_FLAGS.get(test_set, test_set),
            weights_file=self.weights_file(model_cfg, "lipforensics_ff.pth"),
            weights_dir=model_cfg["weights_dir"],
            repo_dir=model_cfg["repo_dir"],
            compression=cfg.get("default_compression", "c23"),
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
        commit = self.git_commit(model_cfg["repo_dir"])
        notes = ""
        if test_set == "dfdc_preview":
            notes = "test_set 为 preview，不是全量 DFDC。"
        if str(test_set).startswith("mentor_swap_200"):
            notes = "mentor custom raw-video set; not Celeb-DF / FF++ / DFDC."
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
        score_file = (extra or {}).get("score_file")
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
                    notes="official stdout had no AUC; keep log and score files",
                    commit=commit,
                    extra={"stdout_tail": stdout[-2000:]},
                )
            ]
        return records
