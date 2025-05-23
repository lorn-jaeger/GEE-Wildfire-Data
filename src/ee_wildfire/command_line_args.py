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

def get_namespace():
    namespace = []
    for name in COMMAND_ARGS:
        if(name != "-version"):
            namespace.append(name[1:].replace("-","_"))
    return namespace

def parse():
    # base_parser = argparse.ArgumentParser(add_help=False)
    # base_parser.add_argument('--config', 
    #                          type=str,default=INTERNAL_USER_CONFIG_DIR,
    #                          help="Path to JSON config file")
    # args_partial, _ = base_parser.parse_known_args()
    #
    # # Load from YAML config (if given)
    # config_path = args_partial.config
    # config_data = load_yaml_config(config_path) if config_path else {}
    #
    # # Full parser
    # parser = argparse.ArgumentParser(
    #     parents=[base_parser],
    #     description="Generate fire config YAML from GeoJSON."
    # )
    # parser.add_argument(
    #     "--year", type=str, help="Year of fire parameters."
    # )
    #
    # parser.add_argument("--min-size", type=float, 
    #                     # default=configuration.MIN_SIZE,
    #                     )
    #
    # parser.add_argument(
    #     "--output",
    #     type=str,
    #     # default=configuration.OUTPUT_DIR,
    #     help="local directory where the TIFF files will go.",
    # )
    #
    # parser.add_argument(
    #     "--drive-dir",
    #     type=str,
    #     # default=configuration.DATA_DIR,
    #     help="The google drive directory for TIFF files",
    # )
    #
    # parser.add_argument(
    #     "--credentials",
    #     type=str,
    #     help="Path to Google OAuth credentials JSON.",
    # )
    #
    # parser.add_argument(
    #     "--geojson-dir",
    #     type=str,
    #     help="Directory to store geojson files",
    # )
    #
    # parser.add_argument(
    #     "--download",
    #     # type=bool,
    #     action="store_true",
    #     help="Download TIFF files from google drive.",
    # )
    # parser.add_argument("--export",
    #                     action="store_true",
    #                     help="Export to Google Drive")
    #
    # parser.add_argument("--show-config",
    #                     action="store_true",
    #                     help="Show current configuration.")
    #
    # parser.add_argument("--force-new-geojson",
    #                     action="store_true",
    #                     help="Force generate new geojson.")
    #
    # parser.add_argument("--sync-year",
    #                     action="store_true",
    #                     help="Syncs the year to the input/output files")
    #
    #
    # parser.add_argument("--version",
    #                     action="version",
    #                     version=f"ee-wildfire version = {VERSION}")
    #
    # parser.add_argument(
    #     "--project-id",
    #     type=str,
    #     help="Project ID for Google Cloud",
    # )
    #
    # args = parser.parse_args()
    #
    # # Update config_data with any non-None CLI args (override)
    # for key in ARG_NAMESPACE:
    #     val = getattr(args,key)
    #     if val is not None:
    #         config_data[key]=val
    #
    # # check if year is within bounds of the dataset
    # reference_year = int(config_data['year'])
    # if((reference_year < MIN_YEAR) or (reference_year > MAX_YEAR)):
    #     raise IndexError(f"Year {reference_year} is not contained within the dataset.")
    #
    # # if(config_data['sync_year']):
    # #     sync_drive_path_with_year()
    # #     sync_tiff_output_with_year()
    #
    # if(config_data['show_config']):
    #     print(config_data)
    #
    # # save dictionary back to yaml file
    # if config_path:
    #     save_yaml_config(config_data, config_path)
    #
    #
    # # Read the user account creds
    # credentials_path = config_data.get('credentials')
    # if not credentials_path:
    #     raise KeyError(f"Malformed configuration yaml at {credentials_path}. Missing credentials field.")
    #
    # Authenticate()
    # Initialize(project=config_data['project_id'])

    # use or generate geojson
    # geojson_path = get_full_geojson_path()
    # if (not os.path.exists(geojson_path) or config_data['force_new_geojson']):
    #     print("Generating Geojson...")
    #     generate_geojson(config_data)
    #
    # # generate the YAML output config
    # yaml_path = get_full_yaml_path(config_data)
    # create_fire_config_globfire(geojson_path, yaml_path, config_data['year'])
    
    # if(config_data['export']):
    #     print("Exporting data...")
    #     export_data(yaml_path)   
    #
    # if(config_data['download']):
    #     downloader = DriveDownloader(config_data['credentials'])
    #     downloader.download_folder(config_data['drive_dir'], config_data['output'])
    
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


    config = UserConfig()
    config.change_configuration_from_yaml(args.config)

    if(args.show_config):
        print(config)

    full_geojson_path = get_full_geojson_path(config)
    if(args.force_new_geojson or os.path.exists(full_geojson_path)):
        generate_geojson(config)

    # generate the YAML output config
    create_fire_config_globfire(config)

    if(args.export):
        export_data(get_full_yaml_path(config))

    if(args.download):
        print(config.google_drive_dir)
        config.downloader.download_folder(config.google_drive_dir, config.tiff_dir)


