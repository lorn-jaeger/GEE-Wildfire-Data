"""Helpers for interacting with the filesystem."""

from __future__ import annotations

from pathlib import Path

from ..context import PipelineContext

__all__ = ["dataset_output_dir"]


def dataset_output_dir(context: PipelineContext, stage: str, dataset_name: str) -> Path:
    """Return a directory for storing outputs related to a dataset."""

    if stage in {"index", "earthengine"}:
        root = context.raw_path
    else:
        root = context.processed_path

    output = root / stage / dataset_name
    output.mkdir(parents=True, exist_ok=True)
    return output
