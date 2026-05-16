import tomllib
import time
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

from ml_pipeline.data import (
    get_train_test_split,
    load_data_from_db,
    print_split_composition,
    get_quality_metrics
)
from ml_pipeline.evaluate import (
    evaluate_gate,
)
from ml_pipeline.train import train_deep_learning
from ml_pipeline.storage import save_evaluation_results

# --- Constants ---
PROJECT_ROOT = Path(".").resolve()
CONFIG_PATH = PROJECT_ROOT / "research/experiment_config.toml"

def run_champion_pipeline():
    """Trains and evaluates the Champion Model (MobileNetV2)."""
    print("Starting Champion Model Pipeline...")
    
    with open(CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)
    
    # Champion Model Selection
    champion_model = "MobileNetV2"
    cfg["models"]["list"] = [champion_model, "Dummy"]
    
    # Setup parameters
    mode = "standard"
    sample_size = 2500
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    base_df = load_data_from_db()
    
    print(f"\n>>> Running Champion Pipeline: Model={champion_model}, Mode={mode}, Size={sample_size}")
    split = get_train_test_split(base_df, mode, sample_size, cfg)
    if not split:
        print("Failed to get data split.")
        return
    
    df, idx_tr, idx_val, idx_te = split
    print_split_composition(df, idx_tr, idx_val, idx_te)
    
    # Step 13.5: Automated Quality Check
    quality = get_quality_metrics(df)
    print(f"Data Quality Score: {quality['integral_score']}")

    # Training
    # Note: Using optimized train_deep_learning which includes scheduler and weighted loss
    res, model = train_deep_learning(
        df.iloc[idx_tr],
        df.iloc[idx_te],
        mode,
        sample_size,
        cfg,
        device
    )
    
    # Baseline comparison for gate
    # For champion pipeline, we skip full baseline training to save time, 
    # but we should ideally have a reference. 
    # Here we just check against a reasonable F1 floor or re-run Dummy.
    dummy_f1 = 0.86 # From research results for standard mode
    
    res.update({
        "Mode": mode,
        "SampleSize": sample_size,
        "Status": evaluate_gate(res, dummy_f1),
        "DataQuality": quality["integral_score"],
        "DiseasedRatio": quality["diseased_ratio"]
    })
    
    save_evaluation_results(res)
    
    print("\n### Champion Model Final Results ###")
    for k, v in res.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    run_champion_pipeline()
