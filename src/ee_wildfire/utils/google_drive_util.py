"""
google_drive_util.py

helper funcitons to help handle google drive api calls.
"""

from pathlib import Path
from ee_wildfire.utils.yaml_utils import load_fire_config
from ee_wildfire.constants import CRS_CODE
from ee_wildfire.DataPreparation.DatasetPrepareService import DatasetPrepareService
from tqdm import tqdm

def sync(config_data):
    sync_drive_path_with_year(config_data)
    sync_tiff_output_with_year(config_data)
                              
def sync_drive_path_with_year(config_data):
    drive_path = f"EarthEngine_WildfireSpreadTS_{config_data['year']}"
    config_data['drive_dir'] = drive_path

def sync_tiff_output_with_year(config_data):
    parent_tiff_path = Path(config_data['output']).parent
    new_tiff_path = parent_tiff_path / config_data['year']
    new_tiff_path.mkdir(parents=True, exist_ok=True)
    config_data['output'] = str(new_tiff_path) + "/"

def export_data(yaml_path):
    
    # fp = FirePred()
    config = load_fire_config(yaml_path)
    # print(f"[LOG] from export_data, yaml path: {yaml_path}")
    # print(f"[LOG] from export_data, config: {config}")
    fire_names = list(config.keys())
    for non_fire_key in ["output_bucket", "rectangular_size", "year"]:
        fire_names.remove(non_fire_key)
    locations = fire_names

    # Track any failures
    failed_locations = []

    # Process each location
    for location in tqdm(locations):
        print(f"\nFailed locations so far: {failed_locations}")
        print(f"Current Location: {location}")

        dataset_pre = DatasetPrepareService(location=location, config=config)

        try:
            print(f"Trying to export {location} to Google Drive")
            dataset_pre.extract_dataset_from_gee_to_drive(CRS_CODE , n_buffer_days=4)
        except Exception as e:
            print(f"Failed on {location}: {str(e)}")
            failed_locations.append(location)
            continue

    if failed_locations:
        print("\nFailed locations:")
        for loc in failed_locations:
            print(f"- {loc}")
    else:
        print("\nAll locations processed successfully!")

