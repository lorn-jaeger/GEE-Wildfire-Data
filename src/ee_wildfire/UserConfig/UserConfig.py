


from ee_wildfire.utils.yaml_utils import load_yaml_config, save_yaml_config
from ee_wildfire.constants import *
from ee_wildfire.drive_downloader import DriveDownloader
from ee_wildfire.get_globfire import get_combined_fires

from ee import Authenticate #type: ignore
from ee import Initialize

import os

from typing import Union, Dict, Any


default_values: Dict[str, Any] = {
    "project_id": DEFAULT_PROJECT_ID,
    "start_date": DEFAULT_START_DATE,
    "end_date": DEFAULT_END_DATE,
    "google_drive_dir": DEFAULT_GOOGLE_DRIVE_DIR,
    "min_size": DEFAULT_MIN_SIZE,
    "max_size": DEFAULT_MAX_SIZE,
    "credentials":DEFAULT_OAUTH_DIR,
    "data_dir": DEFAULT_DATA_DIR,
    "tiff_dir": DEFAULT_TIFF_DIR,
    "export": False,
    "download": False,
}

class UserConfig:
    """
    User configuration class for managing Earth Engine access, paths,
    and project-specific configuration loaded from a YAML file.

    Handles authentication, validation of user input, and integration
    with Google Drive and geospatial fire datasets.
    """

    def __init__(self, yaml_path: Union[Path,str] = INTERNAL_USER_CONFIG_DIR):
        """
        Initialize the UserConfig object by loading and validating the configuration.

        Args:
            yaml_path (Union[Path,str]): Path to the user configuration YAML file.
        """
        self.change_configuration_from_yaml(yaml_path)

        self._validate_paths()
        self._validate_time()
        self._authenticate()

        self.exported_files = []


    def __str__(self) -> str:
        """
        String representation of the configuration for display or debugging.

        Returns:
            str: Human-readable representation of the current config state.
        """
        output_string = ""
        attrs = self.__dict__
        for key in attrs:
            output_string += f"{key}: {attrs[key]}\n"

        return output_string

    def _authenticate(self) -> None:
        """
        Authenticate with Google Earth Engine and initialize the DriveDownloader.
        """
        Authenticate()
        Initialize(project=self.project_id)
        self.downloader = DriveDownloader(self.credentials)

    def _validate_paths(self) -> None:
        """
        Ensure necessary file system paths exist or are created.
        Raises:
            FileNotFoundError: If credentials file does not exist.
        """
        if not os.path.exists(self.credentials):
            raise FileNotFoundError(f"{self.credentials} not found!")

        self._try_make_path(self.data_dir)
        self._try_make_path(self.tiff_dir)

    def _validate_time(self) -> None:
        """
        Validate that the start and end dates are within allowed bounds.
        Raises:
            IndexError: If date ranges are outside of accepted year limits or incorrectly ordered.
        """
        start_year = int(self.start_date.year)
        end_year = int(self.end_date.year)

        if(start_year < MIN_YEAR):
            raise IndexError(f"Querry year '{start_year}' is smaller than the minimum year {MIN_YEAR}")

        if(start_year > MAX_YEAR):
            raise IndexError(f"Querry year '{start_year}' is larger than the maximum year {MAX_YEAR}")

        if(end_year < MIN_YEAR):
            raise IndexError(f"Querry year '{end_year}' is smaller than the minimum year {MIN_YEAR}")

        if(end_year > MAX_YEAR):
            raise IndexError(f"Querry year '{end_year}' is larger than the maximum year {MAX_YEAR}")


        if(self.start_date > self.end_date):
            raise IndexError(f"start date '{self.start_date}' is after end date '{self.end_date}'")


    def _try_make_path(self, path: Path) -> None:
        """
        Attempt to create a directory if it does not already exist.

        Args:
            path (Path): Directory path to create.
        """
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except PermissionError:
                print(f"Permission denied: Unable to create '{path}'")

    def _get_args_namespace(self) -> list[str]:
        """
        Build a list of normalized command-line argument keys.

        Returns:
            List[str]: A list of keys stripped of dashes and converted to snake_case.
        """
        namespace = []
        for name in COMMAND_ARGS:
            if(name != "-version"):
                fixed_name = name[1:].replace("-","_")
                namespace.append(fixed_name)
        return namespace

# =========================================================================== #
#                               Public Methods
# =========================================================================== #

    def get_geodataframe(self) -> None:
        """
        Load the combined fire geodataframe and assign it to `self.geodataframe`.
        """
        self.geodataframe = get_combined_fires(self)

    def change_configuration_from_yaml(self, yaml_path: Union[Path,str]) -> None:
        """
        Load and apply configuration from a YAML file, falling back to defaults if necessary.

        Args:
            yaml_path (Union[Path,str]): Path to the YAML config file.
        """
        config_data = load_yaml_config(yaml_path)

        for key in default_values.keys():
            if key not in config_data:
                config_data[key] = default_values[key]

            setattr(self, key ,config_data[key])

        save_yaml_config(self.__dict__, INTERNAL_USER_CONFIG_DIR)

    def change_bool_from_args(self, args: Any) -> None:
        """
        Update internal boolean flags (`export`, `download`) from parsed CLI arguments.

        Args:
            args (Any): Parsed argparse namespace object.
        """
        namespace = self._get_args_namespace()
        internal_config = args.config == INTERNAL_USER_CONFIG_DIR
        for key in namespace:
            val = getattr(args,key)
            if(internal_config):

                if (key == "export"):
                    self.export = val

                if (key == "download"):
                    self.download = val



def main():
    outside_config_path = HOME / "NRML" / "outside_config.yml"
    uf = UserConfig(outside_config_path)
    print(getattr(uf, "downloader"))

if __name__ == "__main__":
    main()
