from itertools import product
from pathlib import Path

import argparse
import pandas as pd
import tomllib
import torch

from ml_pipeline.data import (
    ImageFeaturizer,
    featurize_dataframe,
    get_train_test_split,
    get_quality_metrics,
    load_data_from_db,
    print_split_composition,
)
from ml_pipeline.evaluate import (
    evaluate_gate,
    save_gradcam_visualizations,
)
from ml_pipeline.train import (
    train_classical_models,
    train_deep_learning,
)
from ml_pipeline.storage import save_evaluation_results

# --- Constants ---
PROJECT_ROOT = Path(".").resolve()
CONFIG_PATH = PROJECT_ROOT / "research/experiment_config.toml"


def run_experiment_suite():
    """Main orchestrator for experiments."""

    parser = argparse.ArgumentParser(description="Run model comparison experiments.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display dataset compositions and exit without training models.",
    )
    args = parser.parse_args()

    with open(CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    featurizer = ImageFeaturizer()
    base_df = load_data_from_db()
    all_results = []

    modes = [
        m
        for m in ["standard", "balanced", "cross_source"]
        if cfg["experiments"].get(f"run_{m}")
    ]

    for mode, size_val in product(modes, cfg["sampling"]["sample_sizes"]):
        size = int(size_val)
        print(f"\n>>> Running Experiment: Mode={mode}, Size={size}")

        split = get_train_test_split(base_df, mode, size, cfg)
        if not split:
            continue
        df, idx_tr, idx_val, idx_te = split
        print_split_composition(df, idx_tr, idx_val, idx_te)

        quality = get_quality_metrics(df)
        print(f"Data Quality Score: {quality['integral_score']}")

        if args.dry_run:
            print(f"Dry run enabled: Skipping training for {mode} (N={size}).")
            continue

        X = featurize_dataframe(df, featurizer)
        y = df["is_diseased"].values

        results = train_classical_models(
            X[idx_tr],
            y[idx_tr],
            X[idx_val],
            y[idx_val],
            X[idx_te],
            y[idx_te],
            mode,
            size,
            cfg,
        )
        dummy_f1 = next((r["F1"] for r in results if r["Model"] == "Dummy"), 0.0)

        if "MobileNetV2" in cfg["models"]["list"]:
            res_dl, model_dl = train_deep_learning(
                df.iloc[idx_tr], df.iloc[idx_te], mode, size, cfg, device
            )
            results.append(res_dl)
            save_gradcam_visualizations(
                model_dl, df.iloc[idx_te], mode, size, cfg, device
            )

        for r in results:
            r.update(
                {
                    "Mode": mode,
                    "SampleSize": size,
                    "Status": evaluate_gate(r, dummy_f1),
                    "DataQuality": quality["integral_score"],
                    "DiseasedRatio": quality["diseased_ratio"],
                }
            )
            all_results.append(r)
            save_evaluation_results(r)

    if all_results:
        report = pd.DataFrame(all_results)
        print("\n### Modular Experiment Results\n", report.to_markdown(index=False))


if __name__ == "__main__":
    run_experiment_suite()
