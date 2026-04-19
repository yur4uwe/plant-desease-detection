import logging
import sqlite3
import pandas as pd
import time
import math
from tqdm import tqdm

from etl.config.helpers import ETL_ROOT
from etl.transform import _get_season, _get_solar_status
from etl.sources.weather import get_weather_for_location, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = ETL_ROOT / "data" / "processed" / "observations.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Alter Table
    new_columns = {
        "season": "TEXT",
        "solar_status": "TEXT",
        "temperature": "REAL",
        "precipitation": "REAL",
    }

    cursor.execute("PRAGMA table_info(observations)")
    existing_cols = [row[1] for row in cursor.fetchall()]

    for col, col_type in new_columns.items():
        if col not in existing_cols:
            logger.info(f"Adding column {col} {col_type}")
            cursor.execute(f"ALTER TABLE observations ADD COLUMN {col} {col_type}")

    conn.commit()

    # 2. Fetch rows that need enrichment
    df = pd.read_sql(
        """
        SELECT id, latitude, longitude, observation_date 
        FROM observations 
        WHERE (temperature IS NULL OR season IS NULL) 
        AND latitude IS NOT NULL
        """,
        conn,
    )

    if df.empty:
        logger.info("No records need migration.")
        return

    logger.info(f"Migrating {len(df)} records...")

    df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")

    updates = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Enriching Metadata"):
        rid = row["id"]

        lat_val = row["latitude"]
        lon_val = row["longitude"]
        obs_date = row["observation_date"]

        season = None
        solar = None
        temp = None
        precip = None

        if (
            isinstance(lat_val, (int, float))
            and not math.isnan(float(lat_val))
            and isinstance(lon_val, (int, float))
            and not math.isnan(float(lon_val))
            and isinstance(obs_date, pd.Timestamp)
        ):
            lat = float(lat_val)
            lon = float(lon_val)

            season = _get_season(lat, obs_date.month)
            solar = _get_solar_status(lat, lon, obs_date.to_pydatetime())
            date_str = obs_date.strftime("%Y-%m-%d")

            try:
                # API Call
                temp, precip = get_weather_for_location(lat, lon, date_str)
                # Polite delay between requests
                time.sleep(0.1)
            except RateLimitError as e:
                logger.error(f"Migration interrupted by rate limit: {e}")
                break

        updates.append((season, solar, temp, precip, rid))

    # 3. Batch Update
    if updates:
        logger.info(f"Writing {len(updates)} updates to database...")
        cursor.executemany(
            "UPDATE observations SET season = ?, solar_status = ?, temperature = ?, precipitation = ? WHERE id = ?",
            updates,
        )
        conn.commit()

    logger.info("Migration loop finished.")
    conn.close()


if __name__ == "__main__":
    migrate()

