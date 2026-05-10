import logging
from typing import cast
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import DataFrameSchema, Column, Check
from datetime import datetime, timezone
from astral import Observer
from astral.sun import sun
from etl.sources.weather import get_weather_bulk

from etl.sources.interface import RawObservation

logger = logging.getLogger(__name__)

# ─── Schema Validation ──────────────────────────────────────────

observation_schema = DataFrameSchema(
    {
        "source": Column(str),
        "external_id": Column(str, Check.str_length(min_value=1)),
        "image_url": Column(str, nullable=True),
        "label": Column(str, nullable=True),
        "is_diseased": Column(pd.BooleanDtype(), nullable=False),
        "latitude": Column(float, nullable=True, checks=Check.in_range(-90, 90)),
        "longitude": Column(float, nullable=True, checks=Check.in_range(-180, 180)),
        "observation_date": Column(pa.DateTime, nullable=True),
        "extracted_at": Column(pa.DateTime, nullable=False),
        "season": Column(str, nullable=True),
        "solar_status": Column(str, nullable=True),
        "temperature": Column(float, nullable=True),
        "precipitation": Column(float, nullable=True),
        "provenance": Column(str, nullable=True),
    }
)

# ─── Transformations ────────────────────────────────────────────


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["source", "external_id"])
    dropped = before - len(df)
    if dropped:
        logger.info(f"Dropped {dropped} duplicate observations")
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    df["observation_date"] = (
        pd.to_datetime(df["observation_date"], errors="coerce")
        .dt.tz_localize(None)
    )
    df["extracted_at"] = (
        pd.to_datetime(df["extracted_at"], errors="coerce")
        .dt.tz_localize(None)
    )
    return df


def _get_season(lat: float, month: int) -> str | None:
    if pd.isna(lat) or pd.isna(month):
        return None
    if lat > 0:  # Northern Hemisphere
        if month in [3, 4, 5]:
            return "Spring"
        if month in [6, 7, 8]:
            return "Summer"
        if month in [9, 10, 11]:
            return "Autumn"
        return "Winter"
    else:  # Southern Hemisphere
        if month in [3, 4, 5]:
            return "Autumn"
        if month in [6, 7, 8]:
            return "Winter"
        if month in [9, 10, 11]:
            return "Spring"
        return "Summer"


def _get_solar_status(lat: float, lon: float, dt: datetime) -> str | None:
    if pd.isna(lat) or pd.isna(lon) or pd.isna(dt):
        return None
    try:
        obs = Observer(latitude=lat, longitude=lon)
        # Assume dt is UTC. If naive, localize to UTC for astral to work reliably.
        if dt.tzinfo is None:
            dt_utc = dt.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt.astimezone(timezone.utc)

        s = sun(obs, date=dt_utc.date())

        if dt_utc < s["dawn"] or dt_utc > s["dusk"]:
            return "Night"
        elif s["dawn"] <= dt_utc < s["sunrise"] or s["sunset"] < dt_utc <= s["dusk"]:
            return "Dusk/Dawn"
        else:
            return "Daylight"
    except ValueError:
        # Sun remains above/below horizon (polar day/night)
        # A simple fallback: checking month and hemisphere
        if lat > 66.5 and dt.month in [5, 6, 7, 8]:
            return "Daylight"
        if lat > 66.5 and dt.month in [11, 12, 1, 2]:
            return "Night"
        if lat < -66.5 and dt.month in [11, 12, 1, 2]:
            return "Daylight"
        if lat < -66.5 and dt.month in [5, 6, 7, 8]:
            return "Night"
        return "Polar"
    except Exception as e:
        logger.warning(
            f"Astral calculation failed for lat={lat} lon={lon} dt={dt}: {e}"
        )
        return None


