from ee import ee_exception
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
    """Create an Earth Engine geometry object for the contiguous USA."""
    return Geometry.Polygon([usa_coords])

def compute_area(feature):
    """Compute the area of a feature and set it as a property."""
    return feature.set({'area': feature.area()})

def compute_centroid(feature):
    """Compute the centroid coordinates of a feature and set them as properties."""
    centroid = feature.geometry().centroid().coordinates()
    return feature.set({
        'lon': centroid.get(0),
        'lat': centroid.get(1)
    })

def time_to_milli(time):
    return time.timestamp() * 1000

def ee_featurecollection_to_gdf(fc):
    """Convert Earth Engine FeatureCollection to GeoPandas DataFrame."""
    features = fc.getInfo()['features']
    
    # Extract the geometry and properties from each feature
    geometries = []
    properties = []
    
    for feature in features:
        # Convert GEE geometry to Shapely geometry
        geom = feature['geometry']
        if geom['type'] == 'Polygon':
            geometry = Polygon(geom['coordinates'][0])
        else:
            # Handle other geometry types if needed
            continue
            
        geometries.append(geometry)
        properties.append(feature['properties'])
    

    df = pd.DataFrame(properties)
    # TODO: pull crs into constants file
    gdf = gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")
    
    # Convert area to numeric
    if 'area' in gdf.columns:
        gdf['area'] = pd.to_numeric(gdf['area'])
    
    return gdf

def get_daily_fires(config):
    """
    Get daily fire perimeters from the GlobFire database.
    
    Args:
        year (str): The year to get fires for
        min_size (float): Minimum fire size in square meters
        region (ee.Geometry, optional): Region to filter fires
    """

    year = config.start_date.year
    min_size = config.min_size
    max_size = config.max_size
    region = create_usa_geometry()
    date_range = pd.date_range(start=config.start_date, end=config.end_date, freq='W')
    all_gdfs = []
    collection_name = f'JRC/GWIS/GlobFire/v2/DailyPerimeters/{year}'

    for week in tqdm(date_range, desc=collection_name):
        start_ms = time_to_milli(week)
        end_ms = time_to_milli(week + pd.Timedelta(weeks=1))
    
        try:
            polygons = (FeatureCollection(collection_name)
                       .filterBounds(region))
            
            polygons = polygons.map(compute_area)
            polygons = (polygons
                       .filter(Filter.gte('area', min_size))
                       .filter(Filter.lt('area', max_size))
                       .filter(Filter.gte('IDate', start_ms))
                       .filter(Filter.lt('IDate', end_ms)))

            
            polygons = polygons.map(compute_centroid)
            
            # TODO: its really slow past here...
            gdf = ee_featurecollection_to_gdf(polygons)

            if not gdf.empty:
                gdf['source'] = 'daily'
                # Convert IDate to datetime directly for each row
                gdf['date'] = pd.to_datetime(gdf['IDate'], unit='ms')
                # For daily perimeters, end_date is same as start date
                gdf['end_date'] = gdf['date']

            all_gdfs.append(gdf)
        
        
        except ee_exception.EEException as e:
            print(f"Error accessing daily collection for {year}: {str(e)}")
            return None

    return gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True), crs=all_gdfs[0].crs)

def get_final_fires(config):
    """
    Get final fire perimeters from the GlobFire database.
    
    Args:
        year (str): The year to get fires for
        min_size (float): Minimum fire size in square meters
        region (ee.Geometry, optional): Region to filter fires
    """
    year = config.start_date.year
    min_size = config.min_size
    max_size = config.max_size
    region = create_usa_geometry()
    date_range = pd.date_range(start=config.start_date, end=config.end_date, freq='W')
    collection_name = 'JRC/GWIS/GlobFire/v2/FinalPerimeters'
    all_gdfs = []
    
    
    for week in tqdm(date_range, desc=collection_name):
        start_ms = time_to_milli(week)
        end_ms = time_to_milli(week + pd.Timedelta(weeks=1))

        try:
            polygons = (FeatureCollection(collection_name)
                       .filter(Filter.gt('IDate', start_ms))
                       .filter(Filter.lt('IDate', end_ms))
                       .filterBounds(region))
            
            polygons = polygons.map(compute_area)
            polygons = (polygons
                       .filter(Filter.gt('area', min_size))
                       .filter(Filter.lt('area', max_size)))
            
            polygons = polygons.map(compute_centroid)
            
            gdf = ee_featurecollection_to_gdf(polygons)
            
            if not gdf.empty:
                gdf['source'] = 'final'
                # Convert IDate and FDate to datetime for each row
                gdf['date'] = pd.to_datetime(gdf['IDate'], unit='ms')
                gdf['end_date'] = pd.to_datetime(gdf['FDate'], unit='ms')
            
            all_gdfs.append(gdf)
            
        except ee_exception.EEException as e:
            print(f"Error accessing final perimeters for {year}: {str(e)}")
            return None

    return gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True), crs=all_gdfs[0].crs)

