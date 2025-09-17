"""Configuration loading and validation utilities for the refactored pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

import yaml

__all__ = [
    "ConfigError",
    "CredentialsConfig",
    "PathsConfig",
    "DatasetEntry",
    "SchemaConfig",
    "PipelineConfig",
    "load_config",
]


class ConfigError(RuntimeError):
    """Raised when the user supplied configuration is invalid."""


@dataclass
class CredentialsConfig:
    """Stores credential locations used by the pipeline."""

    earthengine_service_account: Path
    earthaccess_netrc: Optional[Path] = None

    def expand(self, resolver: "PathResolver") -> "CredentialsConfig":
        self.earthengine_service_account = resolver.resolve_file(self.earthengine_service_account)
        if not self.earthengine_service_account.exists():
            raise ConfigError(
                f"Earth Engine service account file not found: {self.earthengine_service_account}"
            )

        if self.earthaccess_netrc is not None:
            resolved = resolver.resolve_file(self.earthaccess_netrc, must_exist=False)
            self.earthaccess_netrc = resolved

        return self


@dataclass
class PathsConfig:
    """Paths that the pipeline will use for storage."""

    raw_data: Path
    processed_data: Path
    scratch: Optional[Path] = None

    def expand(self, resolver: "PathResolver") -> "PathsConfig":
        self.raw_data = resolver.prepare_dir(self.raw_data)
        self.processed_data = resolver.prepare_dir(self.processed_data)

        if self.scratch is None:
            self.scratch = self.raw_data / "scratch"
        self.scratch = resolver.prepare_dir(self.scratch)

        return self


@dataclass
class DatasetEntry:
    """Represents one dataset declaration inside the schema."""

    name: str
    source: str
    options: Dict[str, Any] = field(default_factory=dict)
    function: Optional[str] = None

    @staticmethod
    def from_mapping(
        data: Mapping[str, Any],
        *,
        default_source: str,
        required_name: bool = True,
    ) -> "DatasetEntry":
        if "dataset" in data:
            name = str(data["dataset"])
        elif required_name and "name" in data:
            name = str(data["name"])
        elif required_name:
            raise ConfigError("Dataset entry missing 'dataset' field")
        else:
            name = data.get("name", default_source)

        source = str(data.get("source", default_source)).lower()
        options = dict(data.get("options", {}))
        function = data.get("function")
        if function is not None:
            function = str(function)
        return DatasetEntry(name=name, source=source, options=options, function=function)


@dataclass
class SchemaConfig:
    """Schema describing the datasets that compose the pipeline run."""

    index: DatasetEntry
    earthengine: List[DatasetEntry] = field(default_factory=list)
    earthaccess: List[DatasetEntry] = field(default_factory=list)
    custom: List[DatasetEntry] = field(default_factory=list)


@dataclass
class PipelineConfig:
    """Complete pipeline configuration loaded from YAML."""

    credentials: CredentialsConfig
    paths: PathsConfig
    schema: SchemaConfig
    config_path: Path


class PathResolver:
    """Resolve user provided paths relative to the config file."""

    def __init__(self, config_path: Path) -> None:
        self._config_dir = config_path.parent

    def _expand(self, path: Path) -> Path:
        if not path.is_absolute():
            path = self._config_dir / path
        return path.expanduser().resolve()

    def resolve_file(self, path: Path, *, must_exist: bool = True) -> Path:
        resolved = self._expand(Path(path))
        if must_exist and not resolved.exists():
            raise ConfigError(f"Expected file does not exist: {resolved}")
        return resolved

    def prepare_dir(self, path: Path) -> Path:
        resolved = self._expand(Path(path))
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved


def _require_section(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    try:
        section = data[key]
    except KeyError as exc:
        raise ConfigError(f"Missing required configuration section '{key}'") from exc
    if not isinstance(section, Mapping):
        raise ConfigError(f"Configuration section '{key}' must be a mapping")
    return section


def _load_dataset_list(
    nodes: Optional[Iterable[Mapping[str, Any]]],
    *,
    default_source: str,
) -> List[DatasetEntry]:
    if nodes is None:
        return []
    entries: List[DatasetEntry] = []
    for node in nodes:
        if not isinstance(node, Mapping):
            raise ConfigError(
                f"Dataset declaration must be a mapping, received {type(node).__name__}"
            )
        entries.append(DatasetEntry.from_mapping(node, default_source=default_source))
    return entries


def load_config(path: Path) -> PipelineConfig:
    """Load a pipeline configuration from a YAML file."""

    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, Mapping):
        raise ConfigError("Configuration file must contain a mapping at the top level")

    resolver = PathResolver(path)

    credentials_section = _require_section(data, "credentials")
    credentials = CredentialsConfig(
        earthengine_service_account=Path(credentials_section["earthengine_service_account"]),
        earthaccess_netrc=(
            Path(credentials_section["earthaccess_netrc"])
            if "earthaccess_netrc" in credentials_section
            else None
        ),
    ).expand(resolver)

    paths_section = _require_section(data, "paths")
    paths = PathsConfig(
        raw_data=Path(paths_section["raw_data"]),
        processed_data=Path(paths_section["processed_data"]),
        scratch=(
            Path(paths_section["scratch"])
            if "scratch" in paths_section
            else None
        ),
    ).expand(resolver)

    schema_section = _require_section(data, "schema")

    if "index" not in schema_section:
        raise ConfigError("Schema must include an 'index' dataset")
    index_cfg_raw = schema_section["index"]
    if not isinstance(index_cfg_raw, Mapping):
        raise ConfigError("Schema 'index' entry must be a mapping")
    index_entry = DatasetEntry.from_mapping(
        index_cfg_raw,
        default_source="index",
        required_name=True,
    )

    earthengine_entries = _load_dataset_list(
        schema_section.get("earthengine"),
        default_source="earthengine",
    )
    earthaccess_entries = _load_dataset_list(
        schema_section.get("earthaccess"),
        default_source="earthaccess",
    )
    custom_entries = _load_dataset_list(
        schema_section.get("custom"),
        default_source="custom",
    )

    schema = SchemaConfig(
        index=index_entry,
        earthengine=earthengine_entries,
        earthaccess=earthaccess_entries,
        custom=custom_entries,
    )

    return PipelineConfig(
        credentials=credentials,
        paths=paths,
        schema=schema,
        config_path=path,
    )
