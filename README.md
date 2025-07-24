# Project Summary
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

- The [Trello page](https://trello.com/b/eEd18oio/natrual-resource-management-lab) contains the current development status.

# Prerequisite

 Requires at least python 3.10.

 As of mid-2023, Google Earth Engine access must be linked to a Google Cloud Project, even for
 free/non-commercial usage. So sign up for a [non-commercial earth engine account](https://earthengine.google.com/noncommercial/).

# 🔐 Google API Setup Instructions

To run this project with Google Earth Engine and Google Drive access, follow the steps below to create and configure your credentials.

---

## Step 1. Create a Google Cloud Project
- Go the [Google Cloud Console.](https://console.cloud.google.com/)
- Click the project drop-down (top bar) -> **New Project**.
- Name your project (eg., ee-wildfire) and click **Create**.

## Step 2. Enable Required APIs
- [Earth Engine API](https://console.cloud.google.com/flows/enableapi?apiid=earthengine.googleapis.com)
- [Google Drive API](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com)

## Step 3. Create a Service Account
- In the left sidebar: **IAM & Admin** → **Service Accounts**.
- Click **+ Create Service Account**.
- Name it (e.g., `wildfire-access`) and click **Create and Continue**.
- Assign the following roles to the service account:
  - Owner
  - Service Usage Admin
  - Service Usage Consumer
  - Storage Admin
  - Storage Object Creator
- On the list, find your service account → Click **Actions (⋮)** → **Manage keys**.
- Under **Keys**, click **Add Key → Create new key → JSON**.
- Save the downloaded JSON file somewhere safe (e.g., `service_account.json`).

## Step 4. Share Google Drive Folder
If your code needs to read/write to Google Drive:

- Create a folder in [Google Drive](https://drive.google.com/).
- Right-click → **Share**.
- Share it with your **service account email** (e.g., `your-sa@your-project.iam.gserviceaccount.com`).
- Grant **Editor** permission.

---

# Install Instructions

For the stable build:
```bash
pip install ee-wildfire
```

For the experimental build:
```bash
git clone git@github.com:KylesCorner/Earth-Engine-Wildfire-Data.git
cd Earth-Engine-Wildfire-Data
pip install -e .
```

# Configuration
This program uses a YAML file for user configuration.

Template for configuration:

```yaml
# NEEDED

# You need a google cloud service account JSON, if not provided here the program
# will prompt you for one
credentials: ~/ee_wildfire_data/OAuth/credentials.json

# OPTIONAL
# These items have default values if not provided in YAML file.

# Fire query
min_size: 10000000.0

max_size: 1000000000.0

start_date: 2021-01-01 00:00:00

end_date: 2021-04-20 00:00:00

# Directories
tiff_dir: ~/ee_wildfire_data/tiff

data_dir: ~/ee_wildfire_data

log_dir : ~/ee_wildfire_data/logs

google_drive_dir: GoogleEarthEngine

# Pipeline
purge_before: false

download: false

export: false

retry_failed: false

purge_after: false

# Logs
no_log: false

log_level: info # levels: debug, info, warn, error

# Misc
silent: false
```

To finish configuration you will need to use the `-config` command line argument.


## Command-Line Interface (CLI)

You can also edit configuration on the fly with command line arguments:

| Argument | Parameters | Description |
| -------- |------------|-------------|
| `--version` | None | Show current version. |
| `--config` | `PATH` | Path to YAML config file. Overrides all other command-line arguments. |
| `--export` | None | Export data from Google Earth Engine to Google Drive. |
| `--download` | None | Download data from Google Drive to your local machine. |
| `--show-config` | None | Show user configuration. |
| `--credentials` | `PATH` | Path to Google authentication `.json` service account file. |
| `--data-dir` | `PATH` | Path to output data directory on your local machine. |
| `--tiff-dir` | `PATH` | Path where downloaded `.tif` files are stored. |
| `--google-drive-dir` | `str` | Name of your Google Drive folder for exporting. |
| `--min-size` | `float` | Minimum size of fire area to detect (in hectares). |
| `--max-size` | `float` | Maximum size of fire area to detect (in hectares). |
| `--retry-failed` | None | Retry failed Earth Engine locations. |
| `--purge-before` | None | Purge files from Google Drive before exporting new data. |
| `--purge-after` | None | Purge files from Google Drive after downloading. |
| `--start-date` | `datetime` | Starting date for Earth Engine query (e.g., `2020-01-01`). |
| `--end-date` | `datetime` | Ending date for Earth Engine query (e.g., `2020-12-31`). |
| `--silent` | None | No command line output. |
| `--reset_config` | None | Resets internal YAML file to default values. |
| `--no-log` | None | Disable logging. |
| `--log-dir` | `PATH` | Directory where you want your logs files stored.|
| `--log-level` | `'debug', 'info', 'warn', or 'error'` | Sets the level of verbosity for log files.|
###  Basic Usage

```bash
ee-wildfire --config /path/to/some/config.yml
```

```bash
ee-wildfire --credentials PATH_TO_CREDS --export --download --min-size 10 --log-level warn
```

# Acknowledgements

This project builds on work from the [WildfireSpreadTSCreateDataset](https://github.com/SebastianGer/WildfireSpreadTSCreateDataset). Credit to original authors for providing data, methods,
and insights.

