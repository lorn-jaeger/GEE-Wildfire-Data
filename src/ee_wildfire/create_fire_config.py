import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta
import yaml
import os

from ee_wildfire.utils.yaml_utils import get_full_yaml_path
from ee_wildfire.utils.geojson_utils import get_full_geojson_path

def create_fire_config_globfire(config):
    output_path = get_full_yaml_path(config)
    year = config.year
    geojson_path = get_full_geojson_path(config)

    # print(f"[LOG] from create_config, geojson_path: {geojson_path}")
    gdf = gpd.read_file(geojson_path)
    # print(f"[LOG] from create_config, gdf: {gdf}")
    gdf['IDate'] = pd.to_datetime(gdf['IDate'], unit='ms')
    gdf['FDate'] = pd.to_datetime(gdf['FDate'], format='mixed')
    # print(f"[LOG] from create_config, gdf Idate: {gdf['IDate']}")

    gdf = gdf[gdf['IDate'].dt.year == int(year)]
    # print(f"[LOG] from create_config, second gdf: {gdf}")
    first_occurrences = gdf.sort_values('IDate').groupby('Id').first()
    last_occurrences = gdf.sort_values('IDate').groupby('Id').last()

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

    with open(output_path, 'w') as f:
        yaml.dump(config, f, Dumper=DateSafeYAMLDumper, default_flow_style=False, sort_keys=False)

def create_fire_config_mtbs(geojson_path, output_path, year):
    # Read GeoJSON
    gdf = gpd.read_file(geojson_path)
    
    # Convert dates
    gdf['Ig_Date'] = pd.to_datetime(gdf['Ig_Date'])
    gdf['End_Date'] = pd.to_datetime(gdf['End_Date'])
    
    # Filter for year
    gdf = gdf[gdf['YEAR'] == year]
    
    config = {
        'output_bucket': 'firespreadprediction',
        'rectangular_size': 0.5,
        'year': year
    }
    
    class DateSafeYAMLDumper(yaml.SafeDumper):
        def represent_data(self, data):
            if isinstance(data, datetime):
                return self.represent_scalar('tag:yaml.org,2002:timestamp', data.strftime('%Y-%m-%d'))
            return super().represent_data(data)
    
    for idx, row in gdf.iterrows():
        start_date = row['Ig_Date'] - timedelta(days=4)
        end_date = row['End_Date'] + timedelta(days=4)
        
        config[f'fire_{row.Event_ID}'] = {
            'latitude': float(row['BurnBndLat']),
            'longitude': float(row['BurnBndLon']),
            'start': start_date.date(),
            'end': end_date.date()
        }
    
    with open(output_path, 'w') as f:
        yaml.dump(config, f, Dumper=DateSafeYAMLDumper, default_flow_style=False, sort_keys=False)

def load_fire_config(yaml_path):
    with open(
        yaml_path, "r", encoding="utf8"
    ) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
