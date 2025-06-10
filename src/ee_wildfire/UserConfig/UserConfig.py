


from ee_wildfire.UserInterface import ConsoleUI
from ee_wildfire.utils.yaml_utils import load_yaml_config, save_yaml_config
from ee_wildfire.constants import *
from ee_wildfire.globfire import get_fires, load_fires, save_fires
from ee_wildfire.UserConfig.authentication import AuthManager


import argparse
import os
import pprint
import json

from typing import Union



class UserConfig:
    """
    User configuration class for managing Earth Engine access, paths,
    and project-specific configuration loaded from a YAML file.

    Handles authentication, validation of user input, and integration
    with Google Drive and geospatial fire datasets.
    """

    def __init__(self):
        """
        Initialize the UserConfig object by loading and validating the configuration.
        """

        self._load_from_internal_config()
        self.exported_files = []
        self.failed_exports = []



    def __repr__(self) -> str:
        output_str = "UserConfig\n"
        for key, value in self.__dict__.items():
            output_str += f"{key} {value}"
        return(output_str)

    def __str__(self) -> str:
        items_to_exclude = [
            "exported_files",
            "failed_exports",
        ]
        config_items = {
            k: str(v)
            for k, v in self.__dict__.items()
            if (not k.startswith('_')) and (k not in items_to_exclude)
        }

        sorted_items = dict(sorted(config_items.items()))

        # Format nicely using pprint
        return "\n".join([
            "╭─ User Configuration ─────────────────────────────────────────────────────────────────────────────",
            *[f"│ {key:<20} : {pprint.pformat(value)}" for key, value in sorted_items.items()],
            "╰──────────────────────────────────────────────────────────────────────────────────────────────────"
        ])
    def _validate_service_account_file(self, path: Path) -> bool:
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            required_fields = [
                "type", "project_id", "private_key_id", "private_key",
                "client_email", "client_id", "auth_uri", "token_uri",
                "auth_provider_x509_cert_url", "client_x509_cert_url"
            ]
            self._missing = [field for field in required_fields if field not in data]
            return all(field in data for field in required_fields)
        
        except (json.JSONDecodeError, FileNotFoundError):
            return False

    def _validate_paths(self) -> None:
        """
        Ensure necessary file system paths exist or are created.
        Raises:
            FileNotFoundError: If credentials file does not exist.
        """

        if hasattr(self, 'config'):
            self.config = Path(os.path.abspath(self.config))

        if hasattr(self, 'tiff_dir'):
            self.tiff_dir = Path(os.path.abspath(self.tiff_dir))
            self._try_make_path(self.tiff_dir)

        if hasattr(self, "log_dir"):
            self.log_dir = Path(os.path.abspath(self.log_dir))
            self._try_make_path(self.log_dir)

        if hasattr(self,'credentials'):
            self.credentials = Path(os.path.abspath(self.credentials))
            # prompt user for service credentials if not found
            num_retries = 3
            while not os.path.exists(self.credentials):
                # FIX: Raise error here
                if(num_retries <= 0):
                    ConsoleUI.error(f"Google service credentials JSON {self.credentials} not found!")
                    raise FileNotFoundError(f"Google cloud service account file not found at {self.credentials}")

                ConsoleUI.print(f"Google service credentials JSON {self.credentials} not found!", color="red")
                self.credentials = os.path.expanduser(ConsoleUI.prompt_path())
                num_retries -= 1

            # validate service credentials format
            # print(self._validate_service_account_file(Path(self.credentials)))
            num_retries = 3
            while not self._validate_service_account_file(Path(self.credentials)):
                # FIX: Raise error here
                if(num_retries <= 0):
                    ConsoleUI.error(f"Google service credentials JSON {self.credentials} incorrect format! {self._missing}")
                    raise ValueError(f"Google cloud service account at {self.credentials} is not in the right format.")

                ConsoleUI.print(f"Google service credentials JSON {self.credentials} is not in the correct format!", color="red")
                self.credentials = os.path.expanduser(ConsoleUI.prompt_path())
                num_retries -= 1



        # Sync data directory
        if hasattr(self, 'data_dir'):
            self.data_dir = Path(os.path.abspath(self.data_dir))
            if (self.data_dir != os.path.abspath(DEFAULT_DATA_DIR)):

                if(self.tiff_dir == os.path.abspath(DEFAULT_TIFF_DIR)):
                    self.tiff_dir = Path(self.data_dir / 'tiff')

                if(self.log_dir == os.path.abspath(DEFAULT_LOG_DIR)):
                    self.log_dir = Path(self.data_dir / 'logs')

            self._try_make_path(self.data_dir)



    def _validate_time(self) -> None:
        """
        Validate that the start and end dates are within allowed bounds.
        Raises:
            IndexError: If date ranges are outside of accepted year limits or incorrectly ordered.
        """
        if(hasattr(self, "start_date") and hasattr(self, "end_date")):
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

    def _fill_namespace(self, namespace: dict) -> None:
        for key, item in namespace.items():
            setattr(self, key, item)

    def _save_to_internal_config_file(self):
        save_yaml_config(self.__dict__, INTERNAL_USER_CONFIG_DIR)

    def _load_from_internal_config(self):
        if os.path.exists(INTERNAL_USER_CONFIG_DIR):
            config_data = load_yaml_config(INTERNAL_USER_CONFIG_DIR)
            self._fill_namespace(config_data)

        self._validate_paths()
        self._validate_time()

# =========================================================================== #
#                               Public Methods
# =========================================================================== #

    def authenticate(self) -> None:
        """
        Authenticate with Google Earth Engine and initialize the DriveDownloader.
        """
        self.auth = AuthManager(
            service_json=self.credentials,
        )
        self.auth.authenticate_drive()
        self.auth.authenticate_earth_engine()
        self.drive_service = self.auth.drive_service
        self.project_id = self.auth.get_project_id()

    def get_geodataframe(self) -> None:
        """
        Load the combined fire geodataframe and assign it to `self.geodataframe`.
        """
        try:
           load_fires(self) 
        except:
            self.geodataframe = get_fires(self)
            save_fires(self)

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
        self._save_to_internal_config_file()

    def change_configuration_from_args(self, args: argparse.Namespace):
        """
        Update internal boolean flags (`export`, `download`) from parsed CLI arguments.

        Args:
            args (Any): Parsed argparse namespace object.
        """
        explicit = getattr(args, "_explicit_args", set())
        bool_keys = self._get_bools()
        all_keys = self._get_args_namespace()

        for key in all_keys:
            arg_val = getattr(args, key)

            # Always set booleans (they're binary state toggles)
            if key in bool_keys:
                setattr(self, key, arg_val)
                continue

            # Set if the attribute doesn't exist
            if not hasattr(self, key):
                setattr(self, key, arg_val)
                continue

            # Only override if user explicitly passed it
            if key in explicit:
                setattr(self, key, arg_val)

        self._validate_paths()
        self._validate_time()
        self._save_to_internal_config_file()

def delete_user_config() -> None:
    """
    Deletes the user_config.yml file if it exists.

    Args:
        path (Path): Path to the config file. Defaults to standard location.
    """
    path = Path(INTERNAL_USER_CONFIG_DIR)
    try:
        if path.exists():
            path.unlink()
            ConsoleUI.print(f"Deleted config file: {path}")
        else:
            ConsoleUI.print(f"No config file found at: {path}", color="yellow")
    except Exception as e:
        ConsoleUI.print(f"Failed to delete config file: {e}", color="red")

def main():
    outside_config_path = HOME / "NRML" / "outside_config.yml"

if __name__ == "__main__":
    main()
