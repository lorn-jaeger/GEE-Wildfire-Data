"""
command_line_args.py

this file will handle all the command line argument parsing.
"""

import argparse
import os
from ee_wildfire.constants import *
from ee import Authenticate #type: ignore
from ee import Initialize
from ee_wildfire.create_fire_config import create_fire_config_globfire
from ee_wildfire.utils.yaml_utils import load_yaml_config, save_yaml_config, get_full_yaml_path
from ee_wildfire.utils.geojson_utils import generate_geojson, get_full_geojson_path
from ee_wildfire.utils.google_drive_util import export_data
from ee_wildfire.drive_downloader import DriveDownloader
from ee_wildfire.UserConfig.UserConfig import UserConfig

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
    config.change_configuration_from_yaml(args.config)
    config.change_bool_from_args(args)

    if(args.show_config):
        print(config)

    full_geojson_path = get_full_geojson_path(config)
    geojson_exist = os.path.exists(full_geojson_path)
    if(not geojson_exist or config.force_new_geojson):

        if(config.force_new_geojson):
            print(f"Forcing the generation of new Geojson...")

        elif(not geojson_exist):
            print(f"Geojson at '{full_geojson_path}' does not exist. Generating Geojson...")


        generate_geojson(config)

            # TODO: split batch into smaller chunks

    #TODO: check if geojson is corrupted, if so regen

    # generate the YAML output config
    print("Generating fire configuration...")
    create_fire_config_globfire(config)


    if(config.export):
        print("Exporting data...")
        export_data(get_full_yaml_path(config))

    if(config.download):
        print("Downloading data...")
        config.downloader.download_folder(config.google_drive_dir, config.tiff_dir)


