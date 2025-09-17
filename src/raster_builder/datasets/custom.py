"""Helpers for dynamically loading custom dataset callables."""

from __future__ import annotations

import importlib
from typing import Callable

__all__ = ["resolve_custom_callable"]


def resolve_custom_callable(path: str) -> Callable[..., object]:
    """Load a function from a ``module:function`` style string."""
    if ":" in path:
        module_name, attr = path.split(":", 1)
    elif "." in path:
        module_name, attr = path.rsplit(".", 1)
    else:
        raise ValueError(
            "Custom dataset function must be provided as 'module:function' or dotted path"
        )

    module = importlib.import_module(module_name)
    try:
        func = getattr(module, attr)
    except AttributeError as exc:
        raise AttributeError(f"Module '{module_name}' has no attribute '{attr}'") from exc

    if not callable(func):
        raise TypeError(f"Resolved object '{path}' is not callable")

    return func

