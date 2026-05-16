import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(".").resolve()
DB_PATH = PROJECT_ROOT / "data" / "processed" / "observations.db"

def init_evaluation_table(db_path: Path = DB_PATH):
    """Creates the model_evaluation table if it doesn't exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_evaluation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                mode TEXT,
                sample_size INTEGER,
                accuracy REAL,
                f1_score REAL,
                recall REAL,
                precision REAL,
                roc_auc REAL,
                latency REAL,
                train_time REAL,
                data_quality_score REAL,
                diseased_ratio REAL,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def save_evaluation_results(res: dict, db_path: Path = DB_PATH):
    """Inserts evaluation results into the model_evaluation table."""
    init_evaluation_table(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            INSERT INTO model_evaluation (
                model_name, mode, sample_size, accuracy, f1_score, recall, precision, roc_auc, 
                latency, train_time, data_quality_score, diseased_ratio, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            res["Model"],
            res["Mode"],
            res["SampleSize"],
            res.get("Accuracy", 0.0),
            res["F1"],
            res["Recall"],
            res["Precision"],
            res.get("ROC_AUC", 0.0),
            res["Latency"],
            res["TrainTime"],
            res.get("DataQuality", 0.0),
            res.get("DiseasedRatio", 0.0),
            res["Status"]
        ))
    print(f"Results for {res['Model']} saved to {db_path}.")
