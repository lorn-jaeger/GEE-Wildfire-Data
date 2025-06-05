import os
import time
import io
import ee


from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from ee_wildfire.UserInterface import ConsoleUI
from ee_wildfire.constants import SCOPES, AUTH_TOKEN_PATH

from pathlib import Path
from tqdm import tqdm
from typing import Union


class DriveDownloader:
    """
    Handles downloading files from Google Drive using OAuth credentials.
    Supports folder and individual file downloads.
    """
    def __init__(self, credentials:Union[Path,str], google_drive_dir:str):
        """
        Args:
            credentials_path: Path to the OAuth credentials JSON file.
        """
        self.creds = credentials
        self.service = self._get_drive_service()
        self.folderID = self._get_folder_id(google_drive_dir)
        
    def _get_drive_service(self):
        creds = None
        if os.path.exists(AUTH_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(AUTH_TOKEN_PATH, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(AUTH_TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)

    def _get_folder_id(self, folder_path: str) -> str:
        """
        Traverse Google Drive folders to retrieve the folder ID.
        """
        parts = folder_path.strip('/').split('/')
        parent_id = 'root'
        
        for part in parts:
            query = f"name='{part}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if not items:
                raise ValueError(f"Folder '{part}' not found in path '{folder_path}'")
            parent_id = items[0]['id']
            
        return parent_id

    def download_folder(self, drive_folder_path: str, local_path: str):
        """Download all files from the specified Drive folder."""
        try:
            folder_id = self._get_folder_id(drive_folder_path)
            # TODO: Check if I even need do the path stuff. It should be handled by UserConfig.py
            output_dir = Path(local_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all files in the folder with pagination
            files = []
            page_token = None
            while True:
                results = self.service.files().list(
                    q=f"'{folder_id}' in parents",
                    spaces='drive',
                    pageSize=1000,
                    fields='nextPageToken, files(id, name)',
                    pageToken=page_token
                ).execute()
                files.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            ConsoleUI.print(f"Found {len(files)} files")
            
            ConsoleUI.add_bar(key="download", total=len(files), desc="Downloading files")
            for file in files:
                request = self.service.files().get_media(fileId=file['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                
                output_path = output_dir / file['name']
                with open(output_path, 'wb') as f:
                    f.write(fh.getvalue())

                ConsoleUI.update_bar("download")
                    
        except Exception as e:
            ConsoleUI.print(f"Error downloading folder: {str(e)}")
            raise

    def get_files_in_drive(self):
        folder_id = self.folderID
        results = self.service.files().list(
            q=f"'{folder_id}' in parents and mimeType='image/tiff' and trashed=false",
            spaces="drive",
            fields="files(id, name)"
        ).execute()
        files = results.get("files",[])
        found_files = {f['name'] for f in files}
        return found_files, files


    def download_files(self, local_path: Path, expected_files: list):
        ConsoleUI.add_bar(key="download",total=len(expected_files), desc="Export progress")
        while True:
            found_names, files = self.get_files_in_drive()
            current_missing = set(expected_files) - found_names

            # FIX: Bar is not updating correctly here
            # ConsoleUI.print(f"{len(expected_files)-len(current_missing)} : {len(expected_files)}")
            # ConsoleUI.update_bar(key="download",n=(len(expected_files)-len(current_missing)))
            ConsoleUI.set_bar_position(key="download", value=(len(expected_files) - len(current_missing)))

            if not current_missing:
                ConsoleUI.print("All files found!")
                break

            else:
                time.sleep(10)


        # Build a dict for easy access
        file_map = {f['name']: f for f in files if f['name'] in expected_files}

        ConsoleUI.add_bar(key="download", total=len(expected_files), desc="Download progress")
        for fname in expected_files:
            file = file_map[fname]
            request = self.service.files().get_media(fileId=file['id'])
            file_path = os.path.join(local_path, fname)

            fh = io.FileIO(file_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            ConsoleUI.update_bar(key="download")

        ConsoleUI.close_bar(key="download")

    # FIX: This requires permissions that are not provided by the scope of drive.readonly
    # in order for this to work you must either; use full scope and have google not verify the app or to tie a service account to the program.
    def purge_data(self):
        try:
            while True:
                _, files = self.get_files_in_drive()

                for f in files:
                    try:
                        self.service.files().delete(fileId=f['id']).execute()
                        print(f"Deleted: {f['name']}")

                    except HttpError as error:
                        print(f"Failed to delete {f['name']}: {error}")

                if len(files) == 0:
                    break



        except HttpError as e:
            print(f"An error occured: {e}")
            raise




def main():
    from ee_wildfire.UserConfig.UserConfig import UserConfig
    uf = UserConfig()
    # exported_files = [
    #     "Image_Export_fire_24845541_2021-01-08.tif",
    #     "Image_Export_fire_24845541_2021-01-06.tif",
    # ]
    # print(uf.downloader.download_files(DEFAULT_TIFF_DIR, exported_files))
    # uf.downloader.purge_data()
    uf.downloader.check_export_completion()


if __name__ == '__main__':
    main()
