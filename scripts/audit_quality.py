import sqlite3
import pandas as pd
import json
import logging
from pathlib import Path
from etl.quality import calculate_quality_score

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

def audit_database(db_path: str = "etl/data/processed/observations.db"):
    if not Path(db_path).exists():
        logger.error(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM observations", conn)
        conn.close()

        logger.info(f"Loaded {len(df)} records from database.")
        
        results = calculate_quality_score(df)
        
        # Output results nicely
        print("\n" + "="*50)
        print(" DATA QUALITY AUDIT REPORT")
        print("="*50)
        print(f"INTEGRAL SCORE (Q): {results['integral_score']}")
        print("-" * 50)
        print("Component Scores:")
        for k, v in results['metrics'].items():
            print(f"  - {k:25}: {v}")
        print("-" * 50)
        print("Raw Counts:")
        for k, v in results['raw_counts'].items():
            print(f"  - {k:25}: {v}")
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"Audit failed: {e}")

if __name__ == "__main__":
    audit_database()
