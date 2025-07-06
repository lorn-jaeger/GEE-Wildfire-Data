from datetime import datetime, timedelta

from dateutil.relativedelta import *

from ee_wildfire.command_line_args import parse, run
from ee_wildfire.constants import DATE_FORMAT
from ee_wildfire.create_fire_config import create_fire_config_globfire
from ee_wildfire.globfire import get_fire_count, get_fires, load_fires, save_fires
from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.utils.google_drive_util import get_location_count
from ee_wildfire.utils.yaml_utils import get_full_yaml_path

MIN_CUTOFF = 10000000
MAX_CUTUFF = 100000000

# Start and end dates as strings
start_str = "2001-01-01"
end_str = "2021-12-01"

# Parse to datetime objects
start_date = datetime.strptime(start_str, DATE_FORMAT)

END_DATE_CUTOFF = datetime.strptime(end_str, DATE_FORMAT)
START_DATE_CUTOFF = start_date

ConsoleUI.set_verbose(False)
uf = parse()
uf.silent = True
uf.authenticate()
uf.max_size = MAX_CUTUFF


def get_date_range(start, end):

    if type(start) is str:
        start = datetime.strptime(start, DATE_FORMAT)

    if type(end) is str:
        end = datetime.strptime(end, DATE_FORMAT)

    current = end
    date_range = []

    while current >= start:
        date_range.append(current.strftime(DATE_FORMAT))
        current = current - relativedelta(months=+1)

    return date_range


target_date = start_date + relativedelta(years=+1)
date_range = get_date_range(start_date, target_date)

fire_counts = []
num_fires = 0
end_date = datetime.strptime(date_range[0], DATE_FORMAT)


while end_date <= END_DATE_CUTOFF:

    for start_date in date_range:
        for min_val in range(1000, MIN_CUTOFF, 1000):

            # setup user config
            uf.min_size = min_val
            uf.start_date = start_date
            uf.end_date = end_date
            print(
                f"Mid computation: {start_date}, {end_date}, {min_val}, {uf.max_size}"
            )

            # get number of fires
            prev_num_fires = num_fires

            try:
                num_fires = get_fire_count(uf)
            except Exception as e:
                print(str(e))
                break

            fire_counts.append((min_val, num_fires, start_date, end_date))
            print(start_date, end_date, min_val, num_fires)

            if num_fires == prev_num_fires:
                break

    target_date = datetime.strptime(start_date, DATE_FORMAT) + relativedelta(years=+1)
    date_range = get_date_range(start_date, target_date)
    end_date = datetime.strptime(date_range[0], DATE_FORMAT)

print(fire_counts)
