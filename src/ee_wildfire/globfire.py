"""
globfire.py

A quick note describing the process for getting fires and some of the choices 
made as well as some helpful information about the globfire dataset. 

The dataset is divided into two parts; Daily Fires and Final Fires. Daily fires
has the geometry, area, and date of each fire for each day it burned. Final 
fires has the final geometry, start date, end date, and final area of each
fire. 

Our goal is to produce a list of fires with their initial latitude and 
longitude as well as their start and end date.

# TODO: Fill this out
"""

from ee.filter import Filter
from ee.geometry import Geometry
from ee.featurecollection import FeatureCollection
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from tqdm import tqdm

usa_coords = [
    [-125.1803892906456, 35.26328285844432],
    [-117.08916345892665, 33.2311514593429],
    [-114.35640058749676, 32.92199940444295],
    [-110.88773544819885, 31.612036247094473],
    [-108.91086200144109, 31.7082477979397],
    [-106.80030780089378, 32.42079476218232],
    [-103.63413436750255, 29.786401496314422],
    [-101.87558377066483, 30.622527701868453],
    [-99.40039768482492, 28.04018292597704],
    [-98.69085295525215, 26.724810345780593],
    [-96.42355704777482, 26.216515704595633],
    [-80.68508661702214, 24.546812350183075],
    [-75.56173032587596, 26.814533788629998],
    [-67.1540159827795, 44.40095539443753],
    [-68.07548734644243, 46.981170472447374],
    [-69.17500995805074, 46.98158998130476],
    [-70.7598785138901, 44.87172183866657],
    [-74.84994741250935, 44.748084983808],
    [-77.62168256782745, 43.005725611950055],
    [-82.45987924104175, 41.41068867019324],
    [-83.38318501671864, 42.09979904377044],
    [-82.5905167831457, 45.06163491639556],
    [-84.83301910769038, 46.83552648258547],
    [-88.26350848510909, 48.143646480291835],
    [-90.06706251069104, 47.553445811024204],
    [-95.03745451438925, 48.9881557770297],
    [-98.45773319567587, 48.94699366043251],
    [-101.7018751401119, 48.98284560308372],
    [-108.43164852530356, 48.81973606668503],
    [-115.07339190755627, 48.93699058308441],
    [-121.82530604190744, 48.9830983403776],
    [-122.22085227110232, 48.63535795404536],
    [-124.59504332589562, 47.695726563030405],
    [-125.1803892906456, 35.26328285844432]
]


def create_usa_geometry():
    return Geometry.Polygon([usa_coords])

def compute_area(feature):
    return feature.set({'area': feature.area()})

def compute_centroid(feature):
    centroid = feature.geometry().centroid().coordinates()
    return feature.set({
        'lon': centroid.get(0),
        'lat': centroid.get(1)
    })

def ee_featurecollection_to_gdf(fc):
    features = fc.getInfo()['features']

    geometries = []
    properties = []
    
    for feature in features:
        geom = feature['geometry']
        if geom['type'] == 'Polygon':
            geometry = Polygon(geom['coordinates'][0])
        else:
            continue
            
        geometries.append(geometry)
        properties.append(feature['properties'])

    df = pd.DataFrame(properties)
    gdf = gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")

    if 'area' in gdf.columns:
        gdf['area'] = pd.to_numeric(gdf['area'])
    
    return gdf

def get_final_fires(config, collection, week):
    start = int(week.timestamp() * 1000)
    end = int((week + pd.Timedelta(weeks=1)).timestamp() * 1000)

    min_size = config.min_size
    region = create_usa_geometry()
   
    fc = (
        FeatureCollection(collection)
        .filterBounds(region)
        .map(compute_area)
        .filter(Filter.gte('area', min_size))
        .filter(Filter.lt('area', 1e20))
        .filter(Filter.gte('IDate', start))
        .filter(Filter.lt('IDate', end))
    )
    
    final = ee_featurecollection_to_gdf(fc)

    if final.empty:
        return final

    final = final.dropna(subset=['Id', 'IDate', 'FDate'])
    final['IDate'] = pd.to_datetime(final['IDate'], unit='ms')
    final['FDate'] = pd.to_datetime(final['FDate'], unit='ms')
    final = final[['Id', 'IDate', 'FDate', 'area']]
    
    years = sorted(set(pd.date_range(
        start=final['IDate'].min(),
        end=final['FDate'].max(),
        freq='D'
    ).year))

    daily = []

    for year in years:
        collection = f"JRC/GWIS/GlobFire/v2/DailyPerimeters/{year}"

        fc = (
            FeatureCollection(collection)
            .filterBounds(region)
            .filter(Filter.inList('Id', final['Id'].tolist()))
            .map(compute_centroid)
        )

        gdf = ee_featurecollection_to_gdf(fc)
        if not gdf.empty:
            daily.append(gdf)

    daily = gpd.GeoDataFrame(pd.concat(daily, ignore_index=True))

    if daily.empty:
        return daily
    
    daily['IDate'] = pd.to_datetime(daily['IDate'], unit='ms')
    daily = daily[['Id', 'IDate', 'lat', 'lon']]

    fires = final.merge(daily, on=['Id'], how='left')
    fires['timedelta'] = (fires['IDate_x'] - fires['IDate_y']).abs()
    fires = fires.sort_values("timedelta").drop_duplicates(subset=['Id'])
    fires = fires[fires['timedelta'] <= pd.Timedelta(hours=24)]
    fires['IDate'] = fires['IDate_x']
    fires = fires[['Id', 'IDate', 'FDate', 'lat', 'lon', 'area']].reset_index(drop=True)
    
    return fires

def get_fires(config):

    collection = 'JRC/GWIS/GlobFire/v2/FinalPerimeters'

    gdfs = []

    dates = pd.date_range(start=config.start_date, end=config.end_date, freq='W')
    for week in tqdm(dates):
        gdf = get_final_fires(config, collection, week)
        if not gdf.empty:
            gdfs.append(gdf)

    return gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))


# def check_query(config):
#     print("Checking globfire query cache...")
#     query = pd.Dataframe([{
#         "start_date" : config.start_date,
#         "end_date" : config.end_date,
#         "min_size" : config.min_size
#     }])
#
#     queries = pd.read_csv("cache/query_cache.csv")
#
#     exists = ((queries == query.iloc[0]).all(axis=1)).any()
#
#     if not exists:
#         queries = pd.concat([queries, query], ignore_index=True)
#         queries.to_csv("path", index=False)
#
#     return exists
#
# def get_cached_gdf(config):
#     print("retrieving cached fire data...")
#     gdf = gpd.read_file("path to file")
#
#     return gdf[
#         (gdf["idate"] >= config.start_date) & 
#         (gdf["fdate"] <= config.end_date) &
#         (gdf["area"] >= config.min_size)
#     ]
#
#
# def cache_gdf(config, gdf):
#     print("Caching fire data...")
#     cache = gpd.read_file("path to file")
#
#     cache = cache.set_index("Id", drop=False)
#     gdf = gdf.set_index("Id", drop=False)
#
#     cache = cache.combine_first(gdf)
#     cache.update(gdf)
#
#     cache = cache.reset_index(drop=True)
#     cache.to_file("this is a path")
#
#
# def get_fires(config):
#     # might have a problem if this fails after writing a query to the query cache
#     refresh_cache = config.force_fires or not check_query(config)
#     if refresh_cache:
#         gdf = get_gdf(config)
#
#         cache_gdf(config, gdf)
#     elif not refresh_cache:
#         gdf = get_cached_gdf(config)
#
#     return gdf
#




    


    
















