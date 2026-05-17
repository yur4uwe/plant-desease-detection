import sqlite3
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from PIL import Image, ImageFilter, ImageOps
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import Dataset
from tqdm import tqdm

from etl.quality import calculate_quality_score
from ml_pipeline.utils import resolve_image_path

# --- Constants ---
PROJECT_ROOT = Path(".").resolve()
DB_PATH = PROJECT_ROOT / "data" / "processed" / "observations.db"

class ImageFeaturizer:
    """Extracts classical CV features from images."""

    def __init__(self, target_size=(128, 128)):
        self.target_size = target_size

    def extract_features(self, image_path: Path) -> np.ndarray | None:
        if not image_path.exists():
            return None
        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB").resize(self.target_size)
                arr = np.array(img)
                hists = [
                    np.histogram(arr[:, :, i], bins=8, range=(0, 255))[0]
                    for i in range(3)
                ]
                hsv_means = np.mean(np.array(img.convert("HSV")), axis=(0, 1))
                gray = ImageOps.grayscale(img)
                edge_arr = np.array(gray.filter(ImageFilter.FIND_EDGES))
                return np.concatenate(
                    [*hists, hsv_means, [np.mean(edge_arr), np.std(edge_arr)]]
                )
        except Exception:
            return None

class PlantDataset(Dataset):
    """PyTorch Dataset for plant images."""

    def __init__(self, df: pd.DataFrame, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            image = Image.open(row["local_path"]).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224))
        if self.transform:
            image = self.transform(image)
        return image, torch.tensor(row["is_diseased"], dtype=torch.float32)

