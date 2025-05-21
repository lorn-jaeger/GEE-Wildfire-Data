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

# Prerequisite

 Requires at least python 3.10.

 As of mid-2023, Google Earth Engine access must be linked to a Google Cloud Project, even for
 free/non-commercial usage. So sign up for a [non-commercial earth engine account](https://earthengine.google.com/noncommercial/).

## 🔐 Google API Setup Instructions

To run this project with Google Earth Engine and Google Drive access, follow the steps below to create and configure your credentials.

---

### 1. ✅ Create a Service Account

In the [Google Cloud Console](https://console.cloud.google.com/), do the following:

- Go to **IAM & Admin → Service Accounts → Create Service Account**
- Assign the following roles to the **Service Account**:
  - `Owner`
  - `Service Usage Admin`
  - `Service Usage Consumer`
  - `Storage Admin`
  - `Storage Object Creator`

---

### 2. 🔑 Assign Roles to Your Personal Account

Make sure your **main Google Cloud account** (the one you'll log in with) has these roles:

- `Owner`
- `Service Usage Admin`
- `Service Usage Consumer`

---

### 3. 🧭 Create OAuth Credentials (for Google Drive Access)

Still in the Google Cloud Console:

- Go to **APIs & Services → Credentials → + Create Credentials → OAuth Client ID**
- If prompted, **configure the OAuth consent screen**:
  - Choose **Desktop App**
  - Provide a name (e.g., "Drive Access")
- Once created:
  - **Download the JSON** file (this is your OAuth credentials)
  - **Save** the `client_id` and `client_secret` (you’ll use these in your config)

---

### 4. 🚀 Enable Required APIs

In the left-hand menu:

- Go to **APIs & Services → Library**
- Enable the following APIs:
  - `Google Drive API`
  - `Google Earth Engine API`

---

### 5. 👤 Add Test Users (Required for OAuth)

- Go to **APIs & Services → OAuth consent screen**
- Scroll to the **Test Users** section
- Click **+ Add Users** and add your personal Google account (the one you'll use for authentication)

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
There are two ways to configure this tool; you can use command line arguments to alter the internal
YAML file, or you can input your own YAML. Here's a template:

```yaml
year: '2020'
min_size: 10000000
project_id: YOUR_PROJECT_ID
geojson_dir: /home/kyle/NRML/data/perims/
output: /home/kyle/NRML/data/tiff/2020/
drive_dir: EarthEngine_WildfireSpreadTS_2020
credentials: /home/kyle/NRML/OAuth/credentials.json
download: false
export: false
show_config: true
force_new_geojson: false
sync_year: true
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
| `--geojson-dir`             | `str`   | Path to the input or output directory for GeoJSON files containing fire perimeter data.   |
| `--download`            | `flag`  | If set, the tool will download TIFF files from Google Drive.               |
| `--export`         | `flag`  | If set, data will be exported to Google Drive using Earth Engine.          |
| `--show-config`         | `flag`  | Print the currently loaded configuration and exit. Useful for debugging.   |
| `--force-new-geojson`   | `flag`  | Force the script to generate a new GeoJSON file even if one exists.        |
| `--sync-year`   | `flag`  | Have all config and output files sync to the year in the config.        |
| `--version`   | `flag`  | Outputs current program version.        |
| `--project-id` | `str` | Your Google project ID|
###  Basic Usage

```bash
ee-wildfire --config ./config_options.yml --year 2020 --geojson data/perims/ --sync-year
```

# Acknowledgements

This project builds on work from the [WildfireSpreadTSCreateDataset](https://github.com/SebastianGer/WildfireSpreadTSCreateDataset). Credit to original authors for providing data, methods,
and insights.

