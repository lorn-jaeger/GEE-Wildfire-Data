import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta
import yaml

def create_fire_config_globfire(geojson_path, output_path, year):
    gdf = gpd.read_file(geojson_path)
    gdf['IDate'] = pd.to_datetime(gdf['IDate'], unit='ms')
    gdf['FDate'] = pd.to_datetime(gdf['FDate'], format='mixed')
    
    gdf = gdf[gdf['IDate'].dt.year == year]
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

