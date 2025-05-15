import sys
import argparse
from bqplot import default
import ee
import configuration
import yaml
from tqdm import tqdm
from get_globfire import get_combined_fires, analyze_fires
from DataPreparation.satellites.FirePred import FirePred
from DataPreparation.DatasetPrepareService import DatasetPrepareService
from create_globfire_config import create_fire_config_globfire
from drive_downloader import DriveDownloader

MIN_SIZE = 1e7



def load_config():
    with open(f"config/us_fire_{configuration.YEAR}_1e7.yml", "r", encoding="utf8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def create_config(type):
    return

# from get_globfire.py
def import_data():
    # Get both daily and final perimeters
    combined_gdf, daily_gdf, final_gdf = get_combined_fires(configuration.YEAR, configuration.MIN_SIZE)

    if combined_gdf is not None:
        print(f"\nAnalysis Results for {configuration.YEAR}:")
        
        print("\nCombined Perimeters:")
        combined_stats = analyze_fires(combined_gdf)
        for key, value in combined_stats.items():
            print(f"{key}: {value}")
        
        if daily_gdf is not None:
            print("\nDaily Perimeters:")
            daily_stats = analyze_fires(daily_gdf)
            for key, value in daily_stats.items():
                print(f"{key}: {value}")
        
        if final_gdf is not None:
            print("\nFinal Perimeters:")
            final_stats = analyze_fires(final_gdf)
            for key, value in final_stats.items():
                print(f"{key}: {value}")
        
        # Temporal distribution
        print("\nFires by month:")
        monthly_counts = combined_gdf.groupby([combined_gdf['date'].dt.month, 'source']).size().unstack(fill_value=0)
        print(monthly_counts)

    # drop everything that does not have at least 2 Id in combined_gdf
    combined_gdf_reduced = combined_gdf[
        combined_gdf['Id'].isin(
            combined_gdf['Id'].value_counts()[combined_gdf['Id'].value_counts() > 1].index)]# save to geojson

    combined_gdf_reduced.to_file(f"{configuration.DATA_DIR}combined_fires_{configuration.YEAR}.geojson", driver="GeoJSON")


# from DatasetPrepareService.py
def export_data():
    ee.Authenticate()
    ee.Initialize(project=configuration.PROJECT)
    # fp = FirePred()
    config = load_config()
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
            dataset_pre.extract_dataset_from_gee_to_drive('32610', n_buffer_days=4)
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


def main():
    parser = argparse.ArgumentParser(
        prog="EE-Wildfire",
        description="Generate fire configuration YAML from GeoJSON fire perimeters.",
    )
    parser.add_argument('--year',
                        type=str,
                        required=True,
                        help="Year of fire parameters.")

    parser.add_argument('--min-size',
                        type=float,
                        default=configuration.MIN_SIZE)

    parser.add_argument('--output',
                        type=str,
                        default=configuration.OUTPUT_DIR,
                        help="local directory where the TIFF files will go."
                        )

    parser.add_argument('--drive-dir',
                        type=str,
                        default=configuration.DATA_DIR,
                        help="The google drive directory for TIFF files"
    )

    parser.add_argument('--credentials',
                        type=str,
                        default=configuration.CREDENTIALS,
                        help="Path to Google OAuth credentials JSON.")

    parser.add_argument('--project-id',
                        type=str,
                        default=configuration.PROJECT,
                        help="Project ID for Google Cloud")

    parser.add_argument('--geojson',
                        type=str,
                        default=configuration.DATA_DIR,
                        help="Directory to store geojson files")

    parser.add_argument('--download',
                        type=bool,
                        default=False,
                        help="Download TIFF files from google drive.")

    parser.add_argument('--export-data',
                        type=bool,
                        default=False,
                        help="Export data?")

    parser.add_argument('--import-data',
                        type=bool,
                        default=False,
                        help="import data?")

    #TODO: arguments to make configs


    args = parser.parse_args()

    if(args.import_data):
        import_data()

    if(args.export_data):
        export_data()

    if(args.download):
        downloader = DriveDownloader()
        downloader.download_folder(configuration.DRIVE_DIR, configuration.OUTPUT_DIR)
    return

if __name__ == "__main__":
    main()
