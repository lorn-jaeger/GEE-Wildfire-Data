from ee_wildfire.UserInterface import ConsoleUI
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.oauth2 import service_account

import json
import ee


class AuthManager:
    def __init__(self, auth_mode="oauth", service_json=None, oauth_json=None):
        self.auth_mode = auth_mode
        self.service_json = service_json
        self.oauth_json = oauth_json

    def authenticate_earth_engine(self):
        if self.auth_mode == "service_account":
            self.ee_creds = ee.ServiceAccountCredentials(email=json.load(open(self.service_json))['client_email'],
                                                 key_file=str(self.service_json))
            # creds = service_account.Credentials.from_service_account_file(self.service_json, scopes=SCOPES)
            ee.Initialize(self.ee_creds)
        elif self.auth_mode == "oauth":
            ee.Authenticate()  # launches browser
            ee.Initialize()
        else:
            raise ValueError("Unsupported Earth Engine auth mode.")

        ConsoleUI.print("Google Earth autheticated succesfully.")

    def authenticate_drive(self):
        """Authenticate Google Drive using a service account."""
        SCOPES = ['https://www.googleapis.com/auth/drive']
        try:
            self.drive_creds= service_account.Credentials.from_service_account_file(
                self.service_json,
                scopes=SCOPES
            )
            self.drive_service = build('drive', 'v3', credentials=self.drive_creds)
            ConsoleUI.print("Google Drive authenticated successfully.")
        except FileNotFoundError:
            # FIX: Here is where i can prompt user for json file
            ConsoleUI.print(f"Could not find service account JSON at {self.service_json}", color="red")
        except HttpError as error:
            ConsoleUI.print(f"An error occurred during Drive auth: {error}", color="red")

        return self.service_json


    def get_project_id(self) -> str:
        return str(self.ee_creds.project_id)

def main():
    am = AuthManager(
        auth_mode="service_account",
        service_json="/home/kyle/NRML/OAuth/service-account-credentials.json",
        # oauth_json="/home/kyle/NRML/OAuth/user-account-credentials.json",
    )
    am.authenticate_earth_engine()
    am.authenticate_drive()
    print(am.get_project_id())

if __name__ == "__main__":
    main()
