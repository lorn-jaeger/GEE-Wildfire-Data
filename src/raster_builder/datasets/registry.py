"""Dataset registry used to resolve dataset functions at runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Tuple

DatasetCallable = Callable[..., object]


@dataclass(frozen=True)
class DatasetKey:
    source: str
    name: str

    def normalized(self) -> "DatasetKey":
        return DatasetKey(self.source.lower(), self.name.lower())


class DatasetRegistry:
    """Stores dataset fetch functions keyed by (source, name)."""

    def __init__(self) -> None:
        self._datasets: Dict[Tuple[str, str], DatasetCallable] = {}

    def register(self, *, source: str, name: str, func: DatasetCallable) -> None:
        key = (source.lower(), name.lower())
        if key in self._datasets:
            raise ValueError(f"Dataset '{name}' for source '{source}' already registered")
        self._datasets[key] = func

    def get(self, *, source: str, name: str) -> DatasetCallable:
        key = (source.lower(), name.lower())
        try:
            return self._datasets[key]
        except KeyError as exc:
            raise KeyError(f"No dataset registered for source='{source}' name='{name}'") from exc

    def items(self) -> Iterable[Tuple[Tuple[str, str], DatasetCallable]]:
        return self._datasets.items()


registry = DatasetRegistry()


def register_dataset(*, source: str, name: str) -> Callable[[DatasetCallable], DatasetCallable]:
    """Decorator used by dataset modules to register fetch functions."""

    def decorator(func: DatasetCallable) -> DatasetCallable:
        registry.register(source=source, name=name, func=func)
        return func

    return decorator

