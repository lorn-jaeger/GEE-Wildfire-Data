import ee
import time
from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.UserConfig.authentication import AuthManager
from ee_wildfire.ExportQueue.QueueManager import QueueManager
from ee_wildfire.constants import *

from ee_wildfire.utils import google_drive_util
from ee_wildfire.drive_downloader import DriveDownloader

from pathlib import Path
import json

SERVICE_ACCOUNT = Path("/home/kyle/NRML/OAuth/service-account-credentials.json")
DRIVE_DIR = 'EE-Wildfire-Test'

def __auth(verb=False):
    uf = UserConfig()
    ConsoleUI.set_verbose(verb)
    ConsoleUI.write(str(uf))
    # uf.authenticate()
    auth = AuthManager(SERVICE_ACCOUNT)
    return auth

def test_export_queue_pull():
    __auth()
    expected_files = [
        "Image_Export_fire_25205533_2021-05-30.tif",
        "Image_Export_fire_25205529_2021-06-14.tif",
        "Image_Export_fire_25205529_2021-06-13.tif",
        "Image_Export_fire_25205529_2021-06-12.tif",
        "Image_Export_fire_25205529_2021-06-11.tif",
    ]
    files = google_drive_util._strip_tif_extention(expected_files)
    filtered_tasks = google_drive_util.get_completed_tasks_versus_list(expected_files)
    assert len(files) == len(filtered_tasks), "Tasks list not the same"

def test_download():
    uf = __auth(True)
    dl = DriveDownloader(uf)
    expected_files = [
        "Image_Export_fire_25205533_2021-05-30.tif",
        "Image_Export_fire_25205529_2021-06-14.tif",
        "Image_Export_fire_25205529_2021-06-13.tif",
        "Image_Export_fire_25205529_2021-06-12.tif",
        "Image_Export_fire_25205529_2021-06-11.tif",
    ]
    # dl_files, dl_something_else = dl.get_files_in_drive()
    # files = google_drive_util.get_completed_tasks_versus_list(expected_files)
    # print(dl_files)
    # print(dl_something_else)
    uf.exported_files = expected_files
    dl.download_files()

def test_others():
    auth = AuthManager(SERVICE_ACCOUNT)
    ConsoleUI.setup_logging(DEFAULT_LOG_DIR, "debug")

    ConsoleUI.add_bar(key="export_queue",
                      total= EXPORT_QUEUE_SIZE,
                      desc="Google Earth Export Queue")
    # Example: queue two dummy exports
    for i in range(25):
        img = ee.Image(1).rename(f"const_{i}")
        desc = f"test_const_{i}"
        name = f"Test_{i}"
        folder="EE-Wildfire-Test"
        # ConsoleUI.print(f"[TEST] - {name} : {desc}")
        QueueManager.add_export(
            image=img,
            description=desc,
            filename=f"Test_const_{i}",
            google_drive_folder=folder,
            max_pixels=100000
        )

    QueueManager.wait_for_exports()




if __name__ == "__main__":
    test_others()


