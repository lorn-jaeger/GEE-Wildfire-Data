import argparse
import os
from pathlib import Path
from datetime import datetime

class StorePassedAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # Record which args were passed by the user
        if not hasattr(namespace, '_explicit_args'):
            namespace._explicit_args = set()
        namespace._explicit_args.add(self.dest)
        setattr(namespace, self.dest, values)


# handles date and time formating from command line
def parse_datetime(s):
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Invalid date format: '{s}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")
