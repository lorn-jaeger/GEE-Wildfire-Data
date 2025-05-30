"""
Constants.py

This is where the programs constant variables are stored
"""

from pathlib import Path
from datetime import datetime

# =========== Paths ===========

ROOT = Path(__file__).resolve().parent

HOME = Path.home()

AUTH_TOKEN_PATH = ROOT / "UserConfig" / "auth_token.json"

INTERNAL_USER_CONFIG_DIR = ROOT / "UserConfig" /"user_config.yml"

# =========== Needed Constants ===========

VERSION = "2025.1.5"

CRS_CODE = "32610"

DATE_FORMAT = "%Y-%m-%d"

MIN_YEAR = 2001

MAX_YEAR = 2021

MIN_MONTH = 1

MAX_MONTH = 12

USA_COORDS = [
    [-125.1803892906456, 35.26328285844432],
    [-117.08916345892665, 33.2311514593429],
    [-114.35640058749676, 32.92199940444295],
    [-110.88773544819885, 31.612036247094473],
    [-108.91086200144109, 31.7082477979397],
    [-106.80030780089378, 32.42079476218232],
    [-103.63413436750255, 29.786401496314422],
    [-101.87558377066483, 30.622527701868453],
    [-99.40039768482492, 28.04018292597704],
    [-98.69085295525215, 26.724810345780593],
    [-96.42355704777482, 26.216515704595633],
    [-80.68508661702214, 24.546812350183075],
    [-75.56173032587596, 26.814533788629998],
    [-67.1540159827795, 44.40095539443753],
    [-68.07548734644243, 46.981170472447374],
    [-69.17500995805074, 46.98158998130476],
    [-70.7598785138901, 44.87172183866657],
    [-74.84994741250935, 44.748084983808],
    [-77.62168256782745, 43.005725611950055],
    [-82.45987924104175, 41.41068867019324],
    [-83.38318501671864, 42.09979904377044],
    [-82.5905167831457, 45.06163491639556],
    [-84.83301910769038, 46.83552648258547],
    [-88.26350848510909, 48.143646480291835],
    [-90.06706251069104, 47.553445811024204],
    [-95.03745451438925, 48.9881557770297],
    [-98.45773319567587, 48.94699366043251],
    [-101.7018751401119, 48.98284560308372],
    [-108.43164852530356, 48.81973606668503],
    [-115.07339190755627, 48.93699058308441],
    [-121.82530604190744, 48.9830983403776],
    [-122.22085227110232, 48.63535795404536],
    [-124.59504332589562, 47.695726563030405],
    [-125.1803892906456, 35.26328285844432]
]

COLLECTIONS = [
    'JRC/GWIS/GlobFire/v2/FinalPerimeters',
    'JRC/GWIS/GlobFire/v2/DailyPerimeters'
]


# =========== Default User Configs ===========

DEFAULT_PROJECT_ID = "ee-earthdata-459817"
    
DEFAULT_START_DATE = datetime.strptime(f'{MAX_YEAR}-{MIN_MONTH}-1', DATE_FORMAT)

DEFAULT_END_DATE = datetime.strptime(f'{MAX_YEAR}-{MAX_MONTH}-31', DATE_FORMAT)

DEFAULT_MIN_SIZE = 1e7

DEFAULT_MAX_SIZE = 1e10

DEFAULT_DATA_DIR = HOME / "ee_wildfire_data"

DEFAULT_TIFF_DIR = DEFAULT_DATA_DIR / "tiff"

DEFAULT_OAUTH_DIR = DEFAULT_DATA_DIR / "OAuth" / "credentials.json"

DEFAULT_GOOGLE_DRIVE_DIR = "EarthEngine_WildfireSpreadTS"


# =========== Command Line Arguments ===========

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
