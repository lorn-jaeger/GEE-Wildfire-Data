"""High level orchestration for the refactored wildfire dataset pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from .config import DatasetEntry, PipelineConfig, load_config
from .context import PipelineContext
from .datasets import load_builtin_datasets, registry
from .datasets.custom import resolve_custom_callable
from .io.auth import authenticate_earth_engine, earthaccess_session

logger = logging.getLogger(__name__)


def _ensure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def _load_config(config_path: Path) -> PipelineConfig:
    _ensure_logging()
    config = load_config(config_path)
    logger.info("Loaded configuration from %s", config.config_path)
    return config


def _resolve_callable(entry: DatasetEntry) -> callable:
    if entry.function:
        return resolve_custom_callable(entry.function)
    return registry.get(source=entry.source, name=entry.name)


def _run_dataset(context: PipelineContext, stage: str, entry: DatasetEntry) -> None:
    func = _resolve_callable(entry)
    logger.info("Running %s dataset '%s'", stage, entry.name)
    func(context, entry.options)


def _run_stage(context: PipelineContext, stage: str, entries: Iterable[DatasetEntry]) -> None:
    for entry in entries:
        _run_dataset(context, stage, entry)


def run_pipeline(config_path: Path) -> PipelineContext:
    """Execute the configured pipeline and return the runtime context."""

    load_builtin_datasets()
    config = _load_config(config_path)
    context = PipelineContext(config=config)

    project_id = authenticate_earth_engine(config.credentials.earthengine_service_account)
    context.earth_engine_project = project_id

    context.earthaccess_session = earthaccess_session(config.credentials.earthaccess_netrc)

    index_entry = config.schema.index
    _run_dataset(context, "index", index_entry)

    _run_stage(context, "earthengine", config.schema.earthengine)
    _run_stage(context, "earthaccess", config.schema.earthaccess)
    _run_stage(context, "custom", config.schema.custom)

    logger.info("Pipeline completed successfully")
    return context