def load_data_from_db(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Loads and resolves paths for all observations."""
    print(f"Loading data from {db_path}...")
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT external_id, image_url, is_diseased, source FROM observations", conn
        )

    df["local_path"] = df.apply(resolve_image_path, axis=1)
    return cast(pd.DataFrame, df[df["local_path"].notnull()].copy())

def _sample_standard(
    base_df: pd.DataFrame, weights: dict, total_size: int, seed: int
) -> list[pd.DataFrame]:
    """Helper for stratified sampling according to natural distribution."""
    sampled = []
    for source, weight in weights.items():
        n_target = int(total_size * weight)
        source_df = base_df[base_df["source"] == source]
        n = min(len(source_df), n_target)
        if n > 0:
            sampled.append(source_df.sample(n=n, random_state=seed))
            print(f"Sampling {source}: {n} (Standard)")
    return sampled

def _sample_balanced_quota(
    df: pd.DataFrame,
    weights: dict,
    total_size: int,
    seed: int,
    allow_oversampling: bool = False,
) -> list[pd.DataFrame]:
    """Dynamically balances classes across sources based on global targets."""
    sampled = []
    target_per_class = total_size // 2
    rem_h, rem_d = target_per_class, target_per_class

    # 1. Resolve Single-Class Constraints
    quotas = {}
    for src, weight in weights.items():
        quota = int(total_size * weight)
        src_df = df[df["source"] == src]
        h_pool = src_df[src_df["is_diseased"] == 0]
        d_pool = src_df[src_df["is_diseased"] == 1]

        if len(h_pool) == 0:
            n = min(len(d_pool), quota)
            quotas[src] = {"n": n, "cls": 1, "single": True}
            rem_d -= n
        elif len(d_pool) == 0:
            n = min(len(h_pool), quota)
            quotas[src] = {"n": n, "cls": 0, "single": True}
            rem_h -= n
        else:
            quotas[src] = {"quota": quota, "single": False}

    # 2. Distribute Remaining Needs to Multi-Class Sources
    multi_sources = [s for s, q in quotas.items() if not q["single"]]
    total_multi_w = sum(weights[s] for s in multi_sources)

    for src in multi_sources:
        rel_w = weights[src] / total_multi_w if total_multi_w > 0 else 0
        t_h, t_d = int(rem_h * rel_w), int(rem_d * rel_w)

        src_df = df[df["source"] == src]
        h_p, d_p = (
            src_df[src_df["is_diseased"] == 0],
            src_df[src_df["is_diseased"] == 1],
        )

        n_h = t_h if allow_oversampling else min(len(h_p), t_h)
        n_d = t_d if allow_oversampling else min(len(d_p), t_d)

        if n_h > 0:
            sampled.append(
                h_p.sample(
                    n=n_h,
                    replace=allow_oversampling and len(h_p) < n_h,
                    random_state=seed,
                )
            )
        if n_d > 0:
            sampled.append(
                d_p.sample(
                    n=n_d,
                    replace=allow_oversampling and len(d_p) < n_d,
                    random_state=seed,
                )
            )
        print(f"Sampling {src}: H={n_h}, D={n_d}")

    # 3. Collect Single-Class Samples
    for src, q in quotas.items():
        if q["single"]:
            s_df = df[(df["source"] == src) & (df["is_diseased"] == q["cls"])]
            if q["n"] > 0:
                sampled.append(s_df.sample(n=q["n"], random_state=seed))
            print(f"Sampling {src}: {'Diseased' if q['cls'] else 'Healthy'}={q['n']}")

    return sampled

def _sample_cross_source(
    base_df: pd.DataFrame,
    weights: dict,
    total_size: int,
    test_pct: float,
    seed: int,
) -> list[pd.DataFrame]:
    """Helper for cross-source sampling with potential iNaturalist leak."""
    tr_size = int(total_size * (1 - test_pct))
    te_size = int(total_size * test_pct)
    
    leak_w = weights.get("inaturalist_leak", 0.0)
    field_weights = {k: v for k, v in weights.items() if k != "inaturalist_leak"}
    
    field_df = base_df[base_df["source"].isin(field_weights.keys())]
    inat_df = base_df[base_df["source"] == "inaturalist"]

    if field_df.empty or inat_df.empty:
        return []

    te_sampled = inat_df.sample(n=min(len(inat_df), te_size), random_state=seed)
    remaining_inat = inat_df.drop(te_sampled.index)
    leak_n = int(tr_size * leak_w)
    
    leak_sampled = []
    if leak_n > 0:
        h_pool = remaining_inat[remaining_inat["is_diseased"] == 0]
        d_pool = remaining_inat[remaining_inat["is_diseased"] == 1]
        n_per = leak_n // 2
        if not h_pool.empty and not d_pool.empty:
            leak_sampled.append(h_pool.sample(n=min(len(h_pool), n_per), random_state=seed))
            leak_sampled.append(d_pool.sample(n=min(len(d_pool), n_per), random_state=seed))
            print(f"Leak: Sampled {len(leak_sampled[0]) + len(leak_sampled[1])} iNaturalist images into training.")

    field_tr_size = tr_size - (leak_n if leak_n > 0 else 0)
    tr_field_sampled = _sample_balanced_quota(
        field_df, field_weights, field_tr_size, seed, allow_oversampling=True
    )

    return [*tr_field_sampled, *leak_sampled, te_sampled]

def sample_by_composition(
    base_df: pd.DataFrame, total_size: int, mode: str, cfg: dict
) -> pd.DataFrame:
    """Samples data dynamically based on mode configuration."""
    seed = cfg["sampling"]["random_state"]
    weights = cfg["modes"].get(mode, {})
    test_pct = cfg["sampling"]["test_size"]

    if mode == "standard":
        sampled = _sample_standard(base_df, weights, total_size, seed)
    elif mode == "balanced":
        sampled = _sample_balanced_quota(base_df, weights, total_size, seed)
    elif mode == "cross_source":
        sampled = _sample_cross_source(base_df, weights, total_size, test_pct, seed)
    else:
        return pd.DataFrame()

    if mode == "cross_source":
        return pd.concat(sampled)
    
    return (
        pd.concat(sampled).sample(frac=1, random_state=seed)
        if sampled
        else pd.DataFrame(columns=base_df.columns)
    )

def featurize_dataframe(df: pd.DataFrame, featurizer: ImageFeaturizer) -> np.ndarray:
    """Extracts features for all images in a dataframe."""
    return np.array(
        [
            f if (f := featurizer.extract_features(p)) is not None else np.zeros(29)
            for p in tqdm(df["local_path"], desc="Featurizing")
        ]
    )


def get_quality_metrics(df: pd.DataFrame) -> dict:
    """Calculates and returns a summary of quality metrics for the dataframe."""
    results = calculate_quality_score(df)
    if not results:
        return {"integral_score": 0.0, "diseased_ratio": 0.0}
    return {
        "integral_score": results["integral_score"],
        "diseased_ratio": results["raw_counts"]["diseased_ratio"],
    }


def get_train_test_split(
    base_df: pd.DataFrame, mode: str, size: int, cfg: dict
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray] | None:
    """Splits the data into training, val, and testing sets based on the mode."""
    seed = cfg["sampling"]["random_state"]
    test_pct = cfg["sampling"]["test_size"]
    val_pct = cfg["sampling"].get("val_size", 0.15)

    df = sample_by_composition(base_df, size, mode, cfg)
    if df.empty:
        return None

    if mode == "cross_source":
        te_size = int(size * test_pct)
        tr_full_size = len(df) - te_size
        df_tr_full = df.iloc[:tr_full_size]
        df_te = df.iloc[tr_full_size:]

        val_rel = val_pct / (1.0 - test_pct)
        idx_tr, idx_val = train_test_split(
            np.arange(len(df_tr_full)),
            test_size=min(0.9, val_rel),
            random_state=seed,
            stratify=df_tr_full["is_diseased"],
        )
        final_df = df.reset_index(drop=True)
        idx_te = np.arange(tr_full_size, len(final_df))
        return final_df, np.array(idx_tr), np.array(idx_val), np.array(idx_te)

    idx_tr, idx_temp = train_test_split(
        np.arange(len(df)),
        test_size=(test_pct + val_pct),
        random_state=seed,
        stratify=df["is_diseased"],
    )
    y_temp = df.iloc[idx_temp]["is_diseased"]
    idx_val, idx_te = train_test_split(
        idx_temp,
        test_size=test_pct / (test_pct + val_pct),
        random_state=seed,
        stratify=y_temp,
    )
    return (
        df.reset_index(drop=True),
        np.array(idx_tr),
        np.array(idx_val),
        np.array(idx_te),
    )

def print_split_composition(df, idx_tr, idx_val, idx_te):
    """Prints a detailed breakdown of the dataset splits."""
    def get_counts(indices):
        if len(indices) == 0:
            return pd.DataFrame()
        subset = df.iloc[indices]
        return subset.groupby(["source", "is_diseased"]).size().unstack(fill_value=0)

    print("\n--- Dataset Split Composition ---")
    print(f"{'Source':<20} | {'Train (H/D)':<15} | {'Val (H/D)':<15} | {'Test (H/D)':<15}")
    print("-" * 75)

    tr = get_counts(idx_tr)
    val = get_counts(idx_val)
    te = get_counts(idx_te)

    all_sources = sorted(set(df["source"]))
    for src in all_sources:
        counts = {}
        for lbl_key, dset in [("tr", tr), ("val", val), ("te", te)]:
            for cls in [0, 1]:
                val_count = 0
                for col in [float(cls), int(cls)]:
                    if col in dset.columns and src in dset.index:
                        val_count = dset.loc[src, col]
                        break
                counts[f"{lbl_key}_{cls}"] = val_count
        print(f"{src:<20} | {counts['tr_0']:>3}/{counts['tr_1']:<3}         | {counts['val_0']:>3}/{counts['val_1']:<3}         | {counts['te_0']:>3}/{counts['te_1']:<3}")
