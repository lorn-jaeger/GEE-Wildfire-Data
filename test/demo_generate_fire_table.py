from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd
from dateutil.relativedelta import *

from ee_wildfire.command_line_args import parse, run
from ee_wildfire.constants import DATE_FORMAT, INTERNAL_USER_CONFIG_DIR
from ee_wildfire.create_fire_config import create_fire_config_globfire
from ee_wildfire.globfire import get_fire_count, get_fires, load_fires, save_fires
from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.utils.google_drive_util import get_location_count
from ee_wildfire.utils.yaml_utils import get_full_yaml_path

MIN_CUTOFF = 100000
MIN_STEP = 1000
MAX_CUTUFF = 10000000
# ACRE_MOD = 0.000247105
ACRE_TO_KM_MOD = 0.00404686

classes_in_km = {
    "A": 0.25 * ACRE_TO_KM_MOD,
    "B": 9.9 * ACRE_TO_KM_MOD,
    "C": 99.9 * ACRE_TO_KM_MOD,
    "D": 299 * ACRE_TO_KM_MOD,
    "E": 999 * ACRE_TO_KM_MOD,
    "F": 4999 * ACRE_TO_KM_MOD,
    "G": 9999 * ACRE_TO_KM_MOD,
}

# authenticate and setup
ConsoleUI.set_verbose(False)
uf = UserConfig()
uf.change_configuration_from_yaml(INTERNAL_USER_CONFIG_DIR)
uf.authenticate()


# date intervals
start = datetime(2017, 1, 1)
end = datetime(2022, 1, 1)
step = relativedelta(months=+1)
date_range = []
current = start

while current < end:
    date_range.append(current.strftime(DATE_FORMAT))
    current += step

# define min_val values
min_vals = list(range(1000, MIN_CUTOFF + MIN_STEP, MIN_STEP))

pivot_table = {min_val: [] for min_val in min_vals}
# pivot_table = defaultdict(lambda: defaultdict(list))
col_headers = []
date_labels = set()

for i in range(len(date_range) - 1):
    start_date = date_range[i]
    end_date = date_range[i + 1]
    col_label = f"{start_date} to {end_date}"
    col_headers.append(col_label)

    for min_val in min_vals:

        # setup user config
        uf.start_date = start_date
        uf.end_date = end_date
        uf.min_size = min_val
        uf.max_size = MAX_CUTUFF
        print(
            f"Fire count for {start_date} -> {end_date} at {min_val}km^2 to {MAX_CUTUFF}km^2 = ",
            end="",
        )
        count = get_fire_count(uf)
        # count = 69
        print(f"{count} fires")
        pivot_table[min_val].append(count)
        date_labels.add(col_label)


# convert pivot table to dataframe
df = pd.DataFrame.from_dict(
    pivot_table, orient="index", columns=list(sorted(date_labels))
)
df.index.name = "min_val"
df.to_csv("FireCounts.csv", index=True)
