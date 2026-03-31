import json
import logging
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera import DataFrameSchema, Column, Check

from etl.sources.interface import RawObservation

logger = logging.getLogger(__name__)

# ─── Схема валідації ──────────────────────────────────────────────

observation_schema = DataFrameSchema(
    {
        "source": Column(str, Check.isin(["inaturalist", "kaggle"])),  # pyright: ignore[reportUnknownMemberType]
        "external_id": Column(str, Check.str_length(min_value=1)),  # pyright: ignore[reportUnknownMemberType]
        "image_url": Column(str, nullable=True),
        "label": Column(str, nullable=True),
        "is_diseased": Column(pd.BooleanDtype(), nullable=True),
        "latitude": Column(float, nullable=True, checks=Check.in_range(-90, 90)),  # pyright: ignore[reportUnknownMemberType]
        "longitude": Column(float, nullable=True, checks=Check.in_range(-180, 180)),  # pyright: ignore[reportUnknownMemberType]
        "observation_date": Column(pa.DateTime, nullable=True),  # pyright: ignore[reportUnknownMemberType]
        "extracted_at": Column(pa.DateTime, nullable=False),  # pyright: ignore[reportUnknownMemberType]
    }
)

# ─── Завантаження сирих даних ─────────────────────────────────────


def load_raw(cache_files: list[Path]) -> pd.DataFrame:
    records: list[RawObservation] = []
    for cache_file in cache_files:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            records.extend([RawObservation.from_dict(obs) for obs in data])
    logger.info(f"Loaded {len(records)} raw records from {len(cache_files)} files")
    return pd.DataFrame(records)


# ─── Трансформації ────────────────────────────────────────────────


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["source", "external_id"])
    dropped = before - len(df)
    if dropped:
        logger.info(f"Dropped {dropped} duplicate observations")
    return df


def drop_missing_labels(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df[df["is_diseased"].notna()]
    dropped = before - len(df)
    if dropped:
        logger.info(f"Dropped {dropped} observations with missing is_diseased label")
    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip().str.lower()
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    return df


def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["is_diseased"] = df["is_diseased"].astype("boolean")
    return df


def drop_invalid_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    mask = (
        df["latitude"].isna()
        | df["longitude"].isna()
        | df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)
    )
    df = df[mask]
    dropped = before - len(df)
    if dropped:
        logger.info(f"Dropped {dropped} observations with invalid coordinates")
    return df


# ─── Оркестрація ──────────────────────────────────────────────────


def run_transform(raw_files: list[Path]) -> pd.DataFrame:
    logger.info(f"Loading raw data from {raw_files}")
    df = load_raw(raw_files)
    logger.info(f"Loaded {len(df)} raw observations")

    df = normalize_columns(df)
    df = drop_duplicates(df)
    df = parse_dates(df)
    df = cast_types(df)
    df = drop_invalid_coordinates(df)
    df = drop_missing_labels(df)

    logger.info(f"Validating schema on {len(df)} observations")
    _ = observation_schema.validate(df)
    logger.info(f"Transform complete — {len(df)} clean observations ready")

    return df
