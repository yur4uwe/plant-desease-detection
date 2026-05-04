from typing import cast
import pandas as pd
import sqlite3
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import logging

from utils.logging.setup import setup_logging

logging.getLogger(__name__)


def load_data(
    db_path="data/processed/observations.db", syn_path="data/syn_data_gen_tsar.csv"
) -> pd.DataFrame:
    """Loads original data from DB and appends synthetic data."""
    logging.info(f"Loading database from {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        df_db = pd.read_sql("SELECT * FROM observations", conn)
        conn.close()
    except Exception as e:
        logging.warning(f"Could not load DB ({e}). Using only synthetic data.")
        df_db = pd.DataFrame()

    logging.info(f"Loading synthetic data from {syn_path}")
    try:
        df_syn = pd.read_csv(syn_path)
    except Exception as e:
        logging.warning(f"Could not load synthetic data ({e}).")
        df_syn = pd.DataFrame()

    if df_db.empty and df_syn.empty:
        raise ValueError("Both data sources are empty!")

    df_combined = pd.concat([df_db, df_syn], ignore_index=True)
    logging.info(f"Combined dataset shape: {df_combined.shape}")
    return df_combined


def clean_data(df: pd.DataFrame, normalize: bool = True) -> pd.DataFrame:
    """
    Applies the cleaning pipeline: deduplication, imputation, anomaly detection, and normalization.
    """
    df_clean = df.copy()

    # 1. Deduplication
    initial_shape = df_clean.shape[0]
    df_clean = df_clean.drop_duplicates(subset=["source", "external_id"], keep="first")
    df_clean = df_clean.drop_duplicates()  # Complete row match
    logging.info(f"Deduplication removed {initial_shape - df_clean.shape[0]} rows.")

    # 2. Imputation
    num_cols = ["latitude", "longitude", "temperature", "precipitation"]
    cat_cols = ["season", "solar_status"]

    # Impute numericals with median
    num_imputer = SimpleImputer(strategy="median")
    df_clean[num_cols] = num_imputer.fit_transform(df_clean[num_cols])

    # Impute categoricals with 'Unknown'
    df_clean[cat_cols] = df_clean[cat_cols].fillna("Unknown")
    logging.info("Imputed missing values for numerical and categorical features.")

    # 3. Anomaly Detection using Isolation Forest
    # We will fit it only on numerical columns
    logging.info("Running Isolation Forest for anomaly detection...")
    iso_forest = IsolationForest(contamination="0.01", random_state=42)
    # fit_predict returns 1 for inliers and -1 for outliers
    anomaly_labels = iso_forest.fit_predict(df_clean[num_cols])

    # Also add hard rule for coordinates based on reality
    invalid_coords = (
        (df_clean["latitude"] < -90)
        | (df_clean["latitude"] > 90)
        | (df_clean["longitude"] < -180)
        | (df_clean["longitude"] > 180)
    )

    invalid_precip = df_clean["precipitation"] < 0

    # Combine anomaly flags
    outliers = (anomaly_labels == -1) | invalid_coords | invalid_precip

    logging.info(
        f"Isolation Forest & Hard Rules identified {outliers.sum()} anomalies. Removing them."
    )
    df_clean = df_clean[~outliers].reset_index(drop=True)

    # 4. Normalization
    if normalize:
        logging.info("Normalizing numerical features (StandardScaler)...")
        scaler = StandardScaler()
        # We will create normalized columns to keep original data intact for business use if needed
        # Or we can overwrite them as per assignment. We will overwrite.
        df_clean[num_cols] = scaler.fit_transform(df_clean[num_cols])

    logging.info(f"Final cleaned dataset shape: {df_clean.shape}")
    return cast(pd.DataFrame, df_clean)


def main():
    setup_logging("INFO")

    df_combined = load_data()
    df_cleaned = clean_data(df_combined, normalize=True)

    output_path = "../data/df_cleaned_tsar.csv"
    df_cleaned.to_csv(output_path, index=False)
    logging.info(f"Cleaned dataset saved to {output_path}")


if __name__ == "__main__":
    main()
