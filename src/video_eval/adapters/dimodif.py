"""Wrap mever-team/dimodif official ``scripts/eval.py`` (DFD + TFL + RVFA)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.video_eval.adapters.base import BaseAdapter
from src.video_eval.parse import parse_mever_result_json
from src.video_eval.schema import (
    DIMODIF_RVFA_NOTE,
    TALKING_FACE_LIPSYNC_NOTE,
    ResultRecord,
)

_DEFAULT_CMD = "{python} scripts/eval.py"

_DFD_JSON = (
    "results/generalization/dfd_fakeavceleb.json",
    "results/generalization/dfd_lavdf.json",
    "results/generalization/dfd_avdeepfake1m.json",
)
_TFL_JSON = (
    "results/generalization/tfl_lavdf.json",
    "results/generalization/tfl_avdeepfake1m.json",
)


class DiMoDifAdapter(BaseAdapter):
    """Official DiMoDif eval: in-dataset DFD, FakeAVCeleb cross-manip (keep RVFA), TFL.

    ``scripts/eval.py`` hardcodes ``device = cuda:0``. Keep yaml ``gpu: cuda:0``.
    Do not treat wav2lip / MyDataSets generator folders as FakeAVCeleb.
    """

    name = "dimodif"

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
                DIMODIF_RVFA_NOTE,
                "DFD 与 TFL 分表。FakeAVCeleb 须官方划分与 RVFA/FV 标签；candidate 目录不得写成 verified。",
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
                train_domain="fakeavceleb",
                test_set=test_set,
                compression="n/a",
                granularity="video",
                metric="ap@0.5" if track == "tfl" else "auc",
                value=None,
                status="parse_failed",
                notes=notes + " official results/generalization JSON missing after scripts/eval.py",
                commit=commit,
                extra={"stdout_tail": stdout[-2000:]},
            )
        ]
