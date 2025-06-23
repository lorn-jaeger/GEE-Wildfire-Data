import json
import time
from pathlib import Path

import ee

from ee_wildfire.command_line_args import parse
from ee_wildfire.constants import *
from ee_wildfire.drive_downloader import DriveDownloader
from ee_wildfire.ExportQueue.QueueManager import QueueManager
from ee_wildfire.UserConfig.authentication import AuthManager
from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.utils import google_drive_util

SERVICE_ACCOUNT = Path("/home/kyle/NRML/OAuth/service-account-credentials.json")
DRIVE_DIR = "EE-Wildfire-Test"


def __auth(verb=False):
    uf = UserConfig()
    ConsoleUI.set_verbose(verb)
    ConsoleUI.write(str(uf))
    # uf.authenticate()
    auth = AuthManager(SERVICE_ACCOUNT)
    return auth


def test_others():
    uf = UserConfig()
    uf.authenticate()
    parse()
    auth = AuthManager(SERVICE_ACCOUNT)
    dn = DriveDownloader(uf)

    ConsoleUI.setup_logging(DEFAULT_LOG_DIR, "debug")

    ConsoleUI.add_bar(
        key="export_queue", total=EXPORT_QUEUE_SIZE, desc="Google Earth Export Queue"
    )
    # Example: queue two dummy exports
    for i in range(10):
        img = ee.Image(1).rename(f"const_{i}")
        desc = f"test_const_{i}"
        name = f"Test_{i}"
        folder = "EE-Wildfire-Test"
        # ConsoleUI.print(f"[TEST] - {name} : {desc}")
        QueueManager.add_export(
            image=img,
            description=desc,
            folder=folder,
            max_pixels=100,
            scale=1000000000,
        )
        # cls,
        # image: Image,
        # description: str,
        # max_pixels: float,
        # scale,
        # filename_prefix=None,
        # region=USA_COORDS,
        # crs=CRS_CODE,
        # folder=DEFAULT_GOOGLE_DRIVE_DIR,

    # QueueManager.update_queue()
    QueueManager.wait_for_exports()
    # print(f"Task queue: {QueueManager._task_queue}")
    # print(f"Active tasks: {QueueManager._active_tasks}")
    # print(f"Completed tasks: {QueueManager._completed_tasks}")
    # print(f"File names: {QueueManager.get_task_filename()}")
    dn.download_files()


if __name__ == "__main__":
    test_others()
