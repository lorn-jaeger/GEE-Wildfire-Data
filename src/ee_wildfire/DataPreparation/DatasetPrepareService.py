import datetime
import sys
import time

from pathlib import Path

from ee import batch
from ee import data
from ee import Geometry, ImageCollection # type: ignore

from ee_wildfire.UserConfig.UserConfig import UserConfig
from ee_wildfire.constants import EXPORT_QUEUE_SIZE
from ee_wildfire.UserInterface import ConsoleUI


# Add the parent directory to the Python path to enable imports
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from DataPreparation.satellites.FirePred import FirePred

class DatasetPrepareService:
    """
    Service class to handle downloading and preparing geospatial datasets
    for a specified location and time period using Google Earth Engine (GEE).

    Attributes:
        config (dict): Configuration dictionary with geospatial and temporal parameters.
        user_config (UserConfig): User-specific configuration object.
        location (str): Location key to extract coordinates and time range from the config.
        rectangular_size (float): Half-width/height of the square area to extract, in degrees.
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        start_time (str): Start date for data extraction.
        end_time (str): End date for data extraction.
        total_tasks (int): Counter for total GEE export tasks submitted.
        geometry (Geometry.Rectangle): Rectangular geometry used for data extraction.
        scale_dict (dict): Mapping of dataset names to their spatial resolution in meters.
    """
    def __init__(self, location: str, config: dict, user_config: UserConfig) -> None:
        """
        Initializes the DatasetPrepareService with geospatial parameters and user configuration.

        Args:
            location (str): Key used to reference a location's config entry.
            config (dict): Dictionary containing configuration for multiple locations.
            user_config (UserConfig): Object containing user-specific settings.
        """
        self.config = config
        self.user_config = user_config
        self.location = location
        self.rectangular_size = self.config.get('rectangular_size')
        self.latitude = self.config.get(self.location).get('latitude')
        self.longitude = self.config.get(self.location).get('longitude') 
        self.start_time = self.config.get(location).get('start')
        self.end_time = self.config.get(location).get('end')
        self.total_tasks = 0

        # Set the area to extract as an image
        self.rectangular_size = self.config.get('rectangular_size')
        self.geometry = Geometry.Rectangle(
            [self.longitude - self.rectangular_size, self.latitude - self.rectangular_size,
             self.longitude + self.rectangular_size, self.latitude + self.rectangular_size])

        self.scale_dict = {"FirePred": 375}
        ConsoleUI.debug(self)

    def __repr__(self) -> str:
        output_str = "DatasetPrepareService.py\n"
        for key, value in self.__dict__.items():
            if key != "user_config":
                output_str += f"{key} {value}\n"
        return(output_str)

    def _batch_export(self,image, base_filename, utm_zone):
        ConsoleUI.debug(f"Exporting {image} as {base_filename} in zone {utm_zone}")
        task = batch.Export.image.toDrive(
            image=image,
            description=base_filename,
            folder=self.user_config.google_drive_dir,
            region=self.geometry.toGeoJSON()['coordinates'],
            scale=self.scale_dict.get("FirePred"),
            crs=f'EPSG:{utm_zone}',
            maxPixels=self.user_config.max_size,
        )
        task.start()

        
    # NOTE: look at this funciton for querrying google earth export queue
    def prepare_daily_image(self, date_of_interest:str, time_stamp_start:str="00:00", time_stamp_end:str="23:59") -> ImageCollection:
        """
        Prepare a daily image from Google Earth Engine (GEE) for a specified date and time range.

        Args:
            date_of_interest (str): Date in 'YYYY-MM-DD' format.
            time_stamp_start (str, optional): Start time in 'HH:MM' format. Defaults to "00:00".
            time_stamp_end (str, optional): End time in 'HH:MM' format. Defaults to "23:59".

        Returns:
            ImageCollection: GEE image collection for the given date and time range.
        """
        self.total_tasks += 1
        if self.total_tasks > 2500:
            active_tasks = str(batch.Task.list()).count('READY')
            while active_tasks > 2000:
                time.sleep(60)
                active_tasks = str(batch.Task.list()).count('READY')
        satellite_client = FirePred()
        img_collection = satellite_client.compute_daily_features(date_of_interest + 'T' + time_stamp_start,
                                                               date_of_interest + 'T' + time_stamp_end,
                                                               self.geometry)
        return img_collection

    def download_image_to_drive(self, image_collection: ImageCollection, index:str, utm_zone:str) -> None:
        """
        Export a single image from the given image collection to Google Drive.

        Args:
            image_collection (ImageCollection): Earth Engine image collection to export.
            index (str): Identifier (typically date) for naming the exported file.
            utm_zone (str): EPSG code for UTM projection to use for export.
        """

        base_filename = f"Image_Export_{self.location}_{index}"
        img = image_collection.max().toFloat()

        # Use geemap's export function
        try:
            # self._gee_export(img, base_filename, utm_zone)
            self._batch_export(img,base_filename,utm_zone)

            # add item to export queue
            self.user_config.exported_files.append(f"{base_filename}.tif")

        except Exception as e:
            ConsoleUI.warn(f"Export failed for {base_filename}: {str(e)}")

            # FIX: Are these getting handled at all?
            self.user_config.failed_exports.append(f"{base_filename}.tif")
            wait_for_gee_queue_space()

        
    def extract_dataset_from_gee_to_drive(self, utm_zone:str, n_buffer_days:int=0) -> None:
        """
        Extracts daily image datasets from GEE and exports them to Google Drive
        over the configured date range and optional buffer.

        Args:
            utm_zone (str): EPSG code for UTM projection to use for image export.
            n_buffer_days (int, optional): Number of days to buffer before and after the time period. Defaults to 0.
        """
        buffer_days = datetime.timedelta(days=n_buffer_days)
        time_dif = self.end_time - self.start_time + 2 * buffer_days + datetime.timedelta(days=1)
        desc = f"Days for {self.location}"
        ConsoleUI.add_bar(key="export",total=time_dif.days,desc=desc )

        for i in range(time_dif.days):
            date_of_interest = str(self.start_time - buffer_days + datetime.timedelta(days=i))
            ConsoleUI.print(f"Processing date: {date_of_interest}")

            try:
                img_collection = self.prepare_daily_image(date_of_interest=date_of_interest)
                # wait to avoid rate limiting
                # time.sleep(1)

                n_images = len(img_collection.getInfo().get("features"))
                if n_images > 1:

                    ConsoleUI.error(f"Found {n_images} features in img_collection returned by prepare_daily_image. "
                                     f"Should have been exactly 1.")

                    raise RuntimeError(f"Found {n_images} features in img_collection returned by prepare_daily_image. "
                                     f"Should have been exactly 1.")

                max_img = img_collection.max()

                if len(max_img.getInfo().get('bands')) != 0:
                    self.download_image_to_drive(img_collection, date_of_interest, utm_zone)
            except Exception as e:
                ConsoleUI.error(f"Failed processing {date_of_interest}: {str(e)}")
                raise

            ConsoleUI.update_bar(key="export")

def wait_for_gee_queue_space():
    ConsoleUI.add_bar("export_queue",total=EXPORT_QUEUE_SIZE, desc="Google Earth export queue", color="yellow")
    total = EXPORT_QUEUE_SIZE
    target = EXPORT_QUEUE_SIZE/2

    while True:
        tasks = data.getTaskList()
        active_tasks = [t for t in tasks if t['state'] in ['READY', 'RUNNING']]

        if len(active_tasks) > total:
            total = len(active_tasks)

        # update progress bar
        ConsoleUI.change_bar_total(key="export_queue",total=total)
        ConsoleUI.set_bar_position(key="export_queue",value=len(active_tasks))
        ConsoleUI.print(f"Waiting until export queue size = {target}. {len(active_tasks)-target} remaining")

        if len(active_tasks) <= target:
            ConsoleUI.change_bar_desc(key="export_queue", desc="Google Earth export queue")
            break
        else:
            ConsoleUI.change_bar_desc(key="export_queue", desc="Google Earth export queue full, waiting...")

        time.sleep(60)


def main():
    from ee_wildfire.UserConfig.UserConfig import UserConfig
    uf = UserConfig()
    wait_for_gee_queue_space()

if __name__ == "__main__":
    main()

