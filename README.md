# Todo List

- catch timeout

- quality README

- central install file

- strip notebooks into python files

- tie to Jesse's google drive, might be weird because its a shared folder. Multiple writing.

- containerize and publish

## Project Summary
Earth-Engine-Wildfire-Data is a Python command-line utility and library for extracting and
transforming wildfire-related geospatial data from Google Earth Engine. It supports:

- Access to MODIS, VIIRS, GRIDMET, and other remote sensing datasets.

- Filtering wildfire perimeters by date, size, and region.

- Combining daily and final fire perimeters.

- Generating YAML config files for use in simulation or prediction tools.

- Command-line configurability with persistent YAML-based settings.

- This tool is intended for researchers, data scientists, or modelers working with wildfire data
pipelines, particularly those interested in integrating Earth Engine datasets into geospatial ML
workflows.

## Prerequisite

 Requires at least python 3.10.

 As of mid-2023, Google Earth Engine access must be linked to a Google Cloud Project, even for
 free/non-commercial usage. So sign up for a [non-commercial earth engine account](https://earthengine.google.com/noncommercial/).
 .


## Google API Instructions 

 Make a service account and add these rolls:
 - Owner
 - Service Usage Admin
 - Service Usage Consumer
 - Storage Admin
 - Storage Object Creator

 In main account add these rolls:
 - Owner
 - Service Usage Admin
 - Service Usage Consumer

 We then created an oath account for google drive access.
We need to create an OAuth account for Google Drive access. In the top right hamburger menu select:

 - APIs & Services/Credentials/+Create credentials/OAuth client ID
	- OAuth client ID
		- first configure OAuth screen. Select Desktop App and give it a name.
		- keep track of the Client ID and Client secret, we will need those later.
		- click download JSON from this screen, these are your credentials.

Now we need to enable the apis. In the top right hamburger menu select:

- APIs & Services
From this menu select `Google Drive API` and click `Enable API`. Do the same for `Google Earth Engine API`

 Now we need to add ourselves as a test user
 in google cloud navigate to API's & Servies/OAut concent screen/Audience
	- Scroll down and under Test users click + Add users. Select your main account.


## Install Instructions
For the experimental build
```bash
git clone git@github.com:KylesCorner/Earth-Engine-Wildfire-Data.git
cd Earth-Engine-Wildfire-Data
pip instll -e .
```

## Command-Line Interface (CLI)

This tool can be run from the command line to generate fire configuration YAML files from GeoJSON
data. Configuration can be passed directly via flags or through a YAML file using `--config`.

| Argument                | Type    | Description                                                                 |
|-------------------------|---------|-----------------------------------------------------------------------------|
| `--config`              | `str`   | Path to a YAML configuration file. Defaults to `./config_options.yml`.     |
| `--year`                | `str`   | The year of the fire events to process.                                    |
| `--min-size`            | `float` | Minimum fire size (in square meters) to include.                           |
| `--output`              | `str`   | Local directory to store generated TIFF files.                             |
| `--drive-dir`           | `str`   | Google Drive directory where TIFFs are uploaded or downloaded from.        |
| `--credentials`         | `str`   | Path to the Google OAuth2 credentials JSON file. Required for GEE export.  |
| `--project-id`          | `str`   | Google Cloud project ID associated with your Earth Engine access.          |
| `--geojson`             | `str`   | Path to the input or output GeoJSON file containing fire perimeter data.   |
| `--download`            | `flag`  | If set, the tool will download TIFF files from Google Drive.               |
| `--export-data`         | `flag`  | If set, data will be exported to Google Drive using Earth Engine.          |
| `--show-config`         | `flag`  | Print the currently loaded configuration and exit. Useful for debugging.   |
| `--force-new-geojson`   | `flag`  | Force the script to generate a new GeoJSON file even if one exists.        |
| `--sync-year`   | `flag`  | Have all config and output files sync to the year in the config.        |

###  Basic Usage

```bash
ee-wildfire --config ./config_options.yml --year 2020 --geojson data/perims/combined_fires_2020.geojson
```

# Acknowledgements

This project builds on work from the [WildfireSpreadTSCreateDataset](https://github.com/SebastianGer/WildfireSpreadTSCreateDataset). Credit to original authors for providing data, methods,
and insights.

