import sqlite3
import logging
from pathlib import Path
from etl.config.helpers import PROJECT_ROOT

logger = logging.getLogger(__name__)

class WeatherCache:
    def __init__(self, db_path: str = "data/processed/weather_cache.db"):
        self.db_path = PROJECT_ROOT / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weather (
                    latitude REAL,
                    longitude REAL,
                    date TEXT,
                    temperature REAL,
                    precipitation REAL,
                    PRIMARY KEY (latitude, longitude, date)
                )
            """)

    def get(self, lat: float, lon: float, date: str) -> tuple[float | None, float | None] | None:
        # Round coordinates to 2 decimal places to increase cache hits (approx 1.1km precision)
        lat_r, lon_r = round(lat, 2), round(lon, 2)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT temperature, precipitation FROM weather WHERE latitude = ? AND longitude = ? AND date = ?",
                (lat_r, lon_r, date)
            )
            row = cursor.fetchone()
            return row if row else None

    def set_batch(self, data: list[tuple[float, float, str, float | None, float | None]]):
        if not data:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO weather (latitude, longitude, date, temperature, precipitation) VALUES (?, ?, ?, ?, ?)",
                [(round(lat, 2), round(lon, 2), date, temp, precip) for lat, lon, date, temp, precip in data]
            )
            conn.commit()
