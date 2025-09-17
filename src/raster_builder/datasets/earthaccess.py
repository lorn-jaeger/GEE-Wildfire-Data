"""Placeholders for NASA earthaccess dataset implementations."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from ..context import PipelineContext
from .registry import register_dataset

logger = logging.getLogger(__name__)


@register_dataset(source="earthaccess", name="example")
def earthaccess_example(context: PipelineContext, options: Mapping[str, Any]) -> None:
    """Demonstration placeholder that records configuration values."""

    logger.warning(
        "earthaccess example dataset is a placeholder and does not download data yet."
    )
    context.add_artifact("earthaccess_example", {"options": dict(options)})

