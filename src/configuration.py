"""
configuration.py
Kyle Krstulich
May 14, 2025


User edit configs
"""
YEAR = "2020" # current year to look at

MIN_SIZE = 1e7

DATATYPE = "glob" # mtbs or glob style of data input

PROJECT = "ee-earthdata-459817" # Google Earth Engine project id

CREDENTIALS = "/home/kyle/NRML/OAuth/credentials.json" # Path to Google OAuth json file

OUTPUT_DIR = "/home/kyle/NRML/data/tiff/" # local machine output directory for .tiff files

DRIVE_DIR = f"EarthEngine_WildfireSpreadTS_{YEAR}" # the directory on google drive where .tiff files are stored

DATA_DIR = "/home/kyle/NRML/data/perims/" # the directory to store geojson files created by FirePred

FEATURECOLLECTION = "" # VIIRS active fire product path
