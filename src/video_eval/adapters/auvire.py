"""Wrap mever-team/auvire official ``scripts/test.py`` (DFD + TFL)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.video_eval.adapters.base import BaseAdapter
from src.video_eval.parse import parse_mever_result_json
from src.video_eval.schema import (
    AUVIRe_NO_FAKEAVCELEB_NOTE,
    TALKING_FACE_LIPSYNC_NOTE,
    ResultRecord,
)

_DEFAULT_CMD = "{python} scripts/test.py"

_DFD_JSON = (
    "results/test/task_dfd_training_on_lavdf.json",
    "results/test/task_dfd_training_on_avdeepfake1m.json",
)
_TFL_JSON = (
    "results/test/task_tfl_training_on_lavdf.json",
    "results/test/task_tfl_training_on_avdeepfake1m.json",
)


class AuViReAdapter(BaseAdapter):
    """Official AuViRe eval binds LAV-DF × AV-Deepfake1M only.

    There is no FakeAVCeleb protocol in the paper JSON. Do not invent that row.
    ``scripts/test.py`` hardcodes ``device = cuda:0`` (visible GPU after
    ``CUDA_VISIBLE_DEVICES``). Do not change yaml ``gpu: cuda:0``.
    """

    name = "auvire"

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
        template = model_cfg.get("eval_command", _DEFAULT_CMD)
        return self.format_cmd(
            template,
            python=model_cfg.get("python", "python"),
            repo_dir=model_cfg["repo_dir"],
            weights_dir=model_cfg.get("weights_dir", ""),
            test_set=test_set,
            track=track,
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
        repo = Path(model_cfg["repo_dir"])
        commit = self.git_commit(repo)
        notes = " ".join(
            [
                TALKING_FACE_LIPSYNC_NOTE,
                AUVIRe_NO_FAKEAVCELEB_NOTE,
                "DFD 与 TFL 分表；AV-Deepfake1M 本脚本评的是 validation，不是 Codabench test。",
            ]
        )
        json_names = _TFL_JSON if track == "tfl" else _DFD_JSON
        records: list[ResultRecord] = []
        for rel in json_names:
            path = repo / rel
            if not path.is_file():
                continue
            records.extend(
                parse_mever_result_json(
                    path,
                    track=track,
                    model=self.name,
                    compression="n/a",
                    granularity="video",
                    notes=notes,
                    commit=commit,
                    gpu=cfg.get("gpu"),
                )
            )
        if records:
            return records
        return [
            ResultRecord(
                track=track,
                model=self.name,
                train_domain="lav_df",
                test_set=test_set,
                compression="n/a",
                granularity="video",
                metric="ap@0.5" if track == "tfl" else "auc",
                value=None,
                status="parse_failed",
                notes=notes + " official results/test JSON missing after scripts/test.py",
                commit=commit,
                extra={"stdout_tail": stdout[-2000:]},
            )
        ]
