"""
command_line_args.py

this file will handle all the command line argument parsing.
"""

import argparse
from ee_wildfire.constants import COMMAND_ARGS, VERSION, INTERNAL_USER_CONFIG_DIR
from ee_wildfire.create_fire_config import create_fire_config_globfire
from ee_wildfire.utils.yaml_utils import  get_full_yaml_path
from ee_wildfire.utils.google_drive_util import export_data
from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface import ConsoleUI
from ee_wildfire.drive_downloader import DriveDownloader
from ee_wildfire.UserConfig.UserConfig import delete_user_config

# from tqdm import tqdm

def run(config: UserConfig) -> None:
    # TODO: update docs
    """
    Core pipeline logic for exporting and downloading wildfire data.
    
    Args:
        config (UserConfig): Fully initialized user configuration.
    """
    config.authenticate()
    downloader = DriveDownloader(config)

    if(config.purge_before):
        downloader.purge_data()

    if(config.export):
        # generate geodata frame
        ConsoleUI.print("Generating GeoDataFrame...")
        config.get_geodataframe()

        # generate the YAML output config
        ConsoleUI.print("Generating Fire Configuration...")
        create_fire_config_globfire(config)



    if((not config.export) and config.download):
        # config.downloader.download_folder(config.google_drive_dir, config.tiff_dir)
        downloader.download_folder()

    # export data from earth engine to google drive
    if(config.export):
        ConsoleUI.print("Processing Data...")
        export_data(yaml_path=get_full_yaml_path(config), user_config=config)


    # download from google drive to local machine
    if(config.download):
        # config.downloader.download_files(config.tiff_dir, config.exported_files)
        downloader.download_files()

    if(config.purge_after):
        downloader.purge_data()


def parse() -> UserConfig:
    """
    Parses command-line arguments and initializes user config.

    Returns:
        UserConfig: A fully initialized user configuration.
    """
    base_parser = argparse.ArgumentParser(add_help=False)
    for cmd in COMMAND_ARGS.keys():
        _type, _default, _action, _help = COMMAND_ARGS[cmd]
        if(_type):
            base_parser.add_argument(cmd,
                                     type=_type,
                                     default=_default,
                                     action=_action,
                                     help=_help)
        elif(cmd not in ["--version", "--help"]):
            base_parser.add_argument(cmd,
                                     default=_default,
                                     action=_action,
                                     help=_help)
        elif(cmd == "--version"):
            base_parser.add_argument(cmd,
                                     action=_action,
                                     version=VERSION,
                                     help=_help)
        elif(cmd == "--help"):
            base_parser.add_argument(cmd,
                                     action=_action,
                                     help=_help)


    args, _ = base_parser.parse_known_args()

    # ======== Before User Config Creation ========


    ConsoleUI.set_verbose(not args.silent)
    ConsoleUI.clear_screen()

    if(args.reset_config):
        delete_user_config()

    # ======== After User Config Creation ========

    config = UserConfig()

    # log files setup
    if(not args.no_log):
        if(hasattr(config,"log_dir")):
            ConsoleUI.setup_logging(config.log_dir)

    # user config from yaml or command line args
    if(args.config == INTERNAL_USER_CONFIG_DIR):
        config.change_configuration_from_args(args)
    else:
        config.change_configuration_from_yaml(args.config)

    # log level
    if hasattr(config,"log_level"):
        ConsoleUI.set_log_level(config.log_level)
    if(hasattr(config,"debug")):
        if(config.debug or args.debug):
            ConsoleUI.set_log_level("debug")

    # ======== After User Config Configuration? ========

    ConsoleUI.write(str(config))

    ConsoleUI.write("")

    ConsoleUI.debug(config.__repr__())

    return config

def main():
    ui = ConsoleUI()
    config = parse()
    # ConsoleUI.prompt_path()

if __name__ == "__main__":
    main()

