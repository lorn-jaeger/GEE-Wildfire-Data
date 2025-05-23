"""
yaml_utils.py

This is a bunch of helper functions for handling yaml files
"""
import yaml
import os
from ee_wildfire.constants import *

def validate_yaml_path(yaml_path):
    return os.path.exists(yaml_path)

def get_full_yaml_path(config):
    config_dir = ROOT / "config" / f"us_fire_{config.year}_1e7.yml"
    return config_dir

def load_yaml_config(yaml_path):
    #TODO: make sure this handles relative pathing
    if validate_yaml_path(yaml_path):
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def load_internal_user_config():
    if not validate_yaml_path(INTERNAL_USER_CONFIG_DIR):
        raise FileNotFoundError(f"Internal config at '{INTERNAL_USER_CONFIG_DIR}' not found.")
    
    with open(INTERNAL_USER_CONFIG_DIR, 'r') as f:
        return yaml.safe_load(f)

def save_yaml_config(config_data, yaml_path):
    if not validate_yaml_path(yaml_path):
        os.makedirs(os.path.dirname(yaml_path), exist_ok=True)

    with open(yaml_path, 'w') as f:
        yaml.dump(config_data, f, sort_keys=False)

def load_fire_config(yaml_path):
    with open(
        yaml_path, "r", encoding="utf8"
    ) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
