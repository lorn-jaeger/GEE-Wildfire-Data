from datetime import datetime
from pathlib import Path

from utils import *

from ee_wildfire.command_line_args import apply_to_user_config, parse
from ee_wildfire.constants import *

SERVICE_ACCOUNT = Path("/home/kyle/NRML/OAuth/service-account-credentials.json")
DATA_DIR = Path("/home/kyle/opt")
TIFF_DIR = Path("/home/kyle/opt/tiff_test")
LOG_DIR = DATA_DIR / "log_test"
LOG_LVL = "debug"
DRIVE_DIR = "test_dir"


def test_config_application():
    args = parse(
        [
            "-c",
            YAML_FILE,
        ]
    )
    file = load_yaml_file()
    uf = apply_to_user_config(args)

    for key, val in file.items():
        assert uf[key] == val
