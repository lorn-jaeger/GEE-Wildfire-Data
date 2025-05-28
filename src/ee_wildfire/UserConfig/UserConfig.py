
from csv import Error

from ee_wildfire.utils.yaml_utils import *
from ee_wildfire.constants import *
from ee_wildfire.drive_downloader import DriveDownloader
from ee_wildfire.get_globfire import get_combined_fires

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
        self._get_geodataframe()

    def __str__(self):
        # TODO: add start/end date. remove year and month
        output_str = [
            f"Project ID:                       {self.project_id}",
            f"Year:                             {self.year}",
            f"Min Size:                         {self.min_size}",
            f"Data directory path               {self.data_dir}",
            f"Google Drive path                 {self.google_drive_dir}",
            f"Credentials path:                 {self.credentials}",
            f"Tiff directory path:              {self.tiff_dir}",
            f"Are you downloading?              {self.download}",
            f"Are you exporting data?           {self.export}",
            f"Start date:                       {self.start_date}",
            f"End date:                         {self.end_date}",
        ]

        return "\n".join(output_str)
        # return str(self._to_dict())
    def _authenticate(self):

        Authenticate()
        Initialize(project=self.project_id)
        self.downloader = DriveDownloader(self.credentials)

    def _load_default_config(self,path):
        print(f"No user configuration found at '{path}'. Loading default.")
        self.project_id = DEFAULT_PROJECT_ID 
        self.start_date = DEFAULT_START_DATE
        self.end_date = DEFAULT_END_DATE
        self.data_dir = DEFAULT_DATA_DIR
        self.credentials = self.data_dir/ "OAuth" / "credentials.json"
        self.year = str(self.start_date.year)
        self.min_size = DEFAULT_MIN_SIZE
        self.tiff_dir = self.data_dir / "tiff" / self.year
        self.download = False
        self.export = False
        # TODO: do i need this? we generate the geodata frame everytime the program is called

        self._validate_paths()
        self._save_config()


    def _save_config(self):
        save_yaml_config(self._to_dict(), INTERNAL_USER_CONFIG_DIR)

    # loading from already built yaml user config
    def _load_config(self, config_data):
        self.start_date = config_data['start_date']
        self.end_date = config_data['end_date']
        self.project_id = config_data['project_id']
        self.data_dir = Path(config_data['data_dir']).expanduser()
        self.year = str(self.start_date.year)
        self.tiff_dir = self.data_dir / "tiff" / self.year
        self.credentials = self.data_dir / "OAuth" / "credentials.json"
        self.download = config_data['download']
        self.export = config_data['export']
        self.min_size = config_data['min_size']
        # self.geodataframe = self._get_geodataframe()

        self._validate_paths()
        self._save_config()

    def _to_dict(self):
        config_data = {
            'project_id':self.project_id,
            'data_dir': str(self.data_dir),
            'credentials':str(self.credentials),
            'start_date':self.start_date,
            'end_date':self.end_date,
            # 'tiff_dir':str(self.tiff_dir),
            'drive_dir':self.google_drive_dir,
            'download':self.download,
            'export':self.export,
            'min_size':self.min_size,
        }
        return config_data

    def _validate_and_sync_time(self):
        # FIX: this needs to work for yyyy-mm-dd kind of dates

        # validate year
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
        try_make_path(self.tiff_dir)
        self._validate_and_sync_time()

    def _get_geodataframe(self):
        print("Generating GeoDataFrame...")
        self.geodataframe = get_combined_fires(self)



    def _get_namespace(self):
        namespace = []
        for name in COMMAND_ARGS:
            if(name != "-version"):
                fixed_name = name[1:].replace("-","_")
                namespace.append(fixed_name)
        return namespace
# =========================================================================== #
#                               Public Methods
# =========================================================================== #


    def change_configuration_from_yaml(self, yaml_path):

        config_data = load_yaml_config(yaml_path)

        if(len(config_data) == 0):
            self._load_default_config(yaml_path)

        else:
            self._load_config(config_data)

    def change_bool_from_args(self, args):
        namespace = self._get_namespace()
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
    print(uf)
    print(uf.geodataframe)

if __name__ == "__main__":
    main()
