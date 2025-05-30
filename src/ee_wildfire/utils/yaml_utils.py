"""
yaml_utils.py

This is a bunch of helper functions for handling yaml files
"""
import yaml
import os
from pathlib import PosixPath
from geopandas import GeoDataFrame
from ee_wildfire.drive_downloader import DriveDownloader
from ee_wildfire.constants import *

def validate_yaml_path(yaml_path):
    return os.path.exists(yaml_path)

def get_full_yaml_path(config):
    config_dir = ROOT / "config" / f"us_fire_{config.start_date.year}_1e7.yml"
    return config_dir

def load_yaml_config(yaml_path):

    if validate_yaml_path(yaml_path):
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

# def load_internal_user_config():
#     if not validate_yaml_path(INTERNAL_USER_CONFIG_DIR):
#         raise FileNotFoundError(f"Internal config at '{INTERNAL_USER_CONFIG_DIR}' not found.")
#
#     with open(INTERNAL_USER_CONFIG_DIR, 'r') as f:
#         return yaml.safe_load(f)

def save_yaml_config(config_data, yaml_path):

    accepted_types = [int, float, bool, str]

    transform_types = [PosixPath]

    rejected_types = [DriveDownloader, GeoDataFrame]

    keys_to_leave_out = []

    if not validate_yaml_path(yaml_path):
        os.makedirs(os.path.dirname(yaml_path), exist_ok=True)

    for key in config_data.keys():
        type_check = type(config_data[key])

        if type_check in accepted_types:
            pass

        if type_check in rejected_types:
            keys_to_leave_out.append(key)

        if type_check in transform_types:
            config_data[key] = str(config_data[key])

    config_data_fixed = {}
    for key in keys_to_leave_out:
        if key not in config_data:
            config_data_fixed[key] = config_data[key]

    with open(yaml_path, 'w') as f:
        yaml.dump(config_data_fixed, f, sort_keys=False)

def load_fire_config(yaml_path):
    with open(
        yaml_path, "r", encoding="utf8"
    ) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
