import os
import time
import io
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface import ConsoleUI

from ee_wildfire.utils.google_drive_util import get_active_tasks_in_export_queue

from pathlib import Path


class DriveDownloader:
    """
    Handles downloading files from Google Drive using OAuth credentials.
    Supports folder and individual file downloads.
    """
    def __init__(self, config: UserConfig):
        """
        Args:
            credentials_path: Path to the OAuth credentials JSON file.
        """
        self.config = config
        # self.creds = credentials
        self.service = config.drive_service
        self.folderID = self.get_folder_id()
        ConsoleUI.debug(self)

    def __repr__(self) -> str:
        output_str = "DriveDownloader.py\n"
        for key, value in self.__dict__.items():
            if key != "config":
                output_str += f"{key} {value}\n"
        return(output_str)
        
    def get_folder_id(self):
        service = self.service
        folder_name = self.config.google_drive_dir
        response = service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        folders = response.get('files', [])
        if not folders:
            raise Exception(f"No folder found with name: {folder_name}")
        return folders[0]['id']

    def download_folder(self):
        """Download all files from the specified Drive folder."""
        folder_id = self.folderID
        local_path = self.config.tiff_dir
        try:
            # TODO: Check if I even need do the path stuff. It should be handled by UserConfig.py
            output_dir = Path(local_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all files in the folder with pagination
            files = []
            page_token = None
            while True:
                ConsoleUI.print(f"Searching for files...")
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
        query = f"'{folder_id}' in parents and mimeType='image/tiff' and trashed=false"
        
        all_files = []
        page_token = None

        ConsoleUI.print("Searching for files in google drive.")
        while True:
            response = self.service.files().list(
                q=query,
                spaces="drive",
                pageSize=1000,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token
            ).execute()

            all_files.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)

            if not page_token:
                break

        return all_files


    def download_files(self):
        local_path = self.config.tiff_dir
        expected_files = self.config.exported_files

        ConsoleUI.add_bar(key="download",total=len(expected_files), desc="Export progress")

        # wait on export queue
        while True:

            active_tasks = get_active_tasks_in_export_queue()
            files = [f['description']+".tif" for f in active_tasks]
            common = set(files) & set(expected_files)

            ConsoleUI.set_bar_position(key="download", value=len(expected_files) - len(common))

            if len(active_tasks) == 0:
                ConsoleUI.print("All files found!")
                break
            else:
                ConsoleUI.print(f"{len(active_tasks)} tasks are on the export qeueue.")
                time.sleep(60)

        files_in_drive = self.get_files_in_drive()
        id_map = {f['name']:f['id'] for f in files_in_drive if f['name'] in expected_files}

        ConsoleUI.add_bar(key="download", total=len(expected_files), desc="Download progress")
        for fname in expected_files:
            fileId = id_map[fname]
            try:
                request = self.service.files().get_media(fileId=fileId)
                file_path = os.path.join(local_path, fname)

                fh = io.FileIO(file_path, 'wb')
                downloader = MediaIoBaseDownload(fh, request)

                ConsoleUI.print("Downloading files...")
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                ConsoleUI.update_bar(key="download")
            except HttpError as e:
                if e.resp.status == 404:
                    ConsoleUI.print(f"File {fname} not found (404). Skipping...", color="red")
                else:
                    ConsoleUI.print(f"Unexpected error downloaded {fname}: {e}", color="red")




    def purge_data(self):
        ConsoleUI.print("Purging data...")
        try:
            while True:
                files = self.get_files_in_drive()
                ConsoleUI.add_bar(key="purge", total=len(files), desc="Purge progress (for first 1000 items)", color="yellow")
                ConsoleUI.print(f"found {len(files)} files")

                for f in files:
                    try:
                        ConsoleUI.print(f"Deleting {f['name']}")
                        self.service.files().delete(fileId=f['id']).execute()

                    except HttpError as error:
                        ConsoleUI.print(f"Failed to delete {f['name']}: {error}")

                    ConsoleUI.update_bar(key="purge")

                if len(files) == 0:
                    break

        except HttpError as e:
            ConsoleUI.print(f"An error occured: {e}")
            raise





def main():
    from ee_wildfire.constants import HOME
    uf = UserConfig()
    # ConsoleUI.set_verbose(False)
    uf.authenticate()
    dn = DriveDownloader(uf)

    expected = [
        "Image_Export_fire_23655799_2020-01-01.tif",
        "Image_Export_fire_23655799_2020-01-02.tif",
        "Image_Export_fire_23655799_2020-01-03.tif",
    ]
    uf.exported_files = expected

    dn.download_files()



if __name__ == '__main__':
    main()
