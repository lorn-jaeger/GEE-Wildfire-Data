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

from typing import Dict, Union, List

def _strip_tif_extention(filenames: List[str]):
    if all(name.endswith('.tif') for name in filenames):
        return [name[:-4] for name in filenames]
    return filenames

def get_number_items_in_export_queue():
    ConsoleUI.print("Quering Google Earth export queue...")
    tasks = getTaskList()
    active_tasks = [t for t in tasks if t['state'] in ['READY', 'RUNNING']]
    return len(active_tasks)

def get_active_tasks_in_export_queue():
    ConsoleUI.print("Quering Google Earth export queue...")
    tasks = getTaskList()
    active_tasks = [t for t in tasks if t['state'] in ['READY', 'RUNNING']]
    return active_tasks

def get_completed_tasks_in_export_queue():
    ConsoleUI.print("Quering Google Earth export queue...")
    tasks = getTaskList()
    completed_tasks = [t for t in tasks if t['state'] == 'COMPLETED']
    return completed_tasks 

def get_completed_tasks_versus_list(expected_files: List[str]):
    ConsoleUI.print("Quering Google Earth export queue...")
    fixed_files = _strip_tif_extention(expected_files)
    completed_tasks = get_completed_tasks_in_export_queue()
    filtered_completed_tasks = [t for t in completed_tasks if t['description'] in fixed_files]
    output = []
    for item in filtered_completed_tasks:
        output.append({
            "id": item['id'],
            "name": item['description']+".tif",
        })
    return output

def process_locations(locations: List[str], user_config: UserConfig, fire_config: Dict) -> List[str]:
    failed_locations = []

    # Process each location
    for location in locations:

        dataset_pre = DatasetPrepareService(location=location, config=fire_config, user_config=user_config)

        try:
            dataset_pre.extract_dataset_from_gee_to_drive(CRS_CODE , n_buffer_days=4)
        except Exception as e:
            ConsoleUI.update_bar(key="failed")
            ConsoleUI.print(f"Failed on {location}: {str(e)}", color="red")
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
    
    fire_config = load_fire_config(yaml_path)
    fire_names = list(fire_config.keys())
    for non_fire_key in ["output_bucket", "rectangular_size", "year"]:
        fire_names.remove(non_fire_key)
    locations = fire_names

    ConsoleUI.add_bar(key="processed", total=len(locations), desc="Fires processed")
    ConsoleUI.add_bar(key="failed", total=len(locations), desc="Number of failed locations",
                      color="red")
    failed_locations = process_locations(locations, user_config, fire_config)

    if failed_locations:
        ConsoleUI.debug("Failed locations:")
        for loc in failed_locations:
            ConsoleUI.debug(f"- {loc}")
        if(user_config.retry_failed):
            ConsoleUI.print("Retrying failed locations",color="yellow")
            process_locations(failed_locations, user_config, fire_config)

    else:
        ConsoleUI.print("All locations processed successfully!")

    return True
