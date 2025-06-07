


from ee_wildfire.UserInterface import ConsoleUI
from ee_wildfire.utils.yaml_utils import load_yaml_config, save_yaml_config
from ee_wildfire.constants import *
from ee_wildfire.globfire import get_fires
from ee_wildfire.UserConfig.authentication import AuthManager


import os
import pprint

from typing import Union, Any



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
        self.exported_files = []
        self.failed_exports = []



    def __str__(self) -> str:
        config_items = {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

        # Optional: sort keys for readability
        sorted_items = dict(sorted(config_items.items()))

        # Format nicely using pprint
        return "\n".join([
            "╭─ User Configuration ─────────────────────────────────────────────────────────────────────────────",
            *[f"│ {key:<20} : {pprint.pformat(value)}" for key, value in sorted_items.items()],
            "╰──────────────────────────────────────────────────────────────────────────────────────────────────"
        ])

    def _validate_paths(self) -> None:
        """
        Ensure necessary file system paths exist or are created.
        Raises:
            FileNotFoundError: If credentials file does not exist.
        """

        self.credentials = os.path.abspath(self.credentials)
        self.data_dir = os.path.abspath(self.data_dir)
        self.tiff_dir = os.path.abspath(self.tiff_dir)


        if not os.path.exists(self.credentials):
            # TODO: verbose error is needed here
            ConsoleUI.print(f"{self.credentials} not found!")

        if (self.data_dir != os.path.abspath(DEFAULT_DATA_DIR)):
            if(self.tiff_dir == os.path.abspath(DEFAULT_TIFF_DIR)):
                self.tiff_dir = self.data_dir + '/tiff'


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

        # FIX: Validate new time if put in by command line argument

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
            if(name not in ["--version", "--help"]):
                fixed_name = self._fix_name(name)
                namespace.append(fixed_name)
        return namespace

    def _get_default_values(self):
        values = {}
        for name in COMMAND_ARGS:
            if(name not in ["--version", "--help"]):
                _, default_val, _, _ = COMMAND_ARGS[name]
                fixed_name = self._fix_name(name)
                values[fixed_name] = default_val
        return values

    def _get_bools(self):
        values = []
        for name in COMMAND_ARGS:
            if(name not in ["--version", "--help"]):
                aType, _, _, _ = COMMAND_ARGS[name]
                fixed_name = self._fix_name(name)
                if(aType is None):
                    values.append(fixed_name)
        return values

    def _fix_name(self, name: str) -> str:
        return name[2:].replace("-","_")

    def _fill_namespace(self, namespace) -> None:
        for item in namespace:
            setattr(self, item, None)

# =========================================================================== #
#                               Public Methods
# =========================================================================== #

    def authenticate(self) -> None:
        """
        Authenticate with Google Earth Engine and initialize the DriveDownloader.
        """
        self.auth = AuthManager(
            auth_mode="service_account",
            service_json=self.credentials,
        )
        self.auth.authenticate_earth_engine()
        self.auth.authenticate_drive()
        self.drive_service = self.auth.drive_service
        self.project_id = self.auth.get_project_id()

    def get_geodataframe(self) -> None:
        """
        Load the combined fire geodataframe and assign it to `self.geodataframe`.
        """
        self.geodataframe = get_fires(self)
        # self.geodataframe = get_combined_fires(self)

    def change_configuration_from_yaml(self, yaml_path: Union[Path,str]) -> None:
        """
        Load and apply configuration from a YAML file, falling back to defaults if necessary.

        Args:
            yaml_path (Union[Path,str]): Path to the YAML config file.
        """
        config_data = load_yaml_config(yaml_path)
        defaults = self._get_default_values()
        namespace = defaults.keys()

        # fill in missing config options with default
        for name in namespace:
            if name not in config_data.keys():
                config_data[name] = defaults[name]

        # set the object attributes with fixed config data
        for item, value in config_data.items():
            setattr(self, item, value)


        self._validate_paths()
        self._validate_time()
        self.save_to_internal_config_file()

    def change_configuration_from_args(self, args: Any) -> None:
        """
        Update internal boolean flags (`export`, `download`) from parsed CLI arguments.

        Args:
            args (Any): Parsed argparse namespace object.
        """
        namespace = self._get_args_namespace()
        internal_config = args.config == INTERNAL_USER_CONFIG_DIR
        bool_names = self._get_bools()
        defaults = self._get_default_values()
        for key in namespace:
            val = getattr(args,key)

            if(not hasattr(self, key)):
                setattr(self,key,val)

            if(defaults[key] != val):
                setattr(self,key,val)

            if(bool_names and internal_config):
                if key in bool_names:
                    setattr(self,key,val)




        self._validate_paths()
        self._validate_time()
        self.save_to_internal_config_file()

    def save_to_internal_config_file(self):
        save_yaml_config(self.__dict__, INTERNAL_USER_CONFIG_DIR)




def main():
    outside_config_path = HOME / "NRML" / "outside_config.yml"
    uf = UserConfig(outside_config_path)

if __name__ == "__main__":
    main()
