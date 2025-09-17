"""Dataset registry and built-in dataset registrations."""

from __future__ import annotations

from importlib import import_module
from typing import Callable, Optional

from .registry import DatasetCallable, DatasetRegistry, register_dataset, registry

__all__ = [
    "DatasetCallable",
    "DatasetRegistry",
    "registry",
    "register_dataset",
    "load_builtin_datasets",
]


def load_builtin_datasets() -> None:
    """Ensure built-in dataset modules are imported so their registrations run."""
    modules = [
        "raster_builder.datasets.index",
        "raster_builder.datasets.earthengine",
        "raster_builder.datasets.earthaccess",
        "raster_builder.datasets.custom",
    ]
    for module in modules:
        import_module(module)
