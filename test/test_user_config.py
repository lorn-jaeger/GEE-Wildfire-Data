from unittest.mock import patch
from datetime import datetime
from ee_wildfire.command_line_args import parse
from ee_wildfire.constants import *
from pathlib import Path


SERVICE_ACCOUNT = Path("/home/kyle/NRML/OAuth/service-account-credentials.json")
DATA_DIR = Path("/home/kyle/opt")
TIFF_DIR = Path("/home/kyle/opt/google-cloud-sdk")
DRIVE_DIR = "test_dir"



def __load_config(args_dict):
    cli_args = []
    for key, value in args_dict.items():
        if isinstance(value, bool):
            if value:  # Only include flags that are True
                cli_args.append(key)
        else:
            cli_args.extend([key, str(value)])
    test_args = ['prog'] + cli_args

    with patch('sys.argv', test_args):
        config = parse()
    return config

def test_reset():
    args_dict = {
        '--silent': None,
        '--reset-config': True,
        '--credentials':SERVICE_ACCOUNT,
    }
    config = __load_config(args_dict)

    assert config.silent, "Expected `config.silent` to be True"
    assert config.reset_config,  "Expected `config.reset_config` to be True"
    assert not config.export, "Expected `config.export` to be False"
    assert not config.download, "Expected `config.download` to be False"
    assert not config.retry_failed, "Expected `config.retry_failed` to be False"
    assert not config.purge_after, "Expected `config.purge_after` to be False"
    assert not config.purge_before, "Expected `config.purge_before` to be False"

    assert config.tiff_dir == DEFAULT_TIFF_DIR, f"Expected `config.tiff_dir` to be {DEFAULT_TIFF_DIR}"
    assert config.data_dir == DEFAULT_DATA_DIR, f"Expected `config.data_dir` to be {DEFAULT_DATA_DIR}"
    assert config.start_date == DEFAULT_START_DATE, f"Expected `config.start_date` to be {DEFAULT_START_DATE}"
    assert config.end_date == DEFAULT_END_DATE, f"Expected `config.end_date` to be {DEFAULT_END_DATE}"
    assert config.credentials == SERVICE_ACCOUNT, f"Expected `config.credentials` to be {SERVICE_ACCOUNT}"
    assert config.google_drive_dir == DEFAULT_GOOGLE_DRIVE_DIR, f"Expected `config.google_drive_dir` to be {DEFAULT_GOOGLE_DRIVE_DIR}"
    assert config.min_size == DEFAULT_MIN_SIZE, f"Expected `config.min_size` to be {DEFAULT_MIN_SIZE}"
    assert config.max_size == DEFAULT_MAX_SIZE, f"Expected `config.max_size` to be {DEFAULT_MAX_SIZE}"



def test_dict_style_arguments():
    args_dict = {
        '--export': True,
        '--download': True,
        '--retry-failed': True,
        '--data-dir': DATA_DIR,
        '--tiff-dir': TIFF_DIR,
        '--start-date': '2021-01-01',
        '--end-date': '2021-01-14',
        '--silent': None,
        '--credentials': SERVICE_ACCOUNT,
        '--google-drive-dir': DRIVE_DIR,
        '--purge-after': True,
        '--purge-before': True,
        '--min-size': 10,
        '--max-size': 100,
    }
    config = __load_config(args_dict)


    assert config.silent, "Expected `config.silent` to be True"
    assert config.purge_after, "Expected `config.purge_after` to be True"
    assert config.purge_before, "Expected `config.purge_before` to be True"
    assert config.export, "Expected `config.export` to be True"
    assert config.download, "Expected `config.download` to be True"
    assert config.retry_failed, "Expected `config.retry_failed` to be True"

    assert config.tiff_dir == TIFF_DIR, f"Expected `config.tiff_dir` to be {TIFF_DIR}"
    assert config.data_dir == DATA_DIR, f"Expected `config.data_dir` to be {DATA_DIR}"
    assert config.start_date == datetime(2021, 1, 1), "Expected `config.start_date` to be 2021-01-01"
    assert config.end_date == datetime(2021, 1, 14), "Expected `config.end_date` to be 2021-01-14"
    assert config.credentials == SERVICE_ACCOUNT, f"Expected `config.credentials` to be {SERVICE_ACCOUNT}"
    assert config.google_drive_dir == DRIVE_DIR, f"Expected `config.google_drive_dir` to be {DRIVE_DIR}"
    assert config.min_size == 10, "Expected `config.min_size` to be 10"
    assert config.max_size == 100, "Expected `config.max_size` to be 100"

def test_internal_config_after_arg_change():
    args_dict = {
        "--silent": None,
    }
    config = __load_config(args_dict)

    assert config.silent, "Expected `config.silent` to be True"
    assert not config.export, "Expected `config.export` to be False"
    assert not config.download, "Expected `config.download` to be False"
    assert not config.retry_failed, "Expected `config.retry_failed` to be False"
    assert not config.purge_after, "Expected `config.purge_after` to be False"
    assert not config.purge_before, "Expected `config.purge_before` to be False"

    assert config.tiff_dir == TIFF_DIR, f"Expected `config.tiff_dir` to be {TIFF_DIR}"
    assert config.data_dir == DATA_DIR, f"Expected `config.data_dir` to be {DATA_DIR}"
    assert config.start_date == datetime(2021, 1, 1), "Expected `config.start_date` to be 2021-01-01"
    assert config.end_date == datetime(2021, 1, 14), "Expected `config.end_date` to be 2021-01-14"
    assert config.credentials == SERVICE_ACCOUNT, f"Expected `config.credentials` to be {SERVICE_ACCOUNT}"
    assert config.google_drive_dir == DRIVE_DIR, f"Expected `config.google_drive_dir` to be {DRIVE_DIR}"
    assert config.min_size == 10, "Expected `config.min_size` to be 10"
    assert config.max_size == 100, "Expected `config.max_size` to be 100"


