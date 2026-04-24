import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from etl.config.helpers import ETL_ROOT
from etl.config.types import AppConfig

logger = logging.getLogger(__name__)

# ─── Table Schema ───────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS observations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source            TEXT    NOT NULL,
    external_id       TEXT    NOT NULL,
    image_url         TEXT,
    label             TEXT,
    is_diseased       INTEGER,
    latitude          REAL,
    longitude         REAL,
    observation_date  TEXT,
    extracted_at      TEXT    NOT NULL,
    loaded_at         TEXT    NOT NULL,
    season            TEXT,
    solar_status      TEXT,
    temperature       REAL,
    precipitation     REAL,
    provenance        TEXT,
    UNIQUE (source, external_id)
)
"""

# ─── Connections ────────────────────────────────────────────────


def get_connection(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    _ = conn.execute("PRAGMA journal_mode=WAL")
    _ = conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─── Database Initialization ─────────────────────────────────────


def init_db(conn: sqlite3.Connection) -> None:
    _ = conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    logger.info("Database schema initialized")


# ─── Loading ─────────────────────────────────────────────────────


def load_observations(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    if df.empty:
        logger.warning("DataFrame is empty — nothing to load")
        return 0

    loaded_at = datetime.now(timezone.utc).isoformat()
    df = df.copy()

    # Prep columns for SQLite
    df["loaded_at"] = loaded_at
    df["is_diseased"] = df["is_diseased"].astype(int)

    # Convert datetime objects to ISO strings for SQLite storage
    df["observation_date"] = (
        df["observation_date"]
        .dt.strftime("%Y-%m-%d")
        .where(df["observation_date"].notna(), None)
    )
    df["extracted_at"] = df["extracted_at"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Drop raw_json before loading to DB (optional, but keep DB clean)
    cols_to_load = [
        "source",
        "external_id",
        "image_url",
        "label",
        "is_diseased",
        "latitude",
        "longitude",
        "observation_date",
        "extracted_at",
        "loaded_at",
        "season",
        "solar_status",
        "temperature",
        "precipitation",
        "provenance",
    ]

    # Use INSERT OR IGNORE via temporary table for bulk performance
    df[cols_to_load].to_sql("temp_observations", conn, if_exists="replace", index=False)

    cursor = conn.cursor()
    _ = cursor.execute(f"""
        INSERT OR IGNORE INTO observations ({", ".join(cols_to_load)})
        SELECT {", ".join(cols_to_load)} FROM temp_observations
    """)
    inserted = cursor.rowcount
    _ = cursor.execute("DROP TABLE temp_observations")
    conn.commit()

    logger.info(f"Loaded {inserted} new observations")
    return inserted


# ─── Verification ────────────────────────────────────────────────


def verify_load(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    _ = cursor.execute("SELECT COUNT(*) FROM observations")
    count = cursor.fetchone()[0]
    logger.info(f"Total observations in database: {count}")
    return count


# ─── Orchestration ───────────────────────────────────────────────


def run_load(df: pd.DataFrame, config: AppConfig) -> None:
    db_path = ETL_ROOT / config.load.target_path
    logger.info(f"Loading {len(df)} observations into {db_path}")

    conn = get_connection(db_path.as_posix())
    try:
        init_db(conn)
        _ = load_observations(conn, df)
        _ = verify_load(conn)
    finally:
        conn.close()
        logger.info("Database connection closed")
