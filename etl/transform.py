import logging
import pandas as pd
import pandera.pandas as pa
from pandera import DataFrameSchema, Column, Check

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


def enrich_environmental_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    SUPPLEMENTARY ENRICHMENT:
    Derives approximate environmental context from (latitude, longitude, date)
    to support secondary analysis of model performance across conditions:
    - Solar Status (Dawn/Dusk/Daylight)
    - Seasonal Context (Growing/Dormant)
    """
    # NOTE: Implementation planned for Step 3/4 of the development cycle.
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
