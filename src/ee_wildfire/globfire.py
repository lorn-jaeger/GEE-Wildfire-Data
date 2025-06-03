from ee.filter import Filter
from ee.geometry import Geometry
from ee.featurecollection import FeatureCollection
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from tqdm import tqdm
from ee_wildfire.get_globfire import ee_featurecollection_to_gdf

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

def process(config, collection, year, week):
    daily = "Daily" in collection
    if daily:
        collection += "/" + str(year)

    
    start = int(week.timestamp() * 1000)
    end = int((week + pd.Timedelta(weeks=1)).timestamp() * 1000)


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

    # just return an empty dataframe if the data columns are malformed
    # this will just do nothing when concatenated later
    if gdf.empty or ('IDate' not in gdf.columns) or (not daily and 'FDate' not in gdf.columns):
        return gpd.GeoDataFrame(columns=['Id', 'date', 'end_date', 'area', 'lat', 'lon', 'source', 'geometry'], crs="EPSG:4326")
    
    gdf['date'] = pd.to_numeric(pd.to_datetime(gdf['IDate'], unit='ms'))
    gdf['end_date'] = pd.to_numeric(pd.to_datetime(gdf['IDate' if daily else 'FDate'], unit='ms'))
    gdf['source'] = 'daily' if daily else 'final'
    
    return gdf


def get_gdfs(config):
    years = sorted(set(pd.date_range(start=config.start_date, end=config.end_date, freq='D').year))

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
    gdf = get_gdfs(config)

    gdf['Id'] = gdf['Id'].astype(str)
    gdf['area'] = pd.to_numeric(gdf['area'], errors='coerce')
    gdf['IDate'] = pd.to_datetime(gdf['date'], errors='coerce')
    gdf['FDate'] = pd.to_datetime(gdf['end_date'], errors='coerce')
    gdf['lat'] = pd.to_numeric(gdf['lat'], errors='coerce')
    gdf['lon'] = pd.to_numeric(gdf['lon'], errors='coerce')

    gdf = gdf.dropna(subset=['Id', 'date', 'end_date'])

    gdf = gdf.groupby('Id').agg({
        'IDate': 'first',
        'FDate': 'last',
        'area': 'max',
        'lat': 'first',
        'lon': 'first'
    }).reset_index()   

    return gdf

def main():
    pass

if __name__ == '__main__':
    main()



