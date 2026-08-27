"""Shared adapter utilities."""

from __future__ import annotations

import shlex
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.video_eval.schema import ResultRecord, data_missing_record


class _SafeFormat(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class BaseAdapter(ABC):
    name: str

    @staticmethod
    def format_cmd(template: str, **kwargs: Any) -> list[str]:
        rendered = template.format_map(_SafeFormat(**kwargs))
        return shlex.split(rendered)

    @staticmethod
    def weights_file(model_cfg: dict[str, Any], default_name: str) -> str:
        if model_cfg.get("weights_file"):
            return str(model_cfg["weights_file"])
        return str(Path(model_cfg["weights_dir"]) / default_name)

    def dataset_path(self, manifest: dict[str, Any], key: str) -> Path | None:
        entry = manifest.get("datasets", {}).get(key)
        if not entry:
            return None
        path = Path(entry["path"])
        if not path.exists():
            return None
        return path

    def git_commit(self, repo_dir: str | Path) -> str | None:
        repo = Path(repo_dir)
        if not (repo / ".git").exists():
            return None
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode != 0:
            return None
        return out.stdout.strip()

    def missing(
        self,
        *,
        track: str,
        train_domain: str,
        test_set: str,
        compression: str,
        granularity: str = "video",
        metric: str = "auc",
        notes: str = "data_missing",
    ) -> ResultRecord:
        return data_missing_record(
            track=track,
            model=self.name,
            train_domain=train_domain,
            test_set=test_set,
            compression=compression,
            granularity=granularity,
            metric=metric,
            notes=notes,
        )

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
