"""
google_drive_util.py

helper funcitons to help handle google drive api calls.
"""

from ee_wildfire.utils.yaml_utils import load_fire_config
from ee_wildfire.constants import CRS_CODE
from ee_wildfire.DataPreparation.DatasetPrepareService import DatasetPrepareService
from tqdm import tqdm


def export_data(yaml_path, user_config):
    
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
            failed_fire_bar.update(1)
            failed_locations.append(location)
            continue

    failed_fire_bar.close()

    if failed_locations:
        print("\nFailed locations:")
        for loc in failed_locations:
            print(f"- {loc}")
    else:
        print("\nAll locations processed successfully!")


    return True

