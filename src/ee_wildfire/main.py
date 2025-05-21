import os
from pathlib import Path
import argparse
from ee import Authenticate, ServiceAccountCredentials #type: ignore
from ee import Initialize
import json
from google.oauth2.reauth import refresh_grant
import yaml
from tqdm import tqdm
from get_globfire import get_combined_fires, analyze_fires
from DataPreparation.DatasetPrepareService import DatasetPrepareService
from drive_downloader import DriveDownloader
from create_fire_config import create_fire_config_globfire

VERSION = "2025.1.2"
CRS_CODE = "32610"
MIN_YEAR = 2001
MAX_YEAR = 2021

config_data = {}

ROOT = Path(__file__).resolve().parent

ARG_NAMESPACE = ["year","min_size","output","drive_dir",
                "credentials","geojson_dir", "project_id",
                "download", "export_data", "show_config",
                "force_new_geojson", "sync_year",]


def get_full_geojson_path():
    return f"{config_data['geojson_dir']}combined_fires_{config_data['year']}.geojson"

def get_full_yaml_path():
    config_dir = ROOT / "config" / f"us_fire_{config_data['year']}_1e7.yml"
    return config_dir

def sync_drive_path_with_year():
    drive_path = f"EarthEngine_WildfireSpreadTS_{config_data['year']}"
    config_data['drive_dir'] = drive_path

def sync_tiff_output_with_year():
    parent_tiff_path = Path(config_data['output']).parent
    new_tiff_path = parent_tiff_path / config_data['year']
    new_tiff_path.mkdir(parents=True, exist_ok=True)
    config_data['output'] = str(new_tiff_path) + "/"

def load_yaml_config(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_yaml_config(config, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(config, f, sort_keys=False)

def load_fire_config(yaml_path):
    with open(
        yaml_path, "r", encoding="utf8"
    ) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


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
        if combined_stats is not None:
            for key, value in combined_stats.items():
                print(f"{key}: {value}")
        else:
            print("No stats available for combined perimeters.")

        if daily_gdf is not None:
            print("\nDaily Perimeters:")
            daily_stats = analyze_fires(daily_gdf)
            if daily_stats is not None:
                for key, value in daily_stats.items():
                    print(f"{key}: {value}")
            else:
                print("No stats available for daily perimeters.")

        if final_gdf is not None:
            print("\nFinal Perimeters:")
            final_stats = analyze_fires(final_gdf)
            if final_stats is not None:
                for key, value in final_stats.items():
                    print(f"{key}: {value}")
            else:
                print("No stats available for final perimeters.")

        # Temporal distribution
        print("\nFires by month:")
        monthly_counts = (
            combined_gdf.groupby([combined_gdf["date"].dt.month, "source"])
            .size()
            .unstack(fill_value=0)
        )
        print(monthly_counts)

    # drop everything that does not have at least 2 Id in combined_gdf
    combined_gdf_reduced = None

    if combined_gdf is not None and "Id" in combined_gdf.columns:
        id_counts = combined_gdf["Id"].value_counts()
        repeated_ids = id_counts[id_counts > 1].index.tolist()
        combined_gdf_reduced = combined_gdf[combined_gdf["Id"].isin(repeated_ids)]
    else:
        raise TypeError("combined_gdf is None or missing 'Id' column")

    # save to geojson
    geojson_path = get_full_geojson_path()
    combined_gdf_reduced.to_file(
        geojson_path,
        driver="GeoJSON",
    )


# from DatasetPrepareService.py
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


def main():
    global config_data
    internal_config_path = ROOT / "config_options.yml"

    # FIX: this doesn't actully update any values in the internal config
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('--config', 
                             type=str,default=internal_config_path ,
                             help="Path to JSON config file")
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
        help="Path to Google OAuth credentials JSON.",
    )

    parser.add_argument(
        "--geojson-dir",
        type=str,
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
                        help="Export to Google Drive")

    parser.add_argument("--show-config",
                        action="store_true",
                        help="Show current configuration.")

    parser.add_argument("--force-new-geojson",
                        action="store_true",
                        help="Force generate new geojson.")

    parser.add_argument("--sync-year",
                        action="store_true",
                        help="Syncs the year to the input/output files")


    parser.add_argument("--version",
                        action="version",
                        version=f"ee-wildfire version = {VERSION}")

    parser.add_argument(
        "--project-id",
        type=str,
        help="Project ID for Google Cloud",
    )

    args = parser.parse_args()


    # Update config_data with any non-None CLI args (override)
    for key in ARG_NAMESPACE:
        val = getattr(args,key)
        if val is not None:
            config_data[key]=val

    # check if year is within bounds of the dataset
    reference_year = int(config_data['year'])
    if((reference_year < MIN_YEAR) or (reference_year > MAX_YEAR)):
        raise IndexError(f"Year {reference_year} is not contained within the dataset.")

    if(config_data['sync_year']):
        sync_drive_path_with_year()
        sync_tiff_output_with_year()

    if(config_data['show_config']):
        print(config_data)

    # save dictionary back to yaml file
    if config_path:
        save_yaml_config(config_data, config_path)


    # Read the user account creds
    credentials_path = config_data.get('credentials')
    if not credentials_path:
        raise KeyError(f"Malformed configuration yaml at {credentials_path}. Missing credentials field.")

    Authenticate()
    Initialize(project=config_data['project_id'])

    # use or generate geojson
    geojson_path = get_full_geojson_path()
    if (not os.path.exists(geojson_path) or config_data['force_new_geojson']):
        print("Generating Geojson...")
        generate_geojson()

    # generate the YAML output config
    yaml_path = get_full_yaml_path()
    create_fire_config_globfire(geojson_path, yaml_path, config_data['year'])
    
    if(config_data['export_data']):
        print("Exporting data...")
        export_data(yaml_path)   

    if(config_data['download']):
        downloader = DriveDownloader(config_data['credentials'])
        downloader.download_folder(config_data['drive_dir'], config_data['output'])

if __name__ == "__main__":
    main()