def enrich_environmental_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives approximate environmental context (season, solar status, weather) efficiently.
    """
    logger.info("Enriching environmental metadata (Season, Solar Status, Weather)")

    # Ensure columns exist even if no weather is fetched
    if "temperature" not in df.columns:
        df["temperature"] = None
    if "precipitation" not in df.columns:
        df["precipitation"] = None

    # 1. Vectorized Season & Solar Status
    # Using apply for complex logic, but it's still better than row-by-row manual list building
    df["season"] = df.apply(
        lambda row: (
            _get_season(row["latitude"], row["observation_date"].month)
            if pd.notna(row["latitude"]) and pd.notna(row["observation_date"])
            else None
        ),
        axis=1,
    )
    df["solar_status"] = df.apply(
        lambda row: (
            _get_solar_status(
                row["latitude"], row["longitude"], row["observation_date"]
            )
            if pd.notna(row["latitude"])
            and pd.notna(row["longitude"])
            and pd.notna(row["observation_date"])
            else None
        ),
        axis=1,
    )

    # 2. Optimized Bulk Weather Fetching
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    weather_needed_mask = (
        df["latitude"].notna()
        & df["longitude"].notna()
        & df["observation_date"].notna()
        & (df["observation_date"].dt.strftime("%Y-%m-%d") < today_str)
    )
    weather_needed = cast(pd.DataFrame, df[weather_needed_mask].copy())

    if not weather_needed.empty:
        weather_needed["date_str"] = weather_needed["observation_date"].dt.strftime(
            "%Y-%m-%d"
        )

        # Identify unique location-date pairs to minimize API calls
        unique_locs_df = weather_needed[
            ["latitude", "longitude", "date_str"]
        ].drop_duplicates()
        unique_loc_list = [tuple(x) for x in unique_locs_df.values]

        from etl.utils.weather_cache import WeatherCache
        w_cache = WeatherCache()
        
        # 1. Check local cache first
        final_weather_map = {}
        to_fetch = []
        
        for lat, lon, date_str in unique_loc_list:
            cached = w_cache.get(lat, lon, date_str)
            if cached:
                final_weather_map[(lat, lon, date_str)] = cached
            else:
                to_fetch.append((lat, lon, date_str))

        if to_fetch:
            logger.info(
                f"Fetching weather for {len(to_fetch)} unique location-date pairs ({len(unique_loc_list) - len(to_fetch)} from cache)"
            )
            # Call the bulk fetcher
            weather_results = get_weather_bulk(to_fetch)  # type: ignore

            # Save to cache
            cache_entries = []
            for (lat, lon, date), res in zip(to_fetch, weather_results):
                final_weather_map[(lat, lon, date)] = res
                cache_entries.append((lat, lon, date, res[0], res[1]))
            
            w_cache.set_batch(cache_entries)
        else:
            logger.info(f"All {len(unique_loc_list)} weather records retrieved from cache")

        def _map_weather(row):
            key = (
                row["latitude"],
                row["longitude"],
                row["observation_date"].strftime("%Y-%m-%d"),
            )
            return final_weather_map.get(key, (None, None))

        results = weather_needed.apply(_map_weather, axis=1)
        df.loc[weather_needed_mask, "temperature"] = [r[0] for r in results]
        df.loc[weather_needed_mask, "precipitation"] = [r[1] for r in results]

        enriched_count = df["temperature"].notna().sum()
        logger.info(
            f"Weather enrichment complete: {enriched_count} rows updated with environmental context"
        )

    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    df["precipitation"] = pd.to_numeric(df["precipitation"], errors="coerce")
    return df


def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["is_diseased"] = df["is_diseased"].astype("boolean")

    # Explicitly cast categorical columns to string type
    # This prevents Pandera SchemaErrors when columns contain all None/NaN
    for col in ["source", "external_id", "image_url", "label", "season", "solar_status", "provenance"]:
        if col in df.columns:
            df[col] = df[col].astype("string")

    return df


def drop_invalid_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    # Keep if both are null OR both are within valid ranges
    mask = (df["latitude"].isna() & df["longitude"].isna()) | (
        df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)
    )

    before = len(df)
    mask_df = df[mask].copy()
    if isinstance(mask_df, pd.DataFrame):
        df = mask_df
    else:
        logger.warning("Invalid coordinates found but no data to drop")
    dropped = before - len(df)
    if dropped:
        logger.info(f"Dropped {dropped} observations with invalid coordinates")
    return df


# ─── Orchestration ──────────────────────────────────────────────


def run_transform(observations: list[RawObservation]) -> pd.DataFrame:
    if not observations:
        logger.warning("No observations to transform")
        return pd.DataFrame()

    logger.info(f"Transforming {len(observations)} observations")

    # Convert dataclasses to list of dicts for DataFrame creation
    df = pd.DataFrame([obs.to_dict() for obs in observations])

    df = drop_duplicates(df)
    df = parse_dates(df)
    df = enrich_environmental_metadata(df)
    df = cast_types(df)
    df = drop_invalid_coordinates(df)

    # Final Schema Validation
    logger.info("Validating transformed data schema")
    df = observation_schema.validate(df)

    logger.info(f"Transform complete — {len(df)} clean observations ready")
    return df
