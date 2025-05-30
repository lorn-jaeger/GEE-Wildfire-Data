import os
import shutil
import time
import io

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from ee_wildfire.constants import *

from pathlib import Path
from tqdm import tqdm
from typing import Union

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveDownloader:
    """
    Handles downloading files from Google Drive using OAuth credentials.
    Supports folder and individual file downloads.
    """
    def __init__(self, credentials:Union[Path,str]):
        """
        Args:
            credentials_path: Path to the OAuth credentials JSON file.
        """
        self.creds = credentials
        self.service = self._get_drive_service()
        
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
            
            #FIX: Check if this includes the last file name exported. If userconfig recently_exported=True
            tqdm.write(f"Found {len(files)} files")
            
            for file in tqdm(files, desc="Downloading files"):
                request = self.service.files().get_media(fileId=file['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                
                output_path = output_dir / file['name']
                with open(output_path, 'wb') as f:
                    f.write(fh.getvalue())
                    
        except Exception as e:
            tqdm.write(f"Error downloading folder: {str(e)}")
            raise

    def download_files(self, drive_folder_path: str, local_path: Path, expected_files: list):
        folder_id = self._get_folder_id(drive_folder_path)
        time_now = datetime.now()

        # tqdm.write(f"Waiting on exports, this may take a while...")
        while True:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents and mimeType='image/tiff' and trashed=false",
                spaces="drive",
                fields="files(id, name)"
            ).execute()

            files = results.get("files", [])
            found_names = {f['name'] for f in files}
            current_missing = set(expected_files) - found_names
            term_width = shutil.get_terminal_size((80, 20)).columns  # fallback if unknown
            prog_bar = tqdm.format_meter(
                n=len(found_names),
                total=len(expected_files),
                elapsed=(datetime.now() - time_now).total_seconds(),
                prefix="Export progress",
                ncols=term_width,
                unit='file'
            )
            tqdm.write(prog_bar, end="\r")

            if not current_missing:
                tqdm.write("All files found!")
                break

            else:
                time.sleep(10)


        # Build a dict for easy access
        file_map = {f['name']: f for f in files if f['name'] in expected_files}

        for fname in tqdm(expected_files, desc="Download progress", unit='file'):
            file = file_map[fname]
            request = self.service.files().get_media(fileId=file['id'])
            file_path = os.path.join(local_path, fname)

            fh = io.FileIO(file_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

def main():
    from ee_wildfire.UserConfig.UserConfig import UserConfig
    uf = UserConfig()
    exported_files = [
        "Image_Export_fire_24844724_2021-01-12.tif",
        "Image_Export_fire_24844724_2021-01-26.tif",
    ]
    print(uf.downloader.download_files(DEFAULT_GOOGLE_DRIVE_DIR, DEFAULT_TIFF_DIR, exported_files))


if __name__ == '__main__':
    main()
