from ee import ee_exception
from ee.filter import Filter
from ee.geometry import Geometry
from ee.featurecollection import FeatureCollection
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from tqdm import tqdm
from ee_wildfire.get_globfire import ee_featurecollection_to_gdf
from get_globfire import usa_coords, time_to_milli, compute_centroid, compute_area, create_usa_geometry, analyze_fires
from shapely.geometry import shape
from ee_wildfire.utils.yaml_utils import get_full_yaml_path
from ee_wildfire.utils.geojson_utils import get_full_geojson_path

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

def process(config, collection, year, week):
    daily = "Daily" in collection
    if daily:
        collection += year

    start = int(week.timestamp() * 1000)
    end = int(week + pd.timeDelta(weeks=1).timestamp() * 1000)

    min_size = config.min_size
    region = create_usa_geometry()

    geojson = (
        FeatureCollection(collection)
        .filterBounds(region)
        .map(compute_area)
        .filter(Filter.gte('area', min_size))
        .filter(Filter.lt('area', 1e20))
        .filter(Filter.gte('IDate', start))
        .filter(Filter.lt('IDate', end))
        .map(compute_centroid)
    )
    
    gdf = ee_featurecollection_to_gdf(geojson)

    gdf['date'] = pd.to_numerica(pd.to_datetime(gdf['IDate'], unit='ms'))
    gdf['end_date'] = pd.to_numeric(pd.to_datetime(gdf['IDate' if daily else 'FDate'], unit='ms'))
    gdf['source'] = 'daily' if daily else 'final'

    return gdf


def get_gdfs(config):
    years = pd.date_range(start=config.start_date, end=config.end_date, freq='D').year.unique.tolist()

    collections = [
    'JRC/GWIS/GlobFire/v2/FinalPerimeters',
    'JRC/GWIS/GlobFire/v2/DailyPerimeters'
    ]

    gdfs = []

    for collection in collections:
        for year in years:
            start = max(pd.Timestamp(f"{year}-01-01"), config.start_date)
            end = min(pd.Timestamp(f"{year}-12-31"), config.end_date)
            dates = pd.date_range(start=start, end=end, freq='W')
            for week in tqdm(dates, desc=collection):
                gfd = process(config, collection, year, week)
                gdfs.append(gfd)

    return gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs).sort_values(['Id', 'date'])

def get_fires(config):
    pass

    
                

def main():
    pass

if __name__ == '__main__':
    main()


            

            

        
        



    



