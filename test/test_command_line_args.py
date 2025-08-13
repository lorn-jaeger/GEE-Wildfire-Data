import subprocess
from datetime import datetime
from pathlib import Path

import yaml
from utils import *

from ee_wildfire.command_line_args import parse
from ee_wildfire.constants import *


def test_parse_minimal_args():
    args = parse(["-c", YAML_FILE])
    assert str(args.config) == YAML_FILE
    assert args.export is False
    assert args.download is False
    assert args.min_size == DEFAULT_MIN_SIZE
    assert args.max_size == DEFAULT_MAX_SIZE


def test_parse_all_booleans_true():
    args = parse(
        [
            "-c",
            YAML_FILE,
            "-e",
            "-d",
            "-N",
            "-r",
            "-p",
            "-P",
            "-s",
            "-n",
            "-b",
            "-B",
        ]
    )
    assert args.export is True
    assert args.download is True
    assert args.count_fires is True
    assert args.retry_failed is True
    assert args.purge_before is True
    assert args.purge_after is True
    assert args.silent is True
    assert args.no_log is True
    assert args.draw_bbox is True
    assert args.show_bbox is True


def test_parse_paths_and_numbers():
    args = parse(
        [
            "-c",
            YAML_FILE,
            "-C",
            "/creds/auth.json",
            "-D",
            "/data",
            "-t",
            "/tiff",
            "-g",
            "/gdf",
            "-G",
            "/gdrive",
            "-l",
            "/logs",
            "-m",
            "1.5",
            "-M",
            "20.0",
        ]
    )
    assert args.credentials == Path("/creds/auth.json")
    assert args.data_dir == Path("/data")
    assert args.tiff_dir == Path("/tiff")
    assert args.gdf_dir == Path("/gdf")
    assert args.google_drive_dir == Path("/gdrive")
    assert args.log_dir == Path("/logs")
    assert args.min_size == 1.5
    assert args.max_size == 20.0


def test_parse_dates_and_log_level():
    start_str = "2025-01-01"
    end_str = "2025-01-31"
    args = parse(["-c", YAML_FILE, "-S", start_str, "-E", end_str, "-L", "debug"])
    assert args.start_date == parse_datetime(start_str)
    assert args.end_date == parse_datetime(end_str)
    assert args.log_level == "debug"


test_parse_minimal_args()
