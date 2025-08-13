import argparse
import os
from datetime import datetime
from pathlib import Path


# handles date and time formating from command line
def parse_datetime(s):
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Invalid date format: '{s}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."
    )
