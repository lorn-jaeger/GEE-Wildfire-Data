import os
import tempfile
from pathlib import Path

import yaml

from ee_wildfire.constants import *

YAML_FILE = str(Path.home() / "NRML" / "testing_config.yml")


def load_yaml_file(file_path) -> dict:
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")


# Default YAML config values
DEFAULT_TEST_CONFIG = {
    "credentials": "~/NRML/OAuth/credentials.json",
    "min_size": DEFAULT_MIN_SIZE,
    "max_size": DEFAULT_MAX_SIZE,
    "start_date": DEFAULT_START_DATE,
    "end_date": DEFAULT_END_DATE,
    "tiff_dir": str(DEFAULT_TIFF_DIR),
    "data_dir": str(DEFAULT_DATA_DIR),
    "log_dir": str(DEFAULT_LOG_DIR),
    "google_drive_dir": DEFAULT_GOOGLE_DRIVE_DIR,
    "purge_before": False,
    "download": False,
    "export": False,
    "retry_failed": False,
    "purge_after": False,
    "no_log": False,
    "log_level": DEFAULT_LOG_LEVEL,
    "silent": False,
}
testing_yaml_dir = ""


def create_test_yaml(
    overrides: dict = None, dir_path: Path = None, filename: str = "test_config.yaml"
) -> Path:
    """
    Create a YAML file for testing with default fields.

    Args:
        overrides (dict, optional): Dictionary of values to override defaults.
        dir_path (Path, optional): Directory to write YAML. Defaults to temp dir.
        filename (str, optional): Filename of YAML. Defaults to "test_config.yaml".

    Returns:
        Path: Path to created YAML file.
    """
    config = DEFAULT_TEST_CONFIG.copy()
    if overrides:
        config.update(overrides)

    if dir_path is None:
        temp_dir = tempfile.TemporaryDirectory()
        dir_path = Path(temp_dir.name)
    else:
        dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / filename
    with open(file_path, "w") as f:
        yaml.safe_dump(config, f)

    # make sure the temp file doesnt disappear prematurely
    global testing_yaml_dir
    testing_yaml_dir = temp_dir

    return file_path


def count_files_in_directory(directory_path):
    """
    Counts the number of files directly within a specified directory.
    """
    file_count = 0
    try:
        for entry in os.listdir(directory_path):
            full_path = os.path.join(directory_path, entry)
            if os.path.isfile(full_path):
                file_count += 1
        return file_count
    except FileNotFoundError:
        print(f"Error: Directory not found at '{directory_path}'")
        return 0
