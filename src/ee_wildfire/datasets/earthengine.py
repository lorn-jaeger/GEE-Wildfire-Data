"""Placeholders for Earth Engine dataset implementations."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from ..context import PipelineContext
from .registry import register_dataset

logger = logging.getLogger(__name__)


@register_dataset(source="earthengine", name="firepred_daily")
def firepred_daily(context: PipelineContext, options: Mapping[str, Any]) -> None:
    """Placeholder for the FirePred daily export pipeline.

    The legacy implementation exported imagery to Google Drive and then downloaded TIFFs.
    That logic will be adapted to the new pipeline in a follow-up change.
    """

    logger.warning(
        "firepred_daily dataset is not yet implemented in the refactored pipeline."
    )
    context.add_artifact("firepred_daily", {"status": "not-implemented"})

