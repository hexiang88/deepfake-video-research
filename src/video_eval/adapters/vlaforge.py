from __future__ import annotations

from typing import Any

from src.video_eval.adapters.base import BaseAdapter
from src.video_eval.parse import parse_auc_lines
from src.video_eval.schema import ResultRecord

# Names used in official config/test.yaml test_dataset list.
TEST_SET_FLAGS = {
    "celebdf_v2": "Celeb-DF-v2",
    "dfdc": "DFDC",
    "dfdc_preview": "DFDCP",
    "faceshifter": "FaceShifter",
    "deeperforensics": "DeeperForensics",
    "dfd": "DeepFakeDetection",
}


class VlaforgeAdapter(BaseAdapter):
    """Wraps mala-lab/VLAForge official ``bash test.sh``.

    Video-level scores (frame-mean) go to ``cross_dataset.json``.
    Frame-level AUROC goes to ``vlaforge_frame.json`` only.
    Set ``test_dataset`` in the cloned ``config/test.yaml``, or override
    ``eval_command`` / ``frame_command`` after reading the local README.
    """

    name = "vlaforge"

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
        granularity = extra.get(
            "granularity", "frame" if track == "vlaforge_frame" else "video"
        )
        if track == "vlaforge_frame" or granularity == "frame":
            template = model_cfg.get("frame_command", "bash test.sh")
        else:
            template = model_cfg.get("eval_command", "bash test.sh")
        return self.format_cmd(
            template,
            python=model_cfg.get("python", "python"),
            dataset_flag=TEST_SET_FLAGS.get(test_set, test_set),
            weights_file=self.weights_file(model_cfg, "vlaforge.pth"),
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
        granularity = extra.get(
            "granularity", "frame" if track == "vlaforge_frame" else "video"
        )
        metric = "auroc" if granularity == "frame" else "auc"
        notes = ""
        if granularity == "video":
            notes = "视频级分数为帧级平均。"
        if test_set == "dfdc_preview":
            notes = (notes + " test_set 为 preview，不是全量 DFDC。").strip()
        records = parse_auc_lines(
            stdout,
            track=track,
            model=self.name,
            train_domain=cfg.get("train_domain", "ffpp_c23"),
            compression=cfg.get("default_compression", "c23"),
            granularity=granularity,
            default_test_set=test_set,
            notes=notes,
            commit=commit,
            gpu=cfg.get("gpu"),
            metric=metric,
        )
        if not records:
            records = [
                ResultRecord(
                    track=track,
                    model=self.name,
                    train_domain=cfg.get("train_domain", "ffpp_c23"),
                    test_set=test_set,
                    compression=cfg.get("default_compression", "c23"),
                    granularity=granularity,
                    metric=metric,
                    value=None,
                    status="parse_failed",
                    notes=notes or "official stdout had no AUC",
                    commit=commit,
                    extra={"stdout_tail": stdout[-2000:]},
                )
            ]
        return records
