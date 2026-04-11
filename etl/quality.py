import logging
import pandas as pd

logger = logging.getLogger(__name__)

def calculate_quality_score(df: pd.DataFrame) -> dict:
    """
    Calculates an integral quality score (Q) for the dataset based on:
    - w1 (0.50): Completeness of critical fields (image_url, is_diseased)
    - w2 (0.20): Uniqueness of external_id
    - w3 (0.20): Completeness of spatiotemporal metadata (lat, lon, date)
    - w4 (0.10): Global class balance (is_diseased ratio)
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for quality assessment.")
        return {"score": 0.0, "details": {}}

    total = len(df)

    # q1: Completeness of critical fields (image_url, is_diseased)
    # Target: 0% missing values
    critical_missing = df[['image_url', 'is_diseased']].isnull().any(axis=1).sum()
    missing_ratio = critical_missing / total
    q1 = 1.0 if missing_ratio == 0 else (0.0 if missing_ratio > 0.01 else 1.0 - missing_ratio)

    # q2: Uniqueness of external_id
    # Target: 0 duplicates
    duplicates = df.duplicated(subset=['external_id']).sum()
    q2 = 1.0 if duplicates == 0 else 0.0

    # q3: Completeness of metadata (latitude, longitude, observation_date)
    # Target: 100% presence
    metadata_fields = ['latitude', 'longitude', 'observation_date']
    complete_metadata = df[metadata_fields].notnull().all(axis=1).sum()
    q3 = complete_metadata / total

    # q4: Global Balance (is_diseased)
    # Target: 0.5 ratio (1.0 score). 0.0/1.0 ratio (0.0 score).
    diseased_count = df['is_diseased'].sum()
    ratio = diseased_count / total
    # Linear scale: 1.0 at 0.5, 0.0 at 0.0 or 1.0
    q4 = 1.0 - 2.0 * abs(0.5 - ratio)

    # Integral Score
    weights = {
        "q1_completeness_critical": 0.50,
        "q2_uniqueness": 0.20,
        "q3_metadata": 0.20,
        "q4_balance": 0.10
    }
    
    score = (
        weights["q1_completeness_critical"] * q1 +
        weights["q2_uniqueness"] * q2 +
        weights["q3_metadata"] * q3 +
        weights["q4_balance"] * q4
    )

    results = {
        "integral_score": round(score, 4),
        "metrics": {
            "q1_completeness_critical": round(q1, 4),
            "q2_uniqueness": round(q2, 4),
            "q3_metadata": round(q3, 4),
            "q4_balance": round(q4, 4)
        },
        "raw_counts": {
            "total_rows": total,
            "missing_critical": int(critical_missing),
            "duplicates": int(duplicates),
            "complete_metadata": int(complete_metadata),
            "diseased_ratio": round(ratio, 4)
        }
    }
    
    logger.info(f"Data Quality Assessment: Q = {results['integral_score']}")
    return results
