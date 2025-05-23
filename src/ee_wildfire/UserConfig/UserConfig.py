
from ee_wildfire.utils.yaml_utils import load_yaml_config, validate_yaml_path, load_internal_user_config, save_yaml_config
from ee_wildfire.constants import *
from ee_wildfire.drive_downloader import DriveDownloader

from ee import Authenticate #type: ignore
from ee import Initialize

import os


class UserConfig:

    def __init__(self, yaml_path = None):
        if(yaml_path):
            #TODO: validate yaml_path
            config_data = load_yaml_config(yaml_path)
            self._load_config(config_data)

        elif(validate_yaml_path(INTERNAL_USER_CONFIG_DIR)):
            config_data = load_internal_user_config()
            self._load_config(config_data)

        else:
            # default config
            #TODO: validate paths
            print("No user configuration found. Loading default.")
            self.project_id = "ee-earthdata-459817"
            self.credentials = DEFAULT_DATA_DIR / "OAuth" / "credentials.json"
            self.year = str(MAX_YEAR)
            self.month = "1"
            self.geojson_dir = DEFAULT_DATA_DIR / "perims"
            self.tiff_dir = DEFAULT_DATA_DIR / "tiff" / self.year
            self.google_drive_dir = DEFAULT_GOOGLE_DRIVE_DIR
            self.download = False
            self.export = False
            self.force_new_geojson = False

            self._validate_paths()
            self._save_config()

        self._autheticate()

    def _load_config(self, config_data):
        self.project_id = config_data['project_id']
        self.credentials = config_data['credentials']
        self.year = config_data['year']
        self.month = config_data['month']
        self.geojson_dir = config_data['geojson_dir']
        self.tiff_dir = config_data['tiff_dir']
        self.google_drive_dir = config_data['google_drive_dir']
        self.download = config_data['download']
        self.export = config_data['export']
        self.force_new_geojson = config_data['force_new_geojson']
        self._validate_paths()
        self._save_config()

    def _to_dict(self):
        config_data = {
            'project_id':self.project_id,
            'credentials':str(self.credentials),
            'year':self.year,
            'month':self.month,
            'geojson_dir':str(self.geojson_dir),
            'tiff_dir':str(self.tiff_dir),
            'google_drive_dir':self.google_drive_dir,
            'download':self.download,
            'export':self.export,
            'force_new_geojson':self.force_new_geojson,
        }
        return config_data

    def _save_config(self):
        save_yaml_config(self._to_dict(), INTERNAL_USER_CONFIG_DIR)

    def _validate_paths(self):

        def try_make_path(path):
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except PermissionError:
                    print(f"Permission denied: Unable to create '{path}'")
                    
        if not os.path.exists(self.credentials):
            raise FileNotFoundError(f"{self.credentials} is not found.")

        try_make_path(self.geojson_dir)
        try_make_path(self.tiff_dir)

    def _autheticate(self):

        Authenticate()
        Initialize(project=self.project_id)
        self.downloader = DriveDownloader(self.credentials)




def main():
    uf = UserConfig()

if __name__ == "__main__":
    main()
