import sys
import os
import argparse
from bqplot import default
import drive_downloader
import ee
from pandas._config import config
import yaml
from tqdm import tqdm
from get_globfire import get_combined_fires, analyze_fires
from DataPreparation.satellites.FirePred import FirePred
from DataPreparation.DatasetPrepareService import DatasetPrepareService
from create_globfire_config import create_fire_config_globfire
from drive_downloader import DriveDownloader
from create_globfire_config import create_fire_config_globfire

config_data = {}

def get_full_geojson_path():
    return f"{config_data['geojson']}combined_fires_{config_data['year']}.geojson"


def load_yaml_config(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_yaml_config(config, path):
    # print(config)
    # print(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(config, f, sort_keys=False)

def load_fire_config():
    with open(
        f"config/us_fire_{config_data['year']}_1e7.yml", "r", encoding="utf8"
    ) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def create_config(type):
    return


# from get_globfire.py
def generate_geojson():
    # Get both daily and final perimeters
    combined_gdf, daily_gdf, final_gdf = get_combined_fires(
        config_data['year'], config_data['min_size'] 
    )

    if combined_gdf is not None:
        print(f"\nAnalysis Results for {config_data['year']}:")

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
        monthly_counts = (
            combined_gdf.groupby([combined_gdf["date"].dt.month, "source"])
            .size()
            .unstack(fill_value=0)
        )
        comb
        print(monthly_counts)

    # drop everything that does not have at least 2 Id in combined_gdf
    combined_gdf_reduced = combined_gdf[
        combined_gdf["Id"].isin(
            combined_gdf["Id"]
            .value_counts()[combined_gdf["Id"].value_counts() > 1]
            .index
        )
    ]  # save to geojson

    geojson_path = get_full_geojson_path()
    combined_gdf_reduced.to_file(
        geojson_path,
        driver="GeoJSON",
    )


# from DatasetPrepareService.py
def export_data():
    project_id = config_data['project_id']
    
    # fp = FirePred()
    config = load_fire_config()
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
            dataset_pre.extract_dataset_from_gee_to_drive("32610", n_buffer_days=4)
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
    global config_data
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('--config', type=str,default="./config_options.yml" ,help="Path to JSON config file")
    args_partial, _ = base_parser.parse_known_args()

    # Load from YAML config (if given)
    config_path = args_partial.config
    config_data = load_yaml_config(config_path) if config_path else {}

    # Full parser
    parser = argparse.ArgumentParser(
        parents=[base_parser],
        description="Generate fire config YAML from GeoJSON."
    )
    parser.add_argument(
        "--year", type=str, help="Year of fire parameters."
    )

    parser.add_argument("--min-size", type=float, 
                        # default=configuration.MIN_SIZE,
                        )

    parser.add_argument(
        "--output",
        type=str,
        # default=configuration.OUTPUT_DIR,
        help="local directory where the TIFF files will go.",
    )

    parser.add_argument(
        "--drive-dir",
        type=str,
        # default=configuration.DATA_DIR,
        help="The google drive directory for TIFF files",
    )

    parser.add_argument(
        "--credentials",
        type=str,
        # default=configuration.CREDENTIALS,
        help="Path to Google OAuth credentials JSON.",
    )

    parser.add_argument(
        "--project-id",
        type=str,
        # default=configuration.PROJECT,
        help="Project ID for Google Cloud",
    )

    parser.add_argument(
        "--geojson",
        type=str,
        # default=configuration.DATA_DIR,
        help="Directory to store geojson files",
    )

    parser.add_argument(
        "--download",
        # type=bool,
        action="store_true",
        help="Download TIFF files from google drive.",
    )
    parser.add_argument("--export-data",
                        action="store_true",
                        help="Export to Google Drive.")

    # parser.add_argument("--import-data", action="store_true", help="import data?")


    # TODO: arguments to make configs

    args = parser.parse_args()
    print(args)

    # Update config_data with any non-None CLI args (override)
    for key in ["year","min_size","output","drive_dir",
                "credentials","project_id","geojson","download", "export_data"]:
        val = getattr(args,key)
        if val is not None:
            config_data[key]=val

    # save dictionary back to yaml file
    if config_path:
        save_yaml_config(config_data, config_path)

    # use or generate GeoJSON
    ee.Authenticate()
    ee.Initialize(project=config_data['project_id'])

    geojson_path = get_full_geojson_path()
    if not os.path.exists(geojson_path):
        generate_geojson()

    # generate the YAML output config
    yaml_path = f"{config_data['output']}us_fire_{config_data['year']}_1e7_test.yml"
    create_fire_config_globfire(geojson_path, yaml_path, config_data['year'])
    
    
    if(config_data['download']):
        downloader = DriveDownloader()
        downloader.download_folder(config_data['drive_dir'], config_data['output'])

    if(config_data['export_data']):
        export_data()



if __name__ == "__main__":
    main()
