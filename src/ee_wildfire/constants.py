"""
Constants.py

This is where the programs constant variables are stored
"""

from pathlib import Path

VERSION = "2025.1.3"

CRS_CODE = "32610"

MIN_YEAR = 2001

MAX_YEAR = 2021

ROOT = Path(__file__).resolve().parent

HOME = Path.home()

DEFAULT_DATA_DIR = HOME / "ee_wildfire_data"

DEFAULT_TIFF_DIR = DEFAULT_DATA_DIR / "tiff" / str(MAX_YEAR)

DEFAULT_GEOJSON_DIR = DEFAULT_DATA_DIR / "perims"

DEFAULT_GOOGLE_DRIVE_DIR = "EarthEngine_WildfireSpreadTS_"

INTERNAL_USER_CONFIG_DIR = ROOT / "user_config.yml"


COMMAND_ARGS = {
    #"NAME":                (type,  default,                    action,         help)
    "-config":              (Path,  INTERNAL_USER_CONFIG_DIR,   "store",        "Path to JSON config file"),
    "-export":              (None,  False,                      "store_true",   "Export to drive."),
    "-download":            (None,  False,                      "store_true",   "Download from drive."),
    "-show-config":         (None,  False,                      "store_true",   "Show user configuration."),
    "-version":             (None,  None,                       "version",      "Show current version"),
    "-force-new-geojson":   (None,  False,                      "store_true",   "Force new geojson generation."),

}

def main():
    for item in COMMAND_ARGS.keys():
        print(f"{item} {COMMAND_ARGS[item]}")

if __name__ == "__main__":
    main()
