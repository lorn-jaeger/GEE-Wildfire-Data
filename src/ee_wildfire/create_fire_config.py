import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta
import yaml
import os

from ee_wildfire.UserInterface import ConsoleUI
from ee_wildfire.utils.yaml_utils import get_full_yaml_path
from ee_wildfire.UserConfig.UserConfig import UserConfig

def create_fire_config_globfire(user_config: UserConfig) -> None:
    """
    Create a fire configuration YAML file from the user's GeoDataFrame (GlobFire source),
    organizing ignition and containment dates by fire ID.

    The output YAML will include bounding boxes and time intervals for each fire detected
    in the given year, as well as global metadata like output bucket and rectangular size.

    Args:
        config (UserConfig): A user config object that contains:
            - start_date (datetime): The start date of the fire dataset.
            - geodataframe (GeoDataFrame): A GeoDataFrame with fire event records.
    """

    output_path = get_full_yaml_path(user_config)
    year = user_config.start_date.year
    gdf = user_config.geodataframe
    gdf['IDate'] = pd.to_datetime(gdf['IDate'], unit='ms')
    gdf['FDate'] = pd.to_datetime(gdf['FDate'], format='mixed')
    gdf = gdf[gdf['IDate'].dt.year == int(year)]
    first_occurrences = gdf.sort_values('IDate').groupby('Id').first() #type: ignore
    last_occurrences = gdf.sort_values('IDate').groupby('Id').last() #type: ignore

    ConsoleUI.debug(f"\toutput path: {output_path}")
    ConsoleUI.debug(f"\tyear: {year}")
    ConsoleUI.debug(f"\tfirst occurence: {first_occurrences}")
    ConsoleUI.debug(f"\tlast occurence: {last_occurrences}")
    ConsoleUI.debug(f"\tgeodatafram: {gdf}")

    config = {
        'output_bucket': 'firespreadprediction',
        'rectangular_size': 0.5, 'year': year }

    # ensures that datetime objects are dumped as YYYY-MM-DD
    class DateSafeYAMLDumper(yaml.SafeDumper):
        def represent_data(self, data):
            if isinstance(data, datetime):
                return self.represent_scalar('tag:yaml.org,2002:timestamp', data.strftime('%Y-%m-%d'))
            return super().represent_data(data)

    # Populate fire entries
    for idx in first_occurrences.index:
        first = first_occurrences.loc[idx]
        last = last_occurrences.loc[idx]

        # no final date, just pulls last inital date
        end_date = last['FDate'] if pd.notna(last['FDate']) else last['IDate']
        # 4 day buffer before and after ignition/containment
        start_date = first['IDate'] - timedelta(days=4)
        end_date = end_date + timedelta(days=4)

        config[f'fire_{idx}'] = {
            'latitude': float(first['lat']),
            'longitude': float(first['lon']),
            'start': start_date.date(),
            'end': end_date.date()
        }
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ConsoleUI.debug(f"\tFire config: {config}")

    with open(output_path, 'w') as f:
        yaml.dump(config, f, Dumper=DateSafeYAMLDumper, default_flow_style=False, sort_keys=False)



