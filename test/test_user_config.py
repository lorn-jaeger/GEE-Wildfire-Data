import shutil
from datetime import datetime
from pathlib import Path

import pytest
from utils import *

from ee_wildfire.command_line_args import apply_to_user_config, parse, run
from ee_wildfire.constants import *

TMP_DIR = Path("/tmp/ee_wildfire_test")


def test_config_application():

    yaml_path = create_test_yaml()
    args = parse(["-c", str(yaml_path)])
    file = load_yaml_file(yaml_path)
    uf = apply_to_user_config(args)

    for key, val in file.items():
        assert uf[key] == val


@pytest.mark.integration  # optional, mark so you can run only integration tests
def test_single_run():
    data_dir = TMP_DIR / "data"

    data_dir.mkdir(parents=True, exist_ok=True)

    overrides = {
        "data_dir": str(data_dir),
        "min_size": 10000000,
        "max_size": 100000000,
        "start_date": "2020-01-01",
        "end_date": "2020-01-08",
        "export": True,
        "download": True,
        "purge_before": True,
        "silent": True,
    }
    yaml_path = create_test_yaml(overrides=overrides)
    args = parse(["-c", str(yaml_path)])
    file = load_yaml_file(yaml_path)
    uf = apply_to_user_config(args)
    run(uf)

    assert (
        count_files_in_directory(data_dir / "fire_configs") > 0
    ), "No fire config found!"
    assert count_files_in_directory(data_dir / "gdfs") > 0, "No fire pickles found!"
    assert (
        count_files_in_directory(data_dir / "tiff") >= 36
    ), "Not enough tiff files downloaded!"

    shutil.rmtree(TMP_DIR)
