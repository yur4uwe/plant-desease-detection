"""
Unified Cross-Validation script for both Classical and CNN models.
Usage:
    python scripts/run_cv.py MobileNetV2 RandomForest
    python scripts/run_cv.py all
"""
import argparse
import json
import time
import tomllib
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from xgboost import XGBClassifier

from etl.config.helpers import PROJECT_ROOT
from ml_pipeline.data import (
    ImageFeaturizer,
    featurize_dataframe,
    load_data_from_db,
    sample_by_composition,
)
from ml_pipeline.train import train_deep_learning

def run_classical_cv(models_to_run: list[str], df: pd.DataFrame, cfg: dict):
    """Runs 5-fold CV for classical models (RandomForest, XGBoost)."""
    print(f"\n--- Starting Classical CV (5-Folds) for: {models_to_run} ---")
    
    featurizer = ImageFeaturizer()
    X = featurize_dataframe(df, featurizer)
    y = df["is_diseased"].values
    
    available_models = {
        "RandomForest": RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=50, max_depth=5, eval_metric="logloss", random_state=42)
    }
    
    scoring = ['accuracy', 'f1', 'recall', 'precision', 'roc_auc']
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    all_results = {}
    
    for name in models_to_run:
        if name not in available_models:
            print(f"Skipping unknown classical model: {name}")
            continue
            
        print(f"\nExecuting CV for {name}...")
        cv_results = cross_validate(available_models[name], X, y, cv=cv, scoring=scoring, n_jobs=-1)
        
        metrics = {s: cv_results[f'test_{s}'] for s in scoring}
        all_results[name] = metrics
        
        print(f"{'Metric':<15} | {'Mean':<10} | {'Std Dev':<10}")
        print("-" * 40)
        for s in scoring:
            print(f"{s:<15} | {np.mean(metrics[s]):<10.4f} | {np.std(metrics[s]):<10.4f}")

    # Visualization - Accuracy
    plt.figure(figsize=(8, 6))
    acc_data = [all_results[m]["accuracy"] for m in all_results]
    plt.boxplot(acc_data, tick_labels=list(all_results.keys()))
    plt.title('5-Fold CV Accuracy: Classical Models')
    plt.ylabel('Accuracy')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    out_path = PROJECT_ROOT / "docs" / "images" / "cv_boxplot.png"
    plt.savefig(out_path)
    print(f"Classical CV plot saved to {out_path}")
    
    return all_results

def run_cnn_cv(df: pd.DataFrame, cfg: dict):
    """Runs 3-fold CV for the CNN champion (MobileNetV2)."""
    print("\n--- Starting CNN CV (3-Folds) for: MobileNetV2 ---")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    cv_scores = []
    
    fold = 1
    for train_idx, test_idx in skf.split(df, df["is_diseased"]):
        print(f"\nProcessing CNN Fold {fold}/3...")
        df_tr, df_te = df.iloc[train_idx], df.iloc[test_idx]
        
        # Train and evaluate using the pipeline function
        scores, _ = train_deep_learning(df_tr, df_te, f"cv_cnn_fold_{fold}", str(len(df)), cfg, device)
        cv_scores.append(scores)
        fold += 1

    metrics_to_report = ["Accuracy", "F1", "Recall", "Precision", "ROC_AUC"]
    results_agg = {m: [s[m] for s in cv_scores] for m in metrics_to_report}
    
    print("\n" + "="*45)
    print("CNN CROSS-VALIDATION SUMMARY (3-FOLD)")
    print(f"{'Metric':<15} | {'Mean':<10} | {'Std Dev':<10}")
    print("-" * 45)
    for m in metrics_to_report:
        mean_val = np.mean(results_agg[m])
        std_val = np.std(results_agg[m])
        print(f"{m:<15} | {mean_val:<10.4f} | {std_val:<10.4f}")
    print("="*45)

    # Visualization - Accuracy
    plt.figure(figsize=(6, 6))
    plt.boxplot([results_agg["Accuracy"]], tick_labels=['Accuracy'])
    plt.title('3-Fold CV Accuracy: MobileNetV2')
    plt.ylabel('Score')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    out_path = PROJECT_ROOT / "docs" / "images" / "cv_cnn_boxplot.png"
    plt.savefig(out_path)
    print(f"CNN CV plot saved to {out_path}")
    
    return results_agg

def main():
    parser = argparse.ArgumentParser(description="Unified CV runner.")
    parser.add_argument("models", nargs="+", help="Model names (RandomForest, XGBoost, MobileNetV2) or 'all'")
    parser.add_argument("--size", type=int, default=600, help="Subset size for CV")
    args = parser.parse_args()

    # Determine which models to run
    all_supported = ["RandomForest", "XGBoost", "MobileNetV2"]
    targets = all_supported if "all" in args.models else args.models
    
    classical_targets = [m for m in targets if m in ["RandomForest", "XGBoost"]]
    cnn_target = "MobileNetV2" in targets

    # Load shared config and data
    with open(PROJECT_ROOT / "research" / "experiment_config.toml", "rb") as f:
        cfg = tomllib.load(f)
    
    base_df = load_data_from_db()
    df = sample_by_composition(base_df, args.size, "standard", cfg)
    print(f"Dataset subset size for CV: {len(df)}")

    combined_results = {}

    if classical_targets:
        combined_results["classical"] = run_classical_cv(classical_targets, df, cfg)
    
    if cnn_target:
        combined_results["cnn"] = run_cnn_cv(df, cfg)

    # Final cleanup/save results
    if combined_results:
        res_path = PROJECT_ROOT / "logs" / "combined_cv_results.json"
        res_path.parent.mkdir(parents=True, exist_ok=True)
        # Handle numpy serialization
        def default_conv(o):
            if isinstance(o, np.ndarray): return o.tolist()
            if isinstance(o, np.float32): return float(o)
            return o
        with open(res_path, "w") as f:
            json.dump(combined_results, f, indent=4, default=default_conv)
        print(f"\nAll results saved to {res_path}")

if __name__ == "__main__":
    main()
