"""Index dataset implementations."""

from __future__ import annotations

import logging
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Mapping

import geopandas as gpd

from ee_wildfire.UserInterface import ConsoleUI  # type: ignore
from ee_wildfire import globfire

from ..config import ConfigError
from ..context import PipelineContext
from ..io.storage import dataset_output_dir
from .registry import register_dataset

logger = logging.getLogger(__name__)


def _parse_datetime(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ConfigError(f"Invalid ISO datetime for '{field}': {value}") from exc
    raise ConfigError(f"Unsupported type for '{field}': {type(value).__name__}")


@register_dataset(source="index", name="globfire")
def load_globfire_index(context: PipelineContext, options: Mapping[str, Any]) -> gpd.GeoDataFrame:
    """Fetch GlobFire index data and attach it to the pipeline context."""

    start = _parse_datetime(options.get("start_date"), field="start_date")
    end = _parse_datetime(options.get("end_date"), field="end_date")
    if end < start:
        raise ConfigError("GlobFire end_date must be on or after start_date")

    min_size = float(options.get("min_size", 1e7))

    config = SimpleNamespace(start_date=start, end_date=end, min_size=min_size)

    # Suppress the verbose console output in the legacy module.
    previous_verbose = getattr(ConsoleUI, "_verbose", True)
    ConsoleUI.set_verbose(False)

    logger.info(
        "Querying GlobFire final perimeters from %s to %s (min_size=%s)",
        start.date(),
        end.date(),
        min_size,
    )
    try:
        gdf = globfire.get_fires(config)
    finally:
        ConsoleUI.set_verbose(previous_verbose)
    logger.info("Retrieved %d GlobFire fire records", len(gdf))

    output_dir = dataset_output_dir(context, stage="index", dataset_name="globfire")
    output_file = output_dir / "globfire_index.csv"

    df = gdf.copy()
    if "geometry" in df:
        geometry = df.geometry
        df = df.drop(columns=["geometry"])
        df["geometry_wkt"] = geometry.to_wkt()

    df.to_csv(output_file, index=False)
    logger.info("Saved GlobFire index CSV to %s", output_file)

    context.set_index(gdf, path=output_file)
    return gdf
