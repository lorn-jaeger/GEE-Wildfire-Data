"""
google_drive_util.py

helper funcitons to help handle google drive api calls.
"""

from ee_wildfire.UserConfig.UserConfig import UserConfig
from pathlib import Path

from ee_wildfire.utils.yaml_utils import load_fire_config
from ee_wildfire.constants import CRS_CODE
from ee_wildfire.DataPreparation.DatasetPrepareService import DatasetPrepareService
from tqdm import tqdm

from typing import Union


def export_data(yaml_path: Union[Path,str], user_config: UserConfig) -> bool:
    """
    Export satellite data from Google Earth Engine to Google Drive for multiple fire locations.

    This function reads a YAML configuration file specifying multiple fire areas, prepares
    datasets for each location using Earth Engine, and attempts to export the images to
    the user's Google Drive. It tracks and reports any failures encountered during the export process.

    Args:
        yaml_path (Union[Path,str]): Path to the YAML configuration file containing fire locations and parameters.
        user_config (UserConfig): An instance of UserConfig containing user credentials and settings.

    Returns:
        bool: True if execution completed (regardless of success/failure for individual locations).
    """
    
    config = load_fire_config(yaml_path)
    fire_names = list(config.keys())
    for non_fire_key in ["output_bucket", "rectangular_size", "year"]:
        fire_names.remove(non_fire_key)
    locations = fire_names

    # Track any failures
    failed_locations = []
    progress_bar = tqdm(locations, desc="Fires processed")
    failed_fire_bar = tqdm(total=len(locations), desc="Number of failed locations", leave=False)

    # Process each location
    for location in progress_bar:

        dataset_pre = DatasetPrepareService(location=location, config=config, user_config=user_config)

        try:
            dataset_pre.extract_dataset_from_gee_to_drive(CRS_CODE , n_buffer_days=4)
        #FIX: This exception needs to be more specific
        except Exception as e:
            # print(f"Failed on {location}: {str(e)}")
            failed_fire_bar.update(1)
            failed_locations.append(location)
            continue

    failed_fire_bar.close()

    if failed_locations:
        print("\nFailed locations:")
        for loc in failed_locations:
            print(f"- {loc}")
    else:
        tqdm.write("\nAll locations processed successfully!")


    return True

