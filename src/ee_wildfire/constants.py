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

DEFAULT_GOOGLE_DRIVE_DIR = "EarthEngine_WildfireSpread_TS_" + str(MAX_YEAR)

INTERNAL_USER_CONFIG_DIR = ROOT / "user_config.yml"

ARG_NAMESPACE = ["year","min_size","output","drive_dir",
                "credentials","geojson_dir", "project_id",
                "download", "export", "show_config",
                "force_new_geojson", "sync_year",]

def main():
    print(HOME)
    print(ROOT)

if __name__ == "__main__":
    main()
