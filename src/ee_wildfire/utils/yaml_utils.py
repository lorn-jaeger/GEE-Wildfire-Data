"""
yaml_utils.py

This is a bunch of helper functions for handling yaml files
"""
import yaml
import os
from pathlib import PosixPath
from geopandas import GeoDataFrame
from ee_wildfire.constants import ROOT
from ee_wildfire.drive_downloader import DriveDownloader
from ee_wildfire.constants import *

from typing import Any, Dict, Union

def validate_yaml_path(yaml_path: Union[Path,str]) -> bool:
    return os.path.exists(yaml_path)

def get_full_yaml_path(config) -> Path:
    config_dir = ROOT / "config" / f"us_fire_{config.start_date.year}_1e{str(int(config.min_size)).count('0')}.yml"
    return config_dir

def load_yaml_config(yaml_path: Union[Path,str]) -> Dict:

    if validate_yaml_path(yaml_path):
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_yaml_config(config_data: Dict[str, Any], yaml_path: Union[Path,str]) -> None:

    accepted_types = [int, float, bool, str]

    transform_types = [PosixPath, Path]

    rejected_types = [DriveDownloader, GeoDataFrame]

    config_data_fixed = {}

    if not validate_yaml_path(yaml_path):
        os.makedirs(os.path.dirname(yaml_path), exist_ok=True)

    for key in config_data.keys():
        type_check = type(config_data[key])

        if type_check in accepted_types:
            config_data_fixed[key] = config_data[key]

        if type_check in rejected_types:
            pass

        if type_check in transform_types:
            config_data_fixed[key] = str(config_data[key])


    with open(yaml_path, 'w') as f:
        yaml.dump(config_data_fixed, f, sort_keys=False)

def load_fire_config(yaml_path: Union[Path,str]) -> Dict:
    with open(
        yaml_path, "r", encoding="utf8"
    ) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
