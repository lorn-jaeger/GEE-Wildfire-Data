"""
yaml_utils.py

This is a bunch of helper functions for handling yaml files
"""
import yaml
import os
from ee_wildfire.constants import *

def get_full_yaml_path(config_data):
    config_dir = ROOT / "config" / f"us_fire_{config_data['year']}_1e7.yml"
    return config_dir

def load_yaml_config(yaml_path):
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_yaml_config(config_data, yaml_path):
    try:
        with open(yaml_path, 'w') as f:
            yaml.dump(config_data, f, sort_keys=False)
    except FileNotFoundError:
        os.makedirs(os.path.dirname(yaml_path), exist_ok=True)

def load_fire_config(yaml_path):
    with open(
        yaml_path, "r", encoding="utf8"
    ) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
