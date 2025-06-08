import argparse
import os
from pathlib import Path

class StorePassedAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # Record which args were passed by the user
        if not hasattr(namespace, '_explicit_args'):
            namespace._explicit_args = set()
        namespace._explicit_args.add(self.dest)
        setattr(namespace, self.dest, values)


def delete_user_config() -> None:
    """
    Deletes the user_config.yml file if it exists.

    Args:
        path (Path): Path to the config file. Defaults to standard location.
    """
    path = Path(INTERNAL_USER_CONFIG_DIR)
    try:
        if path.exists():
            path.unlink()
            print(f"[INFO] Deleted config file: {path}")
        else:
            print(f"[INFO] No config file found at: {path}")
    except Exception as e:
        print(f"[ERROR] Failed to delete config file: {e}")
