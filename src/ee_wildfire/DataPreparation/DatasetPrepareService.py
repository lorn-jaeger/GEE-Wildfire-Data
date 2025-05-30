import datetime
import ee
from ee import Geometry, ImageCollection # type: ignore
import geemap
from tqdm import tqdm
import sys
from pathlib import Path
import time
from ee_wildfire.constants import DEFAULT_GOOGLE_DRIVE_DIR
from ee_wildfire.UserConfig.UserConfig import UserConfig

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
            active_tasks = str(ee.batch.Task.list()).count('READY')
            while active_tasks > 2000:
                time.sleep(60)
                active_tasks = str(ee.batch.Task.list()).count('READY')
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

        folder = DEFAULT_GOOGLE_DRIVE_DIR
        filename = f"{self.location}/{index}"
        base_filename = f"Image_Export_{self.location}_{index}"

        img = image_collection.max().toFloat()
        
        # Use geemap's export function
        try:
            geemap.ee_export_image_to_drive(
                image=img,
                description=base_filename,
                folder=folder,
                region=self.geometry.toGeoJSON()['coordinates'],
                scale=self.scale_dict.get("FirePred"),
                crs=f'EPSG:{utm_zone}',
                maxPixels=1e13
            )
            # tqdm.write(f"Successfully queed export for {filename}")
            self.user_config.exported_files.append(f"{base_filename}.tif")

        except Exception as e:
            tqdm.write(f"Export failed for {filename}: {str(e)}")
            raise
        
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
        day_bar = tqdm(range(time_dif.days), desc=f"Days for {self.location}", leave=False)

        for i in day_bar:
            date_of_interest = str(self.start_time - buffer_days + datetime.timedelta(days=i))
            # tqdm.write(f"Processing date: {date_of_interest}")

            try:
                img_collection = self.prepare_daily_image(date_of_interest=date_of_interest)
                # wait to avoid rate limiting
                time.sleep(1)

                n_images = len(img_collection.getInfo().get("features"))
                if n_images > 1:
                    raise RuntimeError(f"Found {n_images} features in img_collection returned by prepare_daily_image. "
                                     f"Should have been exactly 1.")
                max_img = img_collection.max()
                if len(max_img.getInfo().get('bands')) != 0:
                    self.download_image_to_drive(img_collection, date_of_interest, utm_zone)
            except Exception as e:
                tqdm.write(f"Failed pocessing {date_of_interest}: {str(e)}")
                raise

