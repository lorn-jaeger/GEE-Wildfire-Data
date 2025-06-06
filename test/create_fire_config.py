import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta
import yaml
import os

from ee_wildfire.utils.yaml_utils import get_full_yaml_path
from ee_wildfire.utils.geojson_utils import get_full_geojson_path


def create_fire_config_globfire(config):
    output_path = get_full_yaml_path(config)
    geojson_path = get_full_geojson_path(config)
    gdf = gpd.read_file(geojson_path)

    config = {
        "output_bucket": "firespreadprediction",
        "rectangular_size": 0.5,
        "start": config.start_date,
        "end": config.end_date,
    }

    # ensures that datetime objects are dumped as YYYY-MM-DD
    class DateSafeYAMLDumper(yaml.SafeDumper):
        def represent_data(self, data):
            if isinstance(data, datetime):
                return self.represent_scalar(
                    "tag:yaml.org,2002:timestamp", data.strftime("%Y-%m-%d")
                )
            return super().represent_data(data)
        
    for _, row in gdf.iterrows():
        fire_id = row["Id"]

        config[f"fire_{fire_id}"] = {
            "latitude": float(row["lat"]),
            "longitude": float(row["lon"]),
            "start": row["IDate"].date(),
            "end": row["FDate"].date(),
        }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
   
    with open(output_path, "w") as f:
        yaml.dump(
            config,
            f,
            Dumper=DateSafeYAMLDumper,
            default_flow_style=False,
            sort_keys=False,
        )


def load_fire_config(yaml_path):
    with open(yaml_path, "r", encoding="utf8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
