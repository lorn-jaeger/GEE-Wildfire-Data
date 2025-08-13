import json
import threading
from pathlib import Path
from typing import Optional

import ee
from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from ee_wildfire.UserInterface.UserInterface import ConsoleUI


class AuthManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, service_json: Path):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AuthManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, service_json: Path):

        if self._initialized:
            return
        self._initialized = True

        self.service_json = Path(service_json)
        self.ee_creds = None
        self.drive_creds = None
        self.drive_service: Optional[Resource] = None
        self.__authenticate_drive()
        self.__authenticate_earth_engine()

    def __authenticate_earth_engine(self):
        try:
            self.ee_creds = ee.ServiceAccountCredentials(
                email=json.load(open(self.service_json))["client_email"],
                key_file=str(self.service_json),
            )
            ee.Initialize(credentials=self.ee_creds)
        except Exception as e:
            ConsoleUI.error(f"Failed to authenticate google earth engine: {str(e)}")

        ConsoleUI.print("Google Earth autheticated succesfully.")

    def __authenticate_drive(self):
        """Authenticate Google Drive using a service account."""
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        try:
            self.drive_creds = service_account.Credentials.from_service_account_file(
                self.service_json, scopes=SCOPES
            )
            self.drive_service = build("drive", "v3", credentials=self.drive_creds)
            ConsoleUI.print("Google Drive authenticated successfully.")
        except FileNotFoundError:
            # FIX: Here is where i can prompt user for json file
            ConsoleUI.print(
                f"Could not find service account JSON at {self.service_json}",
                color="red",
            )
        except HttpError as error:
            ConsoleUI.print(
                f"An error occurred during Drive auth: {error}", color="red"
            )

        return self.service_json

    def get_project_id(self) -> str:
        return str(self.ee_creds.project_id)

    def get_drive_service(self) -> Resource:
        return self.drive_service
