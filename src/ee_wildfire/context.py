"""Runtime context shared across pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .config import PipelineConfig

__all__ = ["PipelineContext"]


@dataclass
class PipelineContext:
    """Mutable state that dataset functions can use to coordinate work."""

    config: PipelineConfig
    index_data: Optional[Any] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    earth_engine_project: Optional[str] = None
    earthaccess_session: Optional[Any] = None

    @property
    def raw_path(self) -> Path:
        return self.config.paths.raw_data

    @property
    def processed_path(self) -> Path:
        return self.config.paths.processed_data

    @property
    def scratch_path(self) -> Path:
        assert self.config.paths.scratch is not None
        return self.config.paths.scratch

    @property
    def credentials(self) -> Dict[str, Path]:
        creds = {
            "earthengine_service_account": self.config.credentials.earthengine_service_account,
        }
        if self.config.credentials.earthaccess_netrc is not None:
            creds["earthaccess_netrc"] = self.config.credentials.earthaccess_netrc
        return creds

    def set_index(self, data: Any, **metadata: Any) -> None:
        """Store the index dataset result and optional metadata."""
        self.index_data = data
        if metadata:
            self.artifacts.setdefault("index", {}).update(metadata)

    def add_artifact(self, key: str, value: Any) -> None:
        self.artifacts[key] = value
