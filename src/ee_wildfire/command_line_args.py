"""
command_line_args.py

this file will handle all the command line argument parsing.
"""

import argparse
from ee_wildfire.constants import *
from ee_wildfire.create_fire_config import create_fire_config_globfire
from ee_wildfire.utils.yaml_utils import load_yaml_config, save_yaml_config, get_full_yaml_path
from ee_wildfire.utils.google_drive_util import export_data
from ee_wildfire.UserConfig.UserConfig import UserConfig

def run(config):
    if(config.export or config.download):
        # generate geodata frame
        print("Generating GeoDataFrame...")
        config.get_geodataframe()
        # generate the YAML output config
        print("Generating fire configuration...")
        create_fire_config_globfire(config)

    # export data from earth engine to google drive
    if(config.export):
        print("Exporting data...")
        export_data(get_full_yaml_path(config))

    # download from google drive to local machine
    if(config.download):
        print("Downloading data...")
        config.downloader.download_folder(config.google_drive_dir, config.tiff_dir)

def parse():
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

    if(args.show_config):
        print(config)

    run(config)

def main():
    parse()

if __name__ == "__main__":
    main()

