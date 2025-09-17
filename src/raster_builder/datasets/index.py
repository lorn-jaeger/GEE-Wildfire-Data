"""Dataset implementations for index sources."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Iterable, Mapping

import ee  # type: ignore
import geopandas as gpd
import pandas as pd

from ..config import ConfigError
from ..context import PipelineContext
from ..io.storage import dataset_output_dir
from .registry import register_dataset

logger = logging.getLogger(__name__)

USA_BOUNDS = [
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
    [-125.1803892906456, 35.26328285844432],
]

FINAL_PERIMETERS = "JRC/GWIS/GlobFire/v2/FinalPerimeters"
DAILY_PERIMETERS_TEMPLATE = "JRC/GWIS/GlobFire/v2/DailyPerimeters/{year}"


def _parse_datetime(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ConfigError(f"Invalid ISO datetime for '{field}': {value}") from exc
    raise ConfigError(f"Unsupported type for '{field}': {type(value).__name__}")


def _usa_geometry() -> ee.Geometry:  # type: ignore[valid-type]
    return ee.Geometry.Polygon([USA_BOUNDS])


def _feature_collection_to_frame(collection: ee.FeatureCollection) -> gpd.GeoDataFrame:  # type: ignore[valid-type]
    info = collection.getInfo()
    features = info.get("features", []) if isinstance(info, dict) else []
    if not features:
        return gpd.GeoDataFrame()
    properties = [feature.get("properties", {}) for feature in features]
    return gpd.GeoDataFrame(properties)


def _final_fires(min_size: float, start_ms: int, end_ms: int) -> gpd.GeoDataFrame:
    region = _usa_geometry()
    collection = (
        ee.FeatureCollection(FINAL_PERIMETERS)
        .filterBounds(region)
        .map(lambda feat: feat.set({"area": feat.area()}))
        .filter(ee.Filter.gte("area", min_size))
        .filter(ee.Filter.lt("area", 1e20))
        .filter(ee.Filter.gte("IDate", start_ms))
        .filter(ee.Filter.lt("IDate", end_ms))
    )
    return _feature_collection_to_frame(collection)


def _daily_centroids(fire_id: Any, start_date: pd.Timestamp, end_date: pd.Timestamp) -> gpd.GeoDataFrame:
    region = _usa_geometry()
    years = sorted(set(pd.date_range(start=start_date, end=end_date, freq="D").year))
    daily_frames: list[gpd.GeoDataFrame] = []
    for year in years:
        collection_id = DAILY_PERIMETERS_TEMPLATE.format(year=year)
        collection = (
            ee.FeatureCollection(collection_id)
            .filterBounds(region)
            .filter(ee.Filter.eq("Id", fire_id))
            .map(lambda feat: feat.set({
                "lon": feat.geometry().centroid().coordinates().get(0),
                "lat": feat.geometry().centroid().coordinates().get(1),
            }))
        )
        frame = _feature_collection_to_frame(collection)
        if not frame.empty:
            daily_frames.append(frame)
    if not daily_frames:
        return gpd.GeoDataFrame(columns=["Id", "IDate", "lat", "lon"])
    return gpd.GeoDataFrame(pd.concat(daily_frames, ignore_index=True))


def _attach_initial_coordinates(fires: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if fires.empty:
        return fires

    lats: list[Any] = []
    lons: list[Any] = []
    for _, row in fires.iterrows():
        daily = _daily_centroids(
            fire_id=row["Id"],
            start_date=row["IDate"],
            end_date=row["FDate"],
        )
        if daily.empty:
            lats.append(pd.NA)
            lons.append(pd.NA)
            continue
        daily["IDate"] = pd.to_datetime(daily["IDate"], unit="ms", errors="coerce")
        daily["timedelta"] = (row["IDate"] - daily["IDate"]).abs()
        daily = daily.sort_values("timedelta")
        if daily["timedelta"].iloc[0] > pd.Timedelta(hours=24):
            lats.append(pd.NA)
            lons.append(pd.NA)
        else:
            lats.append(daily["lat"].iloc[0])
            lons.append(daily["lon"].iloc[0])

    fires = fires.copy()
    fires["lat"] = lats
    fires["lon"] = lons
    fires = fires.dropna(subset=["lat", "lon"])
    return fires


def _format_final_fires(fires: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if fires.empty:
        return gpd.GeoDataFrame(columns=["Id", "IDate", "FDate", "lat", "lon", "area"])
    fires = fires.dropna(subset=["Id", "IDate", "FDate"])
    fires["IDate"] = pd.to_datetime(fires["IDate"], unit="ms", errors="coerce")
    fires["FDate"] = pd.to_datetime(fires["FDate"], unit="ms", errors="coerce")
    fires = fires.dropna(subset=["IDate", "FDate"])
    fires = fires[["Id", "IDate", "FDate", "area"]]
    return fires.reset_index(drop=True)


def _collect_final_fires(start: datetime, end: datetime, min_size: float) -> gpd.GeoDataFrame:
    start_ms = int(pd.Timestamp(start).timestamp() * 1000)
    end_ms = int(pd.Timestamp(end).timestamp() * 1000)
    logger.info(
        "Fetching GlobFire final perimeters between %s and %s (min_size=%s)",
        start.isoformat(),
        end.isoformat(),
        min_size,
    )
    data = _final_fires(min_size=min_size, start_ms=start_ms, end_ms=end_ms)
    logger.info("Retrieved %d final perimeters", len(data))
    return _format_final_fires(data)


def _globfire_index(start: datetime, end: datetime, min_size: float) -> gpd.GeoDataFrame:
    fires = _collect_final_fires(start=start, end=end, min_size=min_size)
    fires = _attach_initial_coordinates(fires)
    logger.info("Final GlobFire index size: %d", len(fires))
    return fires


def _save_index(context: PipelineContext, dataset_name: str, frame: gpd.GeoDataFrame) -> None:
    output_dir = dataset_output_dir(context, stage="index", dataset_name=dataset_name)
    output_path = output_dir / "index.csv"
    df = frame.copy()
    if "geometry" in df:
        geometry = df.geometry
        df = df.drop(columns=["geometry"])
        df["geometry_wkt"] = geometry.to_wkt()
    df.to_csv(output_path, index=False)
    context.set_index(frame, path=output_path)
    logger.info("Stored index CSV at %s", output_path)


@register_dataset(source="index", name="globfire")
def load_globfire_index(context: PipelineContext, options: Mapping[str, Any]) -> gpd.GeoDataFrame:
    """Fetch the GlobFire index dataset and persist it to disk."""

    try:
        start = _parse_datetime(options["start_date"], field="start_date")
        end = _parse_datetime(options["end_date"], field="end_date")
    except KeyError as exc:
        raise ConfigError("GlobFire options require 'start_date' and 'end_date'") from exc

    if end < start:
        raise ConfigError("GlobFire end_date must not precede start_date")

    min_size = float(options.get("min_size", 1e7))
    frame = _globfire_index(start=start, end=end, min_size=min_size)
    _save_index(context, dataset_name="globfire", frame=frame)
    return frame

