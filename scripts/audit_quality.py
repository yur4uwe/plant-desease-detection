import sqlite3
import pandas as pd
import logging
from pathlib import Path
from etl.quality import calculate_quality_score

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s"
)
logger = logging.getLogger(__name__)


def audit_database(db_path: str = "etl/data/processed/observations.db"):
    if not Path(db_path).exists():
        logger.error(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM observations", conn)
        
        # Ensure dates are parsed correctly after SQL load
        df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
        df["extracted_at"] = pd.to_datetime(df["extracted_at"], errors="coerce")

        results = calculate_quality_score(df)

        # Dataset Overview Calculations
        total = len(df)
        diseased = df["is_diseased"].sum()
        healthy = total - diseased
        
        # Original metadata: lat, lon, observation_date
        has_metadata = df[["latitude", "longitude", "observation_date"]].notnull().all(axis=1).sum()
        
        # Enriched metadata: temperature, precipitation, season, solar_status
        enriched_fields = ["temperature", "precipitation", "season", "solar_status"]
        has_enriched = df[enriched_fields].notnull().all(axis=1).sum()

        source_counts = df["source"].value_counts().to_dict()
        
        # Taxonomic Diversity
        unique_labels = df["label"].nunique()
        
        # Provenance breakdown
        prov_counts = df["provenance"].value_counts().to_dict()
        
        # Date range (filter out suspicious epoch starts if any)
        valid_dates = df[df["observation_date"] > "1971-01-01"]["observation_date"].dropna()
        if not valid_dates.empty:
            date_min = valid_dates.min().strftime("%Y-%m-%d")
            date_max = valid_dates.max().strftime("%Y-%m-%d")
            date_range = f"{date_min} to {date_max}"
        else:
            date_range = "N/A"

        # Output results nicely
        print("\n" + "=" * 50)
        print(" DATA QUALITY AUDIT REPORT")
        print("=" * 50)
        
        print(f"DATASET OVERVIEW:")
        print(f"{total} rows")
        print(f"  +-{diseased:5} - diseased")
        print(f"  +-{healthy:5} - healthy")
        print(f"  +-{has_metadata:5} - have metadata (lat, lon, date)")
        print(f"  +-{has_enriched:5} - have enriched metadata (weather, context)")
        print(f"  +-Taxonomic Diversity: {unique_labels} unique labels")
        print(f"  +-Temporal Coverage: {date_range}")
        print(f"  +--provenance:")
        for prov, count in prov_counts.items():
            print(f"     +- {prov:12} = {count}")
        print(f"  +--sources:")
        for src, count in source_counts.items():
            print(f"     +- {src:12} = {count}")
        
        print("-" * 50)
        print(f"INTEGRAL QUALITY SCORE (Q): {results['integral_score']}")
        print("-" * 50)
        print("Component Scores:")
        for k, v in results["metrics"].items():
            print(f"  - {k:25}: {v}")
        print("-" * 50)
        print("Raw Counts:")
        for k, v in results["raw_counts"].items():
            print(f"  - {k:25}: {v}")
        print("=" * 50 + "\n")

    except Exception as e:
        logger.error(f"Audit failed: {e}")


if __name__ == "__main__":
    audit_database()
