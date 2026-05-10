import sqlite3
import os
from etl.utils.weather_cache import WeatherCache

def seed_cache():
    obs_db = "data/processed/observations.db"
    if not os.path.exists(obs_db):
        print("Observations DB not found.")
        return

    print("Seeding weather cache from observations...")
    w_cache = WeatherCache()
    
    with sqlite3.connect(obs_db) as conn:
        cursor = conn.execute("""
            SELECT latitude, longitude, observation_date, temperature, precipitation 
            FROM observations 
            WHERE temperature IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
        """)
        rows = cursor.fetchall()
        
    print(f"Found {len(rows)} records with weather data.")
    w_cache.set_batch(rows)
    print("Seeding complete.")

if __name__ == "__main__":
    seed_cache()
