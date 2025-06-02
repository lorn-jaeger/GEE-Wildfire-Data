"""
geojson_utils.py

this has a bunch of helper functions to handle geojson files
"""
from ee_wildfire.get_globfire import get_combined_fires, analyze_fires
from ee_wildfire.UserConfig.UserConfig import UserConfig

def get_full_geojson_path(config: UserConfig):
    return config.geojson_dir / f"combined_fires_{config.year}.geojson"
    

def generate_geojson(config):
    # Get both daily and final perimeters
    year = config.year
    min_size = config.min_size
    geojson_path = get_full_geojson_path(config)
    
    combined_gdf, daily_gdf, final_gdf = get_combined_fires(
        year, min_size 
    )

    if combined_gdf is not None:
        print(f"\nAnalysis Results for {year}:")

        print("\nCombined Perimeters:")
        combined_stats = analyze_fires(combined_gdf)
        if combined_stats is not None:
            for key, value in combined_stats.items():
                print(f"{key}: {value}")
        else:
            print("No stats available for combined perimeters.")

        if daily_gdf is not None:
            print("\nDaily Perimeters:")
            daily_stats = analyze_fires(daily_gdf)
            if daily_stats is not None:
                for key, value in daily_stats.items():
                    print(f"{key}: {value}")
            else:
                print("No stats available for daily perimeters.")

        if final_gdf is not None:
            print("\nFinal Perimeters:")
            final_stats = analyze_fires(final_gdf)
            if final_stats is not None:
                for key, value in final_stats.items():
                    print(f"{key}: {value}")
            else:
                print("No stats available for final perimeters.")

        # Temporal distribution
        print("\nFires by month:")
        monthly_counts = (
            combined_gdf.groupby([combined_gdf["date"].dt.month, "source"])
            .size()
            .unstack(fill_value=0)
        )
        print(monthly_counts)

    # drop everything that does not have at least 2 Id in combined_gdf
    combined_gdf_reduced = None

    if combined_gdf is not None and "Id" in combined_gdf.columns:
        id_counts = combined_gdf["Id"].value_counts()
        repeated_ids = id_counts[id_counts > 1].index.tolist()
        combined_gdf_reduced = combined_gdf[combined_gdf["Id"].isin(repeated_ids)]
    else:
        raise TypeError("combined_gdf is None or missing 'Id' column")

    # save to geojson
    combined_gdf_reduced.to_file(
        geojson_path,
        driver="GeoJSON",
    )
