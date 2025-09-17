"""Authentication helpers for Google Earth Engine and earthaccess."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import ee  # type: ignore

logger = logging.getLogger(__name__)


def authenticate_earth_engine(service_account_path: Path) -> str:
    """Authenticate the Earth Engine client using a service account JSON file."""
    with service_account_path.open("r", encoding="utf-8") as handle:
        info = json.load(handle)

    email = info.get("client_email")
    if not email:
        raise ValueError("Service account JSON missing 'client_email'")

    credentials = ee.ServiceAccountCredentials(email=email, key_file=str(service_account_path))
    ee.Initialize(credentials=credentials)
    project_id = info.get("project_id", "unknown-project")
    logger.info("Authenticated Earth Engine project '%s'", project_id)
    return str(project_id)


def earthaccess_session(netrc_path: Optional[Path]) -> Optional[Any]:
    """Return an authenticated earthaccess session if credentials are supplied."""
    if netrc_path is None:
        return None

    try:
        import earthaccess  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency
        logger.warning(
            "earthaccess package is not installed; skipping earthaccess authentication"
        )
        return None

    session = earthaccess.login(
        strategy="netrc",
        persist=True,
        netrc=netrc_path.expanduser().resolve(),
    )
    logger.info("Authenticated earthaccess session using %s", netrc_path)
    return session

