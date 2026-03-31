import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from etl.config.helpers import ETL_ROOT
from etl.config.types import AppConfig

logger = logging.getLogger(__name__)

# ─── Схема таблиці ────────────────────────────────────────────────

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
    UNIQUE (source, external_id)
)
"""

# ─── Підключення ──────────────────────────────────────────────────


def get_connection(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─── Ініціалізація схеми ──────────────────────────────────────────


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    logger.info("Database schema initialized")


# ─── Завантаження ─────────────────────────────────────────────────


def load_observations(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    loaded_at = datetime.now(timezone.utc).isoformat()
    df = df.copy()
    df["loaded_at"] = loaded_at
    df["observation_date"] = (
        df["observation_date"]
        .astype(str)
        .where(df["observation_date"].notna(), other=None)
    )
    df["extracted_at"] = (
        df["extracted_at"].astype(str).where(df["extracted_at"].notna(), other=None)
    )
    df["is_diseased"] = df["is_diseased"].map(lambda x: int(x) if pd.notna(x) else None)

    records = df[
        [
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
        ]
    ].to_dict(orient="records")

    cursor = conn.cursor()
    inserted = 0
    skipped = 0

    for record in records:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO observations (
                    source, external_id, image_url, label,
                    is_diseased, latitude, longitude,
                    observation_date, extracted_at, loaded_at
                ) VALUES (
                    :source, :external_id, :image_url, :label,
                    :is_diseased, :latitude, :longitude,
                    :observation_date, :extracted_at, :loaded_at
                )
            """,
                record,
            )
            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1
        except sqlite3.Error as e:
            logger.error(f"Failed to insert {record['external_id']}: {e}")

    conn.commit()
    logger.info(f"Loaded {inserted} new observations, skipped {skipped} duplicates")
    return inserted


# ─── Верифікація ──────────────────────────────────────────────────


def verify_load(conn: sqlite3.Connection, expected: int) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM observations")
    row = cursor.fetchone()
    total: int = row[0] if row else 0
    logger.info(f"Database contains {total} total observations")
    if total < expected:
        logger.warning(f"Expected at least {expected} observations but found {total}")


# ─── Оркестрація ──────────────────────────────────────────────────


def run_load(df: pd.DataFrame, config: AppConfig) -> None:
    db_path = ETL_ROOT / config["load"]["target_path"]
    logger.info(f"Loading {len(df)} observations into {db_path}")

    conn = get_connection(db_path.as_posix())
    try:
        init_db(conn)
        inserted = load_observations(conn, df)
        verify_load(conn, inserted)
    finally:
        conn.close()
        logger.info("Database connection closed")
