import ee
from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.UserInterface import ConsoleUI

from ee_wildfire.utils import google_drive_util
from ee_wildfire.drive_downloader import DriveDownloader

from pathlib import Path
import json

SERVICE_ACCOUNT = Path("/home/kyle/NRML/OAuth/service-account-credentials.json")

def __auth(verb=False):
    uf = UserConfig()
    ConsoleUI.set_verbose(verb)
    ConsoleUI.write(str(uf))
    uf.authenticate()
    return uf

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
    creds = ee.ServiceAccountCredentials(email=json.load(open(SERVICE_ACCOUNT))['client_email'],
                                                 key_file=str(SERVICE_ACCOUNT))
    ee.Authenticate()
    ee.Initialize(project='ee-earthdata-459817')
    # ee.Initialize(credentials=creds)
    small_region = ee.Geometry.Rectangle([-122.45, 37.75, -122.44, 37.76])
    image = ee.Image('CGIAR/SRTM90_V4')
    task = ee.batch.Export.image.toDrive(
        image=image,
        description='test_export',
        folder='EE-wildfire-Test',  # or use folder ID instead
        # folder='GoogleEarthEngine',
        fileNamePrefix='test_image',
        scale=30,
        region=small_region,
        maxPixels=1e6,
    )
    task.start()
    print(ee.data.getAssetRoots())

def test_auth():
    uf = __auth()
    print(ee.data.getAssetRoots())







if __name__ == "__main__":
    test_others()


