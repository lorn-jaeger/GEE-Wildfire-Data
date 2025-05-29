"""
Constants.py

This is where the programs constant variables are stored
"""

from pathlib import Path
# from datetime import Date
from datetime import datetime

VERSION = "2025.1.5"

CRS_CODE = "32610"

DATE_FORMAT = "%Y-%m-%d"

DEFAULT_PROJECT_ID = "ee-earthdata-459817"

MIN_YEAR = 2001

MAX_YEAR = 2021

MIN_MONTH = 1

MAX_MONTH = 12
    
DEFAULT_START_DATE = datetime.strptime(f'{MAX_YEAR}-{MIN_MONTH}-1', DATE_FORMAT)

DEFAULT_END_DATE = datetime.strptime(f'{MAX_YEAR}-{MAX_MONTH}-31', DATE_FORMAT)

DEFAULT_MIN_SIZE = 1e7

DEFAULT_MAX_SIZE = 1e10

ROOT = Path(__file__).resolve().parent

HOME = Path.home()

DEFAULT_DATA_DIR = HOME / "ee_wildfire_data"

DEFAULT_TIFF_DIR = DEFAULT_DATA_DIR / "tiff"

DEFAULT_OAUTH_DIR = DEFAULT_DATA_DIR / "OAuth" / "credentials.json"

DEFAULT_GOOGLE_DRIVE_DIR = "EarthEngine_WildfireSpreadTS"

INTERNAL_USER_CONFIG_DIR = ROOT / "user_config.yml"


COMMAND_ARGS = {
    #"NAME":                (type,  default,                    action,         help)
    "-config":              (Path,  INTERNAL_USER_CONFIG_DIR,   "store",        "Path to JSON config file"),
    "-export":              (None,  False,                      "store_true",   "Export to drive."),
    "-download":            (None,  False,                      "store_true",   "Download from drive."),
    "-show-config":         (None,  False,                      "store_true",   "Show user configuration."),
    "-version":             (None,  None,                       "version",      "Show current version"),

}

def main():
    print(DEFAULT_START_DATE)
    print(DEFAULT_END_DATE)

if __name__ == "__main__":
    main()
