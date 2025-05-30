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

from tqdm import tqdm

def run(config: UserConfig) -> None:
    """
    Core pipeline logic for exporting and downloading wildfire data.
    
    Args:
        config (UserConfig): Fully initialized user configuration.
    """
    if(config.export or config.download):
        # generate geodata frame
        tqdm.write("Generating GeoDataFrame...")
        config.get_geodataframe()

        # generate the YAML output config
        tqdm.write("Generating Fire Configuration...")
        create_fire_config_globfire(config)

    if((not config.export) and config.download):
        config.downloader.download_folder(config.google_drive_dir, config.tiff_dir)

    # export data from earth engine to google drive
    if(config.export):
        tqdm.write("Processing Data...")
        export_data(yaml_path=get_full_yaml_path(config), user_config=config)

    # download from google drive to local machine
    if(config.download):
        config.downloader.download_files(config.google_drive_dir, config.tiff_dir, config.exported_files)

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
        elif(cmd != "-version"):
            base_parser.add_argument(cmd,
                                     default=_default,
                                     action=_action,
                                     help=_help)
        else:
            base_parser.add_argument(cmd,
                                     action=_action,
                                     version=VERSION,
                                     help=_help)


    args, _ = base_parser.parse_known_args()

    outside_user_config_path = args.config

    config = UserConfig(yaml_path=outside_user_config_path)
    config.change_configuration_from_yaml(outside_user_config_path)
    config.change_bool_from_args(args)

    if(args.show_config or (args.config != INTERNAL_USER_CONFIG_DIR)):
        tqdm.write(str(config))

    return config

def main():
    config = parse()
    print(config)

if __name__ == "__main__":
    main()

