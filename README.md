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

## 1. ✅ Create a Service Account

In the [Google Cloud Console](https://console.cloud.google.com/), do the following:

- Go to **IAM & Admin → Service Accounts → Create Service Account**
- Assign the following roles to the **Service Account**:
  - `Owner`
  - `Service Usage Admin`
  - `Service Usage Consumer`
  - `Storage Admin`
  - `Storage Object Creator`

---

## 2. 🔑 Assign Roles to Your Personal Account

Make sure your **main Google Cloud account** (the one you'll log in with) has these roles:

- `Owner`
- `Service Usage Admin`
- `Service Usage Consumer`

---

## 3. 🧭 Create OAuth Credentials (for Google Drive Access)

Still in the Google Cloud Console:

- Go to **APIs & Services → Credentials → + Create Credentials → OAuth Client ID**
- If prompted, **configure the OAuth consent screen**:
  - Choose **Desktop App**
  - Provide a name (e.g., "Drive Access")
- Once created:
  - **Download the JSON** file (this is your OAuth credentials)
  - **Save** the `client_id` and `client_secret` (you’ll use these in your config)

---

## 4. 🚀 Enable Required APIs

In the left-hand menu:

- Go to **APIs & Services → Library**
- Enable the following APIs:
  - `Google Drive API`
  - `Google Earth Engine API`

---

## 5. 👤 Add Test Users (Required for OAuth)

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
This program uses a YAML file for user configuration.

Template for configuration:

```yaml
# NEEDED
# These items are necessary to function.
project_id: YOUR PROJECT ID
credentials: ~/ee_wildfire_data/OAuth/credentials.json

# OPTIONAL
# These items have default values if not provided in YAML file.
data_dir: ~/ee_wildfire_data
start_date: 2021-01-01 00:00:00
end_date: 2021-04-20 00:00:00
tiff_dir: ~/ee_wildfire_data/tiff/2021
drive_dir: EarthEngine_WildfireSpreadTS_2021
download: false
export: false
min_size: 10000000.0
max_size: 1000000000.0

```

To finish configuration you will need to use the `-config` command line argument.

## Command-Line Interface (CLI)
| Argument | Parameters | Description |
| -------- |-- |------------|
| `-config` | `PATH`| Loads a YAML config file located at PATH. This will overload any other command-line arguments.|
| `-show-config`| None | Prints current config to command line. |
| `-export` | None | Export data from Google Earth Engine to Google Drive. |
| `-download`| None | Downloads data from Google Drive to your local machine. |


###  Basic Usage

```bash
ee-wildfire -config /path/to/some/config.yml -show-config
```

```bash
ee-wildfire -export -download
```

# Acknowledgements

This project builds on work from the [WildfireSpreadTSCreateDataset](https://github.com/SebastianGer/WildfireSpreadTSCreateDataset). Credit to original authors for providing data, methods,
and insights.

