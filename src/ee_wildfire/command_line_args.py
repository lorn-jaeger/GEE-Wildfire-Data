"""
command_line_args.py

this file will handle all the command line argument parsing.
"""

import argparse
import os
import time

from ee_wildfire.constants import *
from ee_wildfire.create_fire_config import create_fire_config_globfire
from ee_wildfire.drive_downloader import DriveDownloader
from ee_wildfire.ExportQueue.QueueManager import QueueManager as qm
from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface import map_maker
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.utils.google_drive_util import export_data, get_location_count
from ee_wildfire.utils.user_config_utils import parse_datetime
from ee_wildfire.utils.yaml_utils import (
    get_full_yaml_path,
    load_yaml_config,
    save_yaml_config,
)


def run(config: UserConfig) -> None:
    """
    Core pipeline logic for exporting and downloading wildfire data.

    Args:
        config (UserConfig): Fully initialized user configuration.
    """
    config.authenticate()
    downloader = DriveDownloader(config)

    if config.show_bbox:
        map_maker.show_bbox_on_map(config.bounding_area)

    if config.purge_before:
        downloader.purge_data()

    if config.count_fires:

        # generate geodata frame
        ConsoleUI.print("Generating GeoDataFrame...")
        config.get_geodataframe()

        # generate the YAML output config
        ConsoleUI.print("Generating Fire Configuration...")
        create_fire_config_globfire(config)

        num_fires = get_location_count(yaml_path=get_full_yaml_path(config))
        ConsoleUI.print(f"Number of fires: {num_fires}")
        time.sleep(5)

    if config.export:
        # generate geodata frame
        ConsoleUI.print("Generating GeoDataFrame...")
        config.get_geodataframe()

        # generate the YAML output config
        ConsoleUI.print("Generating Fire Configuration...")
        create_fire_config_globfire(config)

        qm.count_ee_active_tasks()

        ConsoleUI.print("Processing Data...")
        export_data(yaml_path=get_full_yaml_path(config), user_config=config)

    if (not config.export) and config.download:
        # config.downloader.download_folder(config.google_drive_dir, config.tiff_dir)
        downloader.download_folder()

    # download from google drive to local machine
    if config.download:
        # config.downloader.download_files(config.tiff_dir, config.exported_files)
        downloader.download_files()

    if config.purge_after:
        downloader.purge_data()

    ConsoleUI.print("Done!")


def parse(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="EE-Wildfire",
        description="Querries google earth for tiff images of wildfire locations",
        epilog="You will need a google cloud service account.",
    )

    # Required yaml configuration file
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=INTERNAL_USER_CONFIG_DIR,
        action="store",
        help="Path to YAML config file.",
        required=True,
    )

    # ==== Boolean arguments ====

    parser.add_argument(
        "-e",
        "--export",
        default=False,
        action="store_true",
        help="Export tiff images to Google drive.",
    )

    parser.add_argument(
        "-d",
        "--download",
        default=False,
        action="store_true",
        help="Download tiff images from Google drive.",
    )

    parser.add_argument(
        "-N",
        "--count-fires",
        default=False,
        action="store_true",
        help="Count number of querried fires.",
    )

    parser.add_argument(
        "-r",
        "--retry-failed",
        default=False,
        action="store_true",
        help="Retry failed exports.",
    )

    parser.add_argument(
        "-p",
        "--purge-before",
        default=False,
        action="store_true",
        help="Purge data from google drive before exporting new data.",
    )

    parser.add_argument(
        "-P",
        "--purge-after",
        default=False,
        action="store_true",
        help="Purge data from google drive after downloading.",
    )

    parser.add_argument(
        "-s",
        "--silent",
        default=False,
        action="store_true",
        help="No program output.",
    )

    parser.add_argument(
        "-n",
        "--no-log",
        default=False,
        action="store_true",
        help="Disable logging.",
    )

    parser.add_argument(
        "-b",
        "--draw-bbox",
        default=False,
        action="store_true",
        help="Draw bounding box for querry.",
    )

    parser.add_argument(
        "-B",
        "--show-bbox",
        default=False,
        action="store_true",
        help="Show bounding box.",
    )

    # ==== Path arguments ====

    parser.add_argument(
        "-C",
        "--credentials",
        type=Path,
        default=DEFAULT_OAUTH_DIR,
        action="store",
        help="Path to Google authentication JSON",
    )

    parser.add_argument(
        "-D",
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        action="store",
        help="Path to store output data.",
    )

    parser.add_argument(
        "-t",
        "--tiff-dir",
        type=Path,
        default=DEFAULT_TIFF_DIR,
        action="store",
        help="Path to store output tiff images.",
    )

    parser.add_argument(
        "-g",
        "--gdf-dir",
        type=Path,
        default=DEFAULT_GDF_DIR,
        action="store",
        help="Path to store pickle files.",
    )

    parser.add_argument(
        "-G",
        "--google-drive-dir",
        type=Path,
        default=DEFAULT_GOOGLE_DRIVE_DIR,
        action="store",
        help="Directory in Google drive to store tiff images.",
    )

    parser.add_argument(
        "-l",
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        action="store",
        help="Directory to store log files.",
    )

    # ==== Float arguments ====

    parser.add_argument(
        "-m",
        "--min-size",
        type=float,
        default=DEFAULT_MIN_SIZE,
        action="store",
        help="Minimum size fire detection.",
    )

    parser.add_argument(
        "-M",
        "--max-size",
        type=float,
        default=DEFAULT_MAX_SIZE,
        action="store",
        help="Maximum size fire detection.",
    )

    # ==== Date arguments ====

    parser.add_argument(
        "-S",
        "--start-date",
        type=parse_datetime,
        default=DEFAULT_START_DATE,
        action="store",
        help="Start date for querry.",
    )

    parser.add_argument(
        "-E",
        "--end-date",
        type=parse_datetime,
        default=DEFAULT_END_DATE,
        action="store",
        help="End date for querry.",
    )

    # ==== Misc arguments ====

    parser.add_argument(
        "-L",
        "--log-level",
        type=str,
        default=DEFAULT_LOG_LEVEL,
        action="store",
        help="Log level: debug, info, warn, error",
    )

    args = parser.parse_args(argv)
    return args


def apply_to_user_config(args: argparse.Namespace) -> UserConfig:

    config_dict = vars(args)
    for key, val in load_yaml_config(args.config).items():
        config_dict[key] = val

    # UI initialization
    ConsoleUI.set_verbose(not config_dict["silent"])

    # logging setup
    if not config_dict["no_log"]:
        ConsoleUI.setup_logging(config_dict["log_dir"])
        ConsoleUI.set_log_level(config_dict["log_level"])

    # bounding box setup
    if config_dict["draw_bbox"]:
        map_maker.setup_logging(config_dict["log_level"])
        map_maker.get_map_html()
        config_dict["bounding_area"] = map_maker.launch_draw_map()
    else:
        config_dict["bounding_area"] = USA_COORDS

    # apply to user config
    uf = UserConfig(vars(args))

    ConsoleUI.debug(uf.__repr__())

    return uf


def main():
    ui = ConsoleUI()
    config = parse()
    print(config)


if __name__ == "__main__":
    main()
