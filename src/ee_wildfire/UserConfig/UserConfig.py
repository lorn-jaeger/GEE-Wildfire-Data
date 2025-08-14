import argparse
import json
import os
import pprint
from typing import Any, Dict, List, Union

from ee_wildfire.constants import *
from ee_wildfire.globfire import get_fires, load_fires, save_fires
from ee_wildfire.UserConfig.authentication import AuthManager
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.utils.yaml_utils import load_yaml_config, save_yaml_config


class UserConfig:
    """
    User configuration class for managing Earth Engine access, paths,
    and project-specific configuration loaded from a YAML file.

    Handles authentication, validation of user input, and integration
    with Google Drive and geospatial fire datasets.
    """

    # =========================================================================== #
    #                               Dunder Methods
    # =========================================================================== #

    def __init__(self, args: dict):
        """
        Initialize the UserConfig object by loading and validating the configuration.
        """
        self._data = args

        for key, val in args.items():
            setattr(self, key, val)

        self.validate()

    def __repr__(self) -> str:
        output_str = "UserConfig\n"
        for key, value in self.__dict__.items():
            output_str += f"{key} {value}\n"
        return output_str

    def __str__(self) -> str:
        items_to_exclude = [
            "exported_files",
            "failed_exports",
            "bounding_area",
        ]
        config_items = {
            k: str(v)
            for k, v in self.__dict__.items()
            if (not k.startswith("_")) and (k not in items_to_exclude)
        }

        sorted_items = dict(sorted(config_items.items()))

        # Format nicely using pprint
        return "\n".join(
            [
                "╭─ User Configuration ─────────────────────────────────────────────────────────────────────────────",
                *[
                    f"│ {key:<20} : {pprint.pformat(value)}"
                    for key, value in sorted_items.items()
                ],
                "╰──────────────────────────────────────────────────────────────────────────────────────────────────",
            ]
        )

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    # =========================================================================== #
    #                               Private Methods
    # =========================================================================== #

    def _try_make_path(self, path: Path) -> None:
        """
        Attempt to create a directory if it does not already exist.

        Args:
            path (Path): Directory path to create.
        """
        ConsoleUI.debug(f"Trying to make path: {path}")
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except PermissionError:
                print(f"Permission denied: Unable to create '{path}'")

    def _normalize_path(self, path: Path):
        return Path(path).expanduser().resolve()

    def _validate_logs(self) -> None:
        if hasattr(self, "log_level"):
            if self.log_level not in LOG_LEVELS.keys():
                ConsoleUI.debug(
                    f"{self.log_level} is not in {LOG_LEVELS.keys()}, setting to default {DEFAULT_LOG_LEVEL}"
                )
                self.log_dir = DEFAULT_LOG_LEVEL

    def _validate_service_account_file(self, path: Path) -> bool:
        try:
            with open(path, "r") as f:
                data = json.load(f)

            required_fields = [
                "type",
                "private_key_id",
                "private_key",
                "client_email",
                "client_id",
                "auth_uri",
                "token_uri",
                "auth_provider_x509_cert_url",
                "client_x509_cert_url",
            ]
            self._missing = [field for field in required_fields if field not in data]
            ConsoleUI.debug(f"Service account JSON is missing {self._missing}")
            return all(field in data for field in required_fields)

        except (json.JSONDecodeError, FileNotFoundError):
            return False

    def _validate_paths(self) -> None:
        """
        Ensure necessary file system paths exist or are created.
        Raises:
            FileNotFoundError: If credentials file does not exist.
        """
        path_attrs = [
            "config",
            "tiff_dir",
            "gdf_dir",
            "log_dir",
            "credentials",
        ]

        for pa in path_attrs:
            setattr(self, pa, self._normalize_path(getattr(self, pa)))
            ConsoleUI.debug(f"Item {pa} has path {getattr(self, pa)}")

        # Sync data directory
        self.data_dir = self._normalize_path(self.data_dir)
        if self.data_dir != self._normalize_path(DEFAULT_DATA_DIR):

            if self.tiff_dir == DEFAULT_TIFF_DIR:
                self.tiff_dir = Path(self.data_dir / "tiff")

            if self.gdf_dir == DEFAULT_GDF_DIR:
                self.gdf_dir = Path(self.data_dir / "gdfs")

        # make all the paths
        self._try_make_path(self.tiff_dir)
        self._try_make_path(self.log_dir)
        self._try_make_path(self.gdf_dir)
        self._try_make_path(self.data_dir)

        # prompt user for service credentials if not found
        num_retries = 3
        service_exists = os.path.exists(self.credentials)
        ConsoleUI.debug(f"Service credentials path exists: {service_exists}")
        while not service_exists:
            if num_retries <= 0:
                ConsoleUI.error(
                    f"Google service credentials JSON {self.credentials} not found!"
                )
                raise FileNotFoundError(
                    f"Google cloud service account file not found at {self.credentials}"
                )

            ConsoleUI.print(
                f"Google service credentials JSON {self.credentials} not found!",
                color="red",
            )
            self.credentials = os.path.expanduser(ConsoleUI.prompt_path())

            service_exists = os.path.exists(self.credentials)
            num_retries -= 1

        # validate service credentials format
        valid_service = self._validate_service_account_file(Path(self.credentials))
        ConsoleUI.debug(f"Service credentials validation: {valid_service}")
        num_retries = 3
        while not valid_service:
            if num_retries <= 0:
                ConsoleUI.error(
                    f"Google service credentials JSON {self.credentials} incorrect format! {self._missing}"
                )
                raise ValueError(
                    f"Google cloud service account at {self.credentials} is not in the right format."
                )

            ConsoleUI.print(
                f"Google service credentials JSON {self.credentials} is not in the correct format!",
                color="red",
            )
            self.credentials = os.path.expanduser(ConsoleUI.prompt_path())

            valid_service = self._validate_service_account_file(Path(self.credentials))
            num_retries -= 1

    def _validate_time(self) -> None:
        """
        Validate that the start and end dates are within allowed bounds.
        Raises:
            IndexError: If date ranges are outside of accepted year limits or incorrectly ordered.
        """
        if hasattr(self, "start_date") and hasattr(self, "end_date"):
            # Convert date and time if passed as string
            try:
                if isinstance(self.start_date, str):
                    self.start_date = datetime.strptime(self.start_date, DATE_FORMAT)

                if isinstance(self.end_date, str):
                    self.end_date = datetime.strptime(self.end_date, DATE_FORMAT)

            except ValueError as e:
                raise ValueError(f"Invalid date format: {e}")
            start_year = int(self.start_date.year)
            end_year = int(self.end_date.year)

            if start_year < MIN_YEAR:
                raise IndexError(
                    f"Querry year '{start_year}' is smaller than the minimum year {MIN_YEAR}"
                )

            if start_year > MAX_YEAR:
                raise IndexError(
                    f"Querry year '{start_year}' is larger than the maximum year {MAX_YEAR}"
                )

            if end_year < MIN_YEAR:
                raise IndexError(
                    f"Querry year '{end_year}' is smaller than the minimum year {MIN_YEAR}"
                )

            if end_year > MAX_YEAR:
                raise IndexError(
                    f"Querry year '{end_year}' is larger than the maximum year {MAX_YEAR}"
                )

            if self.start_date > self.end_date:
                raise IndexError(
                    f"start date '{self.start_date}' is after end date '{self.end_date}'"
                )

    # =========================================================================== #
    #                               Public Methods
    # =========================================================================== #

    def validate(self) -> None:
        self._validate_paths()
        self._validate_time()
        self._validate_logs()

    def authenticate(self) -> None:
        """
        Authenticate with Google Earth Engine and initialize the DriveDownloader.
        """
        self.auth = AuthManager(
            service_json=self.credentials,
        )
        self.drive_service = self.auth.get_drive_service()
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


if __name__ == "__main__":
    uf = UserConfig()
    print(uf._validate_yaml())
