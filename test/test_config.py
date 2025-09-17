from __future__ import annotations

import json
from pathlib import Path

from ee_wildfire.config import load_config


def write_service_account(path: Path) -> None:
    data = {
        "client_email": "test@example.com",
        "project_id": "ee-test",
        "private_key": "x",
        "private_key_id": "y",
        "token_uri": "https://example.com",
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_load_config_resolves_relative_paths(tmp_path):
    config_dir = tmp_path
    credentials_dir = config_dir / "credentials"
    credentials_dir.mkdir()
    service_account = credentials_dir / "service.json"
    write_service_account(service_account)

    yaml_path = config_dir / "pipeline.yml"
    yaml_path.write_text(
        """
credentials:
  earthengine_service_account: ./credentials/service.json
paths:
  raw_data: ./data/raw
  processed_data: ./data/processed
schema:
  index:
    dataset: globfire
    options:
      start_date: 2020-01-01
      end_date: 2020-01-02
      min_size: 1.0e7
  earthengine: []
  earthaccess: []
  custom: []
""",
        encoding="utf-8",
    )

    config = load_config(yaml_path)

    assert config.credentials.earthengine_service_account == service_account.resolve()
    assert config.paths.raw_data.is_dir()
    assert config.paths.processed_data.is_dir()
    assert config.schema.index.name == "globfire"
    assert config.schema.index.options["min_size"] == 1.0e7

