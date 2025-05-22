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

ARG_NAMESPACE = ["year","min_size","output","drive_dir",
                "credentials","geojson_dir", "project_id",
                "download", "export", "show_config",
                "force_new_geojson", "sync_year",]