# region default to USA
def get_combined_fires(config):
    """
    Get both daily and final fire perimeters and combine them based on Id.
    
    Args:
        year (str): The year to get fires for
        min_size (float): Minimum fire size in square meters
        region (ee.Geometry, optional): Region to filter fires
    
    Returns:
        combined_gdf (GeoDataFrame)
    """
    daily_gdf = get_daily_fires(config)
    final_gdf = get_final_fires(config)
    
    # Handle missing data
    # FIX: gets currupted right here, bad way to deal with errors
    if daily_gdf is None and final_gdf is None:
        raise Error(f"No fires found to export. Try adjusting time frame and min size.")
    
    # Ensure we have dataframes to work with
    if daily_gdf is None:
        daily_gdf = gpd.GeoDataFrame()
    if final_gdf is None:
        final_gdf = gpd.GeoDataFrame()
    
    # Convert timestamps consistently
    for gdf in [daily_gdf, final_gdf]:
        if not gdf.empty:
            # Convert all timestamp fields to numeric if they aren't already
            for col in ['IDate', 'FDate']:
                if col in gdf.columns:
                    gdf[col] = pd.to_numeric(gdf[col])
            for col in ['FDate']:
                if col in gdf.columns:
                    gdf[col] = gdf['end_date']
    
    # Get unique fire IDs
    all_ids = pd.concat([
        daily_gdf['Id'] if not daily_gdf.empty else pd.Series(dtype=int),
        final_gdf['Id'] if not final_gdf.empty else pd.Series(dtype=int)
    ]).unique()
    
    combined_data = []
    
    for fire_id in all_ids:
        # Get daily perimeters for this fire
        daily_fire = daily_gdf[daily_gdf['Id'] == fire_id] if not daily_gdf.empty else None
        # Get final perimeter for this fire
        final_fire = final_gdf[final_gdf['Id'] == fire_id] if not final_gdf.empty else None
        
        if daily_fire is not None and not daily_fire.empty:
            # Add all daily perimeters
            combined_data.append(daily_fire)
        
        if final_fire is not None and not final_fire.empty:
            # Add final perimeter
            combined_data.append(final_fire)
    
    if not combined_data:
        raise Exception(f"No fires found to export. Try adjusting time frame and min size.")
    
    # Combine all data
    combined_gdf = pd.concat(combined_data, ignore_index=True)
    
    # Sort by Id and date for consistency
    combined_gdf = combined_gdf.sort_values(['Id', 'date'])
    
    return combined_gdf

def analyze_fires(gdf):
    """
    Perform basic analysis on fire perimeters.
    """
    if gdf is None or gdf.empty:
        return {
            "total_fires":0,
            'unique_fires':0,
            'total_area_km2': 0,
            'mean_area_km2': 0,
            'max_area_km2': 0,
            'date_range': "0 to 0",
        }
    
    # Basic statistics
    stats = {
        'total_fires': len(gdf),
        'unique_fires': gdf['Id'].nunique(),
        'total_area_km2': gdf['area'].sum() / 1e6,
        'mean_area_km2': gdf['area'].mean() / 1e6,
        'max_area_km2': gdf['area'].max() / 1e6,
        'date_range': f"{gdf['date'].min()} to {gdf['end_date'].max()}"
    }
    
    # Add source-specific counts
    if 'source' in gdf.columns:
        source_counts = gdf['source'].value_counts()
        for source in source_counts.index:
            stats[f'{source}_fires'] = source_counts[source]
            
        # Add counts of fires with both daily and final perimeters
        fires_with_both = (gdf.groupby('Id')['source']
                          .nunique()
                          .where(lambda x: x > 1)
                          .count())
        stats['fires_with_both_perims'] = fires_with_both
    
    return stats

def main():
    from ee_wildfire.UserConfig.UserConfig import UserConfig
    uf = UserConfig()
    print(uf)

    # daily_fire = get_daily_fires(uf)
    final_fire = get_final_fires(uf)
    # combined_fire = get_combined_fires(uf)

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        # print(combined_fire)
        print(final_fire)



if __name__ == "__main__":
    main()
