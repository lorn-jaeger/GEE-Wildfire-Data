"""
google_drive_util.py

helper funcitons to help handle google drive api calls.
"""
from ee.data import getTaskList

from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface import ConsoleUI
from pathlib import Path

from ee_wildfire.utils.yaml_utils import load_fire_config
from ee_wildfire.constants import CRS_CODE
from ee_wildfire.DataPreparation.DatasetPrepareService import DatasetPrepareService

from typing import Union

def get_number_items_in_export_queue():
    # tasks = ee.data.getTaskList()
    tasks = getTaskList()
    active_tasks = [t for t in tasks if t['state'] in ['READY', 'RUNNING']]
    return len(active_tasks)

def get_number_items_in_google_drive():
    pass

def get_number_items_in_local_directory():
    pass

def process_locations(locations, user_config, fire_config):
    failed_locations = []

    # Process each location
    for location in locations:

        dataset_pre = DatasetPrepareService(location=location, config=fire_config, user_config=user_config)

        try:
            dataset_pre.extract_dataset_from_gee_to_drive(CRS_CODE , n_buffer_days=4)
        #FIX: This exception needs to be more specific
        except Exception as e:
            ConsoleUI.update_bar(key="failed")
            ConsoleUI.print(f"Failed on {location}: {str(e)}")
            failed_locations.append(location)
            continue

        ConsoleUI.update_bar(key="processed")

    return failed_locations

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

    ConsoleUI.add_bar(key="processed", total=len(locations), desc="Fires processed")
    ConsoleUI.add_bar(key="failed", total=len(locations), desc="Number of failed locations")
    failed_locations = process_locations(locations, user_config, config)

    # NOTE: This is where I should retry failed locations
    if failed_locations:
        ConsoleUI.print("Failed locations:")
        for loc in failed_locations:
            ConsoleUI.print(f"- {loc}")

        if(user_config.retry_failed):
            ConsoleUI.print("Retrying failed locations")
            process_locations(failed_locations, user_config, config)

    else:
        ConsoleUI.print("All locations processed successfully!")

    ConsoleUI.close_bar(key="export")
    ConsoleUI.close_bar(key="export_queue")
    ConsoleUI.close_bar(key="processed")
    ConsoleUI.close_bar(key="failed")

    return True

def main():
    uf = UserConfig()
    print(get_number_items_in_export_queue())
    pass

if __name__ == "__main__":
    main()



