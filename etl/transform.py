import logging
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import DataFrameSchema, Column, Check
from datetime import datetime, timezone
from astral import Observer
from astral.sun import sun
from etl.sources.weather import get_weather_for_location

from etl.sources.interface import RawObservation

logger = logging.getLogger(__name__)

# ─── Schema Validation ──────────────────────────────────────────

observation_schema = DataFrameSchema(
    {
        "source": Column(str, Check.isin(["inaturalist", "kaggle"])),
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
    df["observation_date"] = pd.to_datetime(
        df["observation_date"], errors="coerce"
    ).dt.tz_localize(None)
    df["extracted_at"] = pd.to_datetime(
        df["extracted_at"], errors="coerce"
    ).dt.tz_localize(None)
    return df


def _get_season(lat: float, month: int) -> str | None:
    if pd.isna(lat) or pd.isna(month):
        return None
    if lat > 0:  # Northern Hemisphere
        if month in [3, 4, 5]: return "Spring"
        if month in [6, 7, 8]: return "Summer"
        if month in [9, 10, 11]: return "Autumn"
        return "Winter"
    else:  # Southern Hemisphere
        if month in [3, 4, 5]: return "Autumn"
        if month in [6, 7, 8]: return "Winter"
        if month in [9, 10, 11]: return "Spring"
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
        if lat > 66.5 and dt.month in [5, 6, 7, 8]: return "Daylight"
        if lat > 66.5 and dt.month in [11, 12, 1, 2]: return "Night"
        if lat < -66.5 and dt.month in [11, 12, 1, 2]: return "Daylight"
        if lat < -66.5 and dt.month in [5, 6, 7, 8]: return "Night"
        return "Polar"
    except Exception as e:
        logger.warning(f"Astral calculation failed for lat={lat} lon={lon} dt={dt}: {e}")
        return None

def enrich_environmental_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives approximate environmental context (season, solar status, weather).
    """
    logger.info("Enriching environmental metadata (Season, Solar Status, Weather)")
    
    # Use lists to build columns faster than df.at iterrows
    seasons = []
    solar_statuses = []
    temperatures = []
    precipitations = []
    
    for _, row in df.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]
        obs_date = row["observation_date"]
        
        season = None
        solar = None
        temp = None
        precip = None

        if pd.notna(lat) and pd.notna(lon) and pd.notna(obs_date):
            season = _get_season(lat, obs_date.month)
            solar = _get_solar_status(lat, lon, obs_date)
            date_str = obs_date.strftime("%Y-%m-%d")
            temp, precip = get_weather_for_location(lat, lon, date_str)
            
        seasons.append(season)
        solar_statuses.append(solar)
        temperatures.append(temp)
        precipitations.append(precip)

    df["season"] = seasons
    df["solar_status"] = solar_statuses
    df["temperature"] = temperatures
    df["precipitation"] = precipitations

    return df


def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["is_diseased"] = df["is_diseased"].astype("boolean")
    return df


def drop_invalid_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    # Keep if both are null OR both are within valid ranges
    mask = (df["latitude"].isna() & df["longitude"].isna()) | (
        df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)
    )

    before = len(df)
    df = df[mask]
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
