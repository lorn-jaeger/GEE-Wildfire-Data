
from csv import Error

from numpy import show_config
from pandas._config import config
from ee_wildfire.utils.yaml_utils import load_yaml_config, validate_yaml_path, load_internal_user_config, save_yaml_config
from ee_wildfire.constants import *
from ee_wildfire.drive_downloader import DriveDownloader

from ee import Authenticate #type: ignore
from ee import Initialize

import os


class UserConfig:

    def __init__(self, yaml_path = None):
        if(yaml_path and (yaml_path != INTERNAL_USER_CONFIG_DIR)):
            config_data = load_yaml_config(yaml_path)
            self._load_config(config_data)

        elif(validate_yaml_path(INTERNAL_USER_CONFIG_DIR)):
            config_data = load_internal_user_config()
            self._load_config(config_data)

        else:
            # default config
            self._load_default_config(INTERNAL_USER_CONFIG_DIR)

        self._authenticate()

    def __str__(self):
        output_str = [
            f"Project ID:                       {self.project_id}",
            f"Year:                             {self.year}",
            f"Min Size:                         {self.min_size}",
            f"Data directory path               {self.data_dir}",
            f"Credentials path:                 {self.credentials}",
            f"Geojson path:                     {self.geojson_dir}",
            f"Tiff directory path:              {self.tiff_dir}",
            f"Are you downloading?              {self.download}",
            f"Are you exporting data?           {self.export}",
            f"Are you needing a new Geojson?    {self.force_new_geojson}"
        ]

        return "\n".join(output_str)
        # return str(self._to_dict())

    def _load_default_config(self,path):
        print(f"No user configuration found at '{path}'. Loading default.")
        self.project_id = "ee-earthdata-459817"
        self.data_dir = DEFAULT_DATA_DIR
        self.credentials = self.data_dir/ "OAuth" / "credentials.json"
        self.year = str(MAX_YEAR)
        self.month = "1"
        self.geojson_dir = self.data_dir / "perims"
        self.tiff_dir = self.data_dir / "tiff" / self.year
        self.download = False
        self.export = False
        self.force_new_geojson = False
        self.min_size = 1e7

        self._validate_paths()
        self._save_config()

    def _save_config(self):
        save_yaml_config(self._to_dict(), INTERNAL_USER_CONFIG_DIR)

    def _load_config(self, config_data):
        self.project_id = config_data['project_id']
        self.data_dir = Path(config_data['data_dir']).expanduser()
        self.year = config_data['year']
        self.month = config_data['month']
        self.geojson_dir = self.data_dir / "perims"
        self.tiff_dir = self.data_dir / "tiff" / self.year
        self.credentials = self.data_dir / "OAuth" / "credentials.json"
        # self.credentials = Path(config_data['credentials']).expanduser()
        # self.geojson_dir = Path(config_data['geojson_dir']).expanduser()
        # self.tiff_dir = Path(config_data['tiff_dir']).expanduser()
        self.download = config_data['download']
        self.export = config_data['export']
        self.force_new_geojson = config_data['force_new_geojson']
        self.min_size = config_data['min_size']
        self._validate_paths()
        self._save_config()

    def _to_dict(self):
        config_data = {
            'project_id':self.project_id,
            'data_dir': str(self.data_dir),
            'credentials':str(self.credentials),
            'year':self.year,
            'month':self.month,
            'geojson_dir':str(self.geojson_dir),
            'tiff_dir':str(self.tiff_dir),
            'drive_dir':self.google_drive_dir,
            'download':self.download,
            'export':self.export,
            'force_new_geojson':self.force_new_geojson,
            'min_size':self.min_size,
        }
        return config_data

    def _validate_and_sync_year(self):
        if(int(self.year) < MIN_YEAR):
            raise IndexError(f"Querry year '{self.year}' is smaller than the minimum year '{MIN_YEAR}'")

        if(int(self.year) > MAX_YEAR):
            raise IndexError(f"Querry year '{self.year}' is larger than the maximum year '{MAX_YEAR}'")

        self.tiff_dir = self.tiff_dir.parent / self.year
        self.google_drive_dir = DEFAULT_GOOGLE_DRIVE_DIR + str(self.year)

    def _validate_paths(self):

        self.google_drive_dir = DEFAULT_GOOGLE_DRIVE_DIR + str(self.year)

        def try_make_path(path):
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except PermissionError:
                    print(f"Permission denied: Unable to create '{path}'")
                except Error as e:
                    print(f"Error happened {e}.")
                    
        if not os.path.exists(self.credentials):
            raise FileNotFoundError(f"{self.credentials} is not found.")

        try_make_path(self.data_dir)
        try_make_path(self.geojson_dir)
        try_make_path(self.tiff_dir)
        self._validate_and_sync_year()


    def _authenticate(self):

        Authenticate()
        Initialize(project=self.project_id)
        self.downloader = DriveDownloader(self.credentials)

# =========================================================================== #
#                               Public Methods
# =========================================================================== #

    def get_namespace(self):
        namespace = []
        for name in COMMAND_ARGS:
            if(name != "-version"):
                fixed_name = name[1:].replace("-","_")
                namespace.append(fixed_name)
        return namespace

    def change_configuration_from_yaml(self, yaml_path):

        config_data = load_yaml_config(yaml_path)
        # print("changing user config from yaml")
        # print(f"[LOG] config data length: {len(config_data)}")
        # print(config_data)

        if(len(config_data) == 0):
            self._load_default_config(yaml_path)

        else:
            self._load_config(config_data)

    def change_bool_from_args(self, args):
        namespace = self.get_namespace()
        internal_config = args.config == INTERNAL_USER_CONFIG_DIR
        for key in namespace:
            val = getattr(args,key)
            if(internal_config):
                if (key == "force_new_geojson"):
                    self.force_new_geojson = val

                if (key == "export"):
                    self.export = val

                if (key == "download"):
                    self.download = val


def main():
    uf = UserConfig()

if __name__ == "__main__":
    main()
