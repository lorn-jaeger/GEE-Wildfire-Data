"""
yaml_utils.py

This is a bunch of helper functions for handling yaml files
"""

import os
from datetime import datetime
from pathlib import PosixPath
from typing import Any, Dict, Union

import yaml

from ee_wildfire.constants import *
from ee_wildfire.constants import ROOT


def validate_yaml_path(yaml_path: Union[Path, str]) -> bool:
    return os.path.exists(yaml_path)


def get_full_yaml_path(config) -> Path:
    file_name = (
        f"us_fire_{config.start_date.year}_1e{str(int(config.min_size)).count('0')}.yml"
    )
    full_path = config.data_dir / "fire_configs" / file_name
    return full_path


def load_yaml_config(yaml_path: Union[Path, str]) -> Dict:

    if validate_yaml_path(yaml_path):
        with open(yaml_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_yaml_config(config_data: Dict[str, Any], yaml_path: Union[Path, str]) -> None:

    accepted_types = [int, float, bool, str, datetime]

    transform_types = [PosixPath, Path]

    config_data_fixed = {}

    rejected_names = ["reset_config"]

    if not validate_yaml_path(yaml_path):
        os.makedirs(os.path.dirname(yaml_path), exist_ok=True)

    for key in config_data.keys():
        type_check = type(config_data[key])

        if key not in rejected_names:

            if type_check in accepted_types:
                config_data_fixed[key] = config_data[key]

            if type_check in transform_types:
                config_data_fixed[key] = str(config_data[key])

            if type_check is None:
                config_data_fixed[key] = False

    with open(yaml_path, "w") as f:
        yaml.dump(config_data_fixed, f, sort_keys=False)


def load_fire_config(yaml_path: Union[Path, str]) -> Dict:
    with open(yaml_path, "r", encoding="utf8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
