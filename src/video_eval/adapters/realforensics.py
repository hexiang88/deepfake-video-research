from __future__ import annotations

from pathlib import Path
from typing import Any

from src.video_eval.adapters.base import BaseAdapter
from src.video_eval.dataset_io import runner_smoke_limit, uses_custom_raw_runner
from src.video_eval.parse import parse_auc_lines, parse_score_csv
from src.video_eval.schema import MANIPULATION_NOTES, ResultRecord

# Official stage2/eval.py uses hydra; one cross-dataset command covers Table 2.
MANIP_WEIGHTS = {
    "Deepfakes": "realforensics_allbutdf.pth",
    "FaceSwap": "realforensics_allbutfs.pth",
    "Face2Face": "realforensics_allbutf2f.pth",
    "NeuralTextures": "realforensics_allbutnt.pth",
}

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RUNNER = _REPO_ROOT / "scripts" / "realforensics_dataset_eval.py"
_RAW_TEMPLATE = (
    "{python} {runner} --repo-dir {repo_dir} --weights {weights_file} "
    "--dataset-dir {dataset_dir} --out-dir {output_dir} "
    "--dataset-name {test_set} --smoke-limit {smoke_limit} --device {device}"
)


def _resolved_weights(model_cfg: dict[str, Any], default_name: str) -> str:
    wf = str(model_cfg.get("weights_file") or default_name)
    if wf.startswith("/") or (len(wf) > 1 and wf[1] == ":"):
        return wf
    weights_dir = model_cfg.get("weights_dir")
    if weights_dir:
        return str(Path(weights_dir) / wf)
    return str(Path(model_cfg["repo_dir"]) / "stage2" / "weights" / wf)


class RealForensicsAdapter(BaseAdapter):
    """Wraps ahaliassos/RealForensics ``stage2/eval.py`` or the raw-video runner.

    Cross-dataset (README)::

        python stage2/eval.py model.weights_filename=realforensics_ff.pth

    Cross-manipulation leave-one-out (README)::

        python stage2/eval.py model.weights_filename=realforensics_allbutdf.pth

    Mentor / real+fake dirs use ``scripts/realforensics_dataset_eval.py``.
    Set ``eval_once: false`` when test_sets are mentor keys.
    """

    name = "realforensics"

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
        python = model_cfg.get("python", "python")
        if track == "cross_manipulation":
            manip = extra.get("manipulation", test_set)
            weights_map = {**MANIP_WEIGHTS, **model_cfg.get("manip_weights", {})}
            weights_file = weights_map.get(manip, f"realforensics_allbut{manip.lower()}.pth")
            template = model_cfg.get(
                "manip_command",
                "{python} stage2/eval.py model.weights_filename={weights_file}",
            )
            return self.format_cmd(
                template,
                python=python,
                weights_file=weights_file,
                weights_dir=model_cfg["weights_dir"],
                repo_dir=model_cfg["repo_dir"],
                manipulation=manip,
            )
        if uses_custom_raw_runner(test_set, extra):
            output_dir = extra.get("output_dir") or str(
                Path(cfg.get("results_dir", "results")) / "realforensics" / test_set
            )
            template = model_cfg.get("raw_eval_command", _RAW_TEMPLATE)
            return self.format_cmd(
                template,
                python=python,
                runner=str(_RUNNER.as_posix()),
                repo_dir=model_cfg["repo_dir"],
                weights_file=_resolved_weights(model_cfg, "realforensics_ff.pth"),
                weights_dir=model_cfg.get("weights_dir", ""),
                dataset_dir=extra.get("dataset_dir", ""),
                output_dir=output_dir,
                test_set=test_set,
                smoke_limit=runner_smoke_limit(test_set, smoke=smoke, cfg=cfg),
                device=cfg.get("gpu", "cuda:0"),
            )
        template = model_cfg.get(
            "eval_command",
            "{python} stage2/eval.py model.weights_filename={weights_file}",
        )
        return self.format_cmd(
            template,
            python=python,
            weights_file=model_cfg.get("weights_file", "realforensics_ff.pth"),
            weights_dir=model_cfg["weights_dir"],
            repo_dir=model_cfg["repo_dir"],
            test_set=test_set,
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
        notes = ""
        if track == "cross_manipulation":
            manip = extra.get("manipulation", test_set)
            notes = MANIPULATION_NOTES.get(manip, "")
            test_set = manip
        elif test_set == "dfdc_preview":
            notes = "test_set 为 preview，不是全量 DFDC。"
        elif str(test_set).startswith("mentor_swap_200"):
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
        if track == "cross_manipulation":
            for rec in records:
                rec.notes = notes
                rec.test_set = extra.get("manipulation", rec.test_set)
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
                    notes=notes or "official stdout had no AUC",
                    commit=commit,
                    extra={"stdout_tail": stdout[-2000:]},
                )
            ]
        return records
