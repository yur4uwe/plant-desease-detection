import argparse
import sqlite3
from typing import cast
import pandas as pd
import requests
from pathlib import Path
from tqdm import tqdm
import time

# --- Configuration ---
DB_PATH = Path("data/processed/observations.db")
SAVE_DIR = Path("data/raw/inaturalist/images")
LIMIT = 1000  # Number of healthy iNaturalist images to fetch for research


def fetch_images(mode: str, limit: int):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    # Get healthy iNaturalist observations that don't have local images
    match mode:
        case "healthy":
            clause = "AND is_diseased = 0"
        case "diseased":
            clause = "AND is_diseased = 1"
        case "all":
            clause = ""
        case _:
            raise ValueError(f"Invalid mode: {mode}")

    query = f"""
    SELECT external_id, image_url 
    FROM observations 
    WHERE source = 'inaturalist' {clause} 
    LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=[limit])
    conn.close()

    print(f"Attempting to download {len(df)} images from iNaturalist...")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "PlantDiseaseETL/1.0 (University Research; contact: YURII.TSAR@lnu.edu.ua)"
        }
    )

    success_count = 0
    for _, row in tqdm(df.iterrows(), total=len(df)):
        ext_id = cast(str, row["external_id"])
        url = cast(str, row["image_url"])

        if not url:
            continue

        # iNaturalist URLs often look like .../square.jpg.
        # We might want 'medium.jpg' for better features.
        url = url.replace("square", "medium")

        target_path = SAVE_DIR / f"{ext_id}.jpg"

        if target_path.exists():
            success_count += 1
            continue

        try:
            resp = session.get(url, timeout=10)
            if resp.status_code == 200:
                with open(target_path, "wb") as f:
                    f.write(resp.content)
                success_count += 1
                # Politeness delay
                time.sleep(0.1)
            else:
                print(f"Failed {url}: {resp.status_code}")
        except Exception as e:
            print(f"Error {url}: {e}")

    print(f"Successfully downloaded {success_count} images.")


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument(
        "--limit", type=int, default=1000, help="Number of images to fetch"
    )
    args.add_argument(
        "--mode", type=str, default="all", help="What type of images to fetch"
    )
    args = args.parse_args()
    fetch_images(mode=args.mode, limit=args.limit)
