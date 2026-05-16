import os
import sqlite3
import time
from itertools import product
from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import tomllib
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image, ImageFilter, ImageOps
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    auc,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from tqdm import tqdm
from xgboost import XGBClassifier

optuna.logging.set_verbosity(optuna.logging.WARNING)

# --- Constants ---
DB_PATH = Path("data/processed/observations.db")
PROJECT_ROOT = Path(".").resolve()
CONFIG_PATH = Path("research/experiment_config.toml")
CM_OUTPUT_DIR = Path("docs/images/confusion_matrices")
ROC_OUTPUT_DIR = Path("docs/images/roc_curves")


def get_model_scores(
    name: str,
    actual: list[Any],
    preds: list[Any],
    latency: float,
    train_time: float = 0.0,
):
    return {
        "Model": name,
        "F1": f1_score(actual, preds, zero_division=0),  # pyright: ignore[reportArgumentType]
        "Recall": recall_score(actual, preds, zero_division=0),  # pyright: ignore[reportArgumentType]
        "Precision": precision_score(actual, preds, zero_division=0),  # pyright: ignore[reportArgumentType]
        "Latency": latency,
        "TrainTime": train_time,
    }


# --- Helper Classes (Data & Visualization) ---


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


class GradCAM:
    """Gradient-weighted Class Activation Mapping."""

    def __init__(self, model, target_layer):
        self.model, self.target_layer = model, target_layer
        self.gradients, self.activations = None, None
        self.target_layer.register_forward_hook(self._forward_hook)
        self.target_layer.register_full_backward_hook(self._backward_hook)

    def _forward_hook(self, _m, _i, o):
        self.activations = o

    def _backward_hook(self, _m, _i, o):
        self.gradients = o[0]

    def generate(self, input_tensor):
        self.model.zero_grad()
        output = self.model(input_tensor)
        output.backward()
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)  # pyright: ignore[reportCallIssue, reportArgumentType]
        cam = torch.relu(torch.sum(weights * self.activations, dim=1).squeeze())
        if output.item() < 0:
            cam = -cam
        cam = torch.relu(cam)
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-7)
        return cam.detach().cpu().numpy()


# --- Data Management Functions ---


def load_data_from_db() -> pd.DataFrame:
    """Loads and resolves paths for all observations."""
    print(f"Loading data from {DB_PATH}...")
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT external_id, image_url, is_diseased, source FROM observations", conn
        )

    def _resolve(row):
        p = PROJECT_ROOT / row["image_url"]
        if p.exists():
            return p

        # Generic fallback for local datasets with train/val/test/valid splits
        # if the database path is slightly off or missing the split directory.
        fname = Path(row["image_url"]).name
        source_dirs = {
            "meta_plantseg": "data/raw/plantseg/plantseg/images",
            "yolo_mcdd_india": "data/raw/mcdd/Multi-Crop Disease Dataset/Multicrop Disease Dataset/Multicrop Disease Dataset",
            "local_ccmt_ghana": "data/raw/ccmt",
        }

        if row["source"] in source_dirs:
            base_search = PROJECT_ROOT / source_dirs[row["source"]]
            for sub in [
                "",
                "train",
                "val",
                "valid",
                "test",
                "train/images",
                "valid/images",
                "test/images",
            ]:
                p_alt = base_search / sub / fname
                if p_alt.exists():
                    return p_alt

        # Fallback for inaturalist (which uses external_id in a specific folder)
        p_inat = (
            PROJECT_ROOT
            / "data"
            / "raw"
            / "inaturalist"
            / "images"
            / f"{row['external_id']}.jpg"
        )
        return p_inat if p_inat.exists() else None

    df["local_path"] = df.apply(_resolve, axis=1)
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
    
    # Extract leak weight and field source weights
    leak_w = weights.get("inaturalist_leak", 0.0)
    field_weights = {k: v for k, v in weights.items() if k != "inaturalist_leak"}
    
    field_df = base_df[base_df["source"].isin(field_weights.keys())]
    inat_df = base_df[base_df["source"] == "inaturalist"]

    if field_df.empty or inat_df.empty:
        return []

    # 1. Isolate Test Set (Strictly iNaturalist)
    te_sampled = inat_df.sample(n=min(len(inat_df), te_size), random_state=seed)
    
    # 2. Isolate Leak Pool (Remaining iNaturalist)
    remaining_inat = inat_df.drop(te_sampled.index)
    leak_n = int(tr_size * leak_w)
    
    leak_sampled = []
    if leak_n > 0:
        # Balance the leak pool (50/50 H/D)
        h_pool = remaining_inat[remaining_inat["is_diseased"] == 0]
        d_pool = remaining_inat[remaining_inat["is_diseased"] == 1]
        
        n_per = leak_n // 2
        if not h_pool.empty and not d_pool.empty:
            leak_sampled.append(h_pool.sample(n=min(len(h_pool), n_per), random_state=seed))
            leak_sampled.append(d_pool.sample(n=min(len(d_pool), n_per), random_state=seed))
            print(f"Leak: Sampled {len(leak_sampled[0]) + len(leak_sampled[1])} iNaturalist images into training.")

    # 3. Sample Field Training Set
    field_tr_size = tr_size - (leak_n if leak_n > 0 else 0)
    tr_field_sampled = _sample_balanced_quota(
        field_df, field_weights, field_tr_size, seed, allow_oversampling=True
    )

    # Return order: [Field sources..., Leak, Test]
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
        # Do not shuffle cross_source yet, as we need to split tr/te by index
        return pd.concat(sampled)
    
    return (
        pd.concat(sampled).sample(frac=1, random_state=seed)
        if sampled
        else pd.DataFrame(columns=base_df.columns)
    )


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
        # In cross_source, the last rows are the test set (sampled from iNaturalist)
        # All preceding rows are training (Field + iNaturalist Leak)
        te_size = int(size * test_pct)
        tr_full_size = len(df) - te_size
        
        df_tr_full = df.iloc[:tr_full_size]
        df_te = df.iloc[tr_full_size:]

        # Split tr_full into tr and val
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

    # Standard / Balanced path
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


# --- Training & Evaluation Functions ---


def optimize_xgboost(X_tr, y_tr, X_val, y_val) -> dict:
    """Use Optuna to find best hyperparameters for XGBoost using Val set."""

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 200),
            "max_depth": trial.suggest_int("max_depth", 2, 10),
            "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.5, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "eval_metric": "logloss",
            "scale_pos_weight": (len(y_tr) - y_tr.sum()) / y_tr.sum()
            if y_tr.sum() > 0
            else 1.0,
        }
        model = XGBClassifier(**params)
        pipe = Pipeline([("scaler", StandardScaler()), ("clf", model)])
        pipe.fit(X_tr, y_tr)
        preds = pipe.predict(X_val)
        return f1_score(y_val, preds, zero_division=0)  # pyright: ignore[reportArgumentType]

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=10)
    return study.best_params


def train_classical_models(
    X_tr, y_tr, X_val, y_val, X_te, y_te, mode, size, cfg
) -> list[dict]:
    """Trains and evaluates classical models."""
    results = []

    # Optionally combine train + val for final fit, or just use train.
    # To keep it simple, we just use train, as val was used for optuna.

    factories = {
        "Dummy": lambda: DummyClassifier(strategy="most_frequent"),
        "RandomForest": lambda: RandomForestClassifier(
            n_estimators=100, class_weight="balanced"
        ),
    }

    for name in cfg["models"]["list"]:
        train_start = time.time()

        if name == "XGBoost":
            print("Optimizing XGBoost with Optuna...")
            best_params = optimize_xgboost(X_tr, y_tr, X_val, y_val)
            # Re-initialize with best params
            best_params["scale_pos_weight"] = (
                (len(y_tr) - y_tr.sum()) / y_tr.sum() if y_tr.sum() > 0 else 1.0
            )
            best_params["eval_metric"] = "logloss"
            model = XGBClassifier(**best_params)
        elif name in factories:
            model = factories[name]()
        else:
            continue

        pipe = (
            Pipeline([("scaler", StandardScaler()), ("clf", model)])
            if name != "Dummy"
            else model
        )
        pipe.fit(X_tr, y_tr)
        train_time = time.time() - train_start

        start = time.time()
        preds = pipe.predict(X_te)
        latency = (time.time() - start) / len(X_te) if len(X_te) > 0 else 0

        # ROC
        if hasattr(pipe, "predict_proba"):
            preds_proba = pipe.predict_proba(X_te)[:, 1]
            save_roc_curve(y_te, preds_proba, name, mode, size, cfg)

        save_confusion_matrix(y_te, preds, name, mode, size)
        results.append(get_model_scores(name, y_te, preds, latency, train_time))
    return results


def train_deep_learning(df_tr, df_te, mode, size, cfg, device):
    """Trains and evaluates MobileNetV2."""
    norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    train_trans = transforms.Compose(
        [
            transforms.RandomResizedCrop(224, scale=(0.2, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(20),
            transforms.ColorJitter(0.3, 0.3, 0.3, 0.15),
            transforms.RandomGrayscale(0.3),
            transforms.ToTensor(),
            norm,
        ]
    )
    test_trans = transforms.Compose(
        [transforms.Resize((224, 224)), transforms.ToTensor(), norm]
    )

    m_cfg = cfg["models"]
    loaders = {
        "train": DataLoader(
            PlantDataset(df_tr, train_trans),
            batch_size=m_cfg["batch_size"],
            shuffle=True,
        ),
        "test": DataLoader(
            PlantDataset(df_te, test_trans), batch_size=m_cfg["batch_size"]
        ),
    }

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    for p in model.parameters():
        p.requires_grad = False
    for p in model.features[-m_cfg["fine_tune_last_blocks"] :].parameters():
        p.requires_grad = True
    model.classifier[1] = nn.Linear(model.last_channel, 1)
    model.to(device)

    opt = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=0.001)
    crit = nn.BCEWithLogitsLoss()

    train_time = 0.0
    for epoch in range(m_cfg["epochs"]):
        model.train()
        ep_start = time.time()
        for imgs, lbls in tqdm(
            loaders["train"],
            desc=f"DL Epoch {epoch + 1}/{m_cfg['epochs']}",
            leave=False,
        ):
            imgs, lbls = imgs.to(device), lbls.to(device)
            opt.zero_grad()
            crit(model(imgs).squeeze(), lbls).backward()
            opt.step()
        train_time += time.time() - ep_start

    model.eval()
    preds, actuals, latencies, preds_proba = [], [], [], []
    with torch.no_grad():
        for imgs, lbls in tqdm(loaders["test"], desc="Evaluating DL", leave=False):
            start = time.time()
            out = torch.sigmoid(model(imgs.to(device)).squeeze())
            latencies.append((time.time() - start) / len(imgs))

            # Handle case where batch size is 1 and squeeze makes it a scalar
            if out.dim() == 0:
                out = out.unsqueeze(0)

            preds_proba.extend(out.detach().cpu().numpy())
            preds.extend((out > 0.5).detach().cpu().numpy())
            actuals.extend(lbls.detach().cpu().numpy())

    save_confusion_matrix(actuals, preds, "MobileNetV2", mode, size)
    save_roc_curve(actuals, preds_proba, "MobileNetV2", mode, size, cfg)

    # Save model weights
    checkpoint_dir = PROJECT_ROOT / "data" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    model_path = checkpoint_dir / f"mobilenetv2_{mode}_{size}.pt"
    torch.save(model.state_dict(), model_path)
    print(f"Model weights saved to {model_path}")

    return get_model_scores(
        "MobileNetV2", actuals, preds, float(np.mean(latencies)), train_time
    ), model


# --- Visualization Functions ---


def save_confusion_matrix(y_true, y_pred, model_name: str, mode: str, size: int):
    """Generates and saves a confusion matrix plot."""
    CM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    disp = ConfusionMatrixDisplay(
        confusion_matrix=confusion_matrix(y_true, y_pred),
        display_labels=["Healthy", "Diseased"],
    )
    _, ax = plt.subplots(figsize=(6, 6))
    disp.plot(cmap="Blues", ax=ax, colorbar=False)
    ax.set_title(f"Confusion Matrix: {model_name}\n({mode}, N={size})")
    filename = f"cm_{model_name.lower().replace(' ', '_')}_{mode}_{size}.png"
    plt.savefig(CM_OUTPUT_DIR / filename, bbox_inches="tight")
    plt.close()


def save_roc_curve(
    y_true, y_pred_proba, model_name: str, mode: str, size: int, cfg: dict
):
    """Generates and saves ROC curve plot if enabled in config."""
    if not cfg.get("visualization", {}).get("save_roc_curve", False):
        return
    ROC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    roc_auc = auc(fpr, tpr)
    disp = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, name=model_name)
    _, ax = plt.subplots(figsize=(6, 6))
    disp.plot(ax=ax)
    ax.set_title(f"ROC Curve: {model_name}\n({mode}, N={size})")
    filename = f"roc_{model_name.lower().replace(' ', '_')}_{mode}_{size}.png"
    plt.savefig(ROC_OUTPUT_DIR / filename, bbox_inches="tight")
    plt.close()


def save_gradcam_visualizations(model, df, mode, size, cfg, device):
    """Generates and saves Grad-CAM heatmaps."""
    vis_cfg = cfg["visualization"]
    if not vis_cfg.get("save_grad_cam", False):
        return
    os.makedirs(vis_cfg["output_dir"], exist_ok=True)
    model.eval()
    gcam = GradCAM(model, model.features[-1])
    norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    trans = transforms.Compose(
        [transforms.Resize((224, 224)), transforms.ToTensor(), norm]
    )
    # Balanced sampling for Grad-CAM
    num_total = min(len(df), vis_cfg["num_samples"])
    num_per_class = num_total // 2

    diseased_df = df[df["is_diseased"] == 1]
    healthy_df = df[df["is_diseased"] == 0]

    # Handle cases where one class might have fewer samples than num_per_class
    d_samples = diseased_df.sample(
        n=min(len(diseased_df), num_per_class),
        random_state=cfg["sampling"]["random_state"],
    )
    h_samples = healthy_df.sample(
        n=min(len(healthy_df), num_per_class),
        random_state=cfg["sampling"]["random_state"],
    )

    samples = pd.concat([d_samples, h_samples]).sample(
        frac=1, random_state=cfg["sampling"]["random_state"]
    )

    for _, row in tqdm(samples.iterrows(), total=len(samples), desc="Grad-CAM"):
        try:
            img_pil = Image.open(row["local_path"]).convert("RGB")
            input_tensor = trans(img_pil).unsqueeze(0).to(device)

            # Get prediction and probability
            model.zero_grad()
            output = model(input_tensor)
            prob = torch.sigmoid(output).item()
            pred = prob > 0.5
            is_correct = pred == bool(row["is_diseased"])

            # Generate Grad-CAM mask
            mask = gcam.generate(input_tensor)

            img_res = img_pil.resize((224, 224))
            plt.figure(figsize=(10, 5))
            plt.subplot(1, 2, 1)
            plt.imshow(img_res)
            plt.axis("off")
            plt.title(f"Original\nID: {row['external_id']}\nSource: {row['source']}")

            plt.subplot(1, 2, 2)
            plt.imshow(img_res)
            plt.imshow(mask, cmap="jet", alpha=0.5, extent=(0, 224, 224, 0))
            plt.axis("off")

            status = "CORRECT" if is_correct else "WRONG"
            gt_label = "Diseased" if row["is_diseased"] else "Healthy"
            pred_label = "Diseased" if pred else "Healthy"
            plt.title(
                f"Grad-CAM [{status}]\nGT: {gt_label}, Pred: {pred_label} ({prob:.2f})"
            )

            plt.savefig(
                Path(vis_cfg["output_dir"])
                / f"gcam_{mode}_{size}_{row['external_id']}.png",
                bbox_inches="tight",
            )
            plt.close()
        except Exception as e:
            print(f"Error on {row['external_id']}: {e}")


# --- Reporting & Orchestration ---


def print_split_composition(df, idx_tr, idx_val, idx_te):
    """Prints a detailed breakdown of the dataset splits."""

    def get_counts(indices):
        if len(indices) == 0:
            return pd.DataFrame()
        subset = df.iloc[indices]
        return subset.groupby(["source", "is_diseased"]).size().unstack(fill_value=0)

    print("\n--- Dataset Split Composition ---")
    print(
        f"{'Source':<20} | {'Train (H/D)':<15} | {'Val (H/D)':<15} | {'Test (H/D)':<15}"
    )
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
                # Check both int and float column names
                for col in [float(cls), int(cls)]:
                    if col in dset.columns and src in dset.index:
                        val_count = dset.loc[src, col]
                        break
                counts[f"{lbl_key}_{cls}"] = val_count

        print(
            f"{src:<20} | {counts['tr_0']:>3}/{counts['tr_1']:<3}         | {counts['val_0']:>3}/{counts['val_1']:<3}         | {counts['te_0']:>3}/{counts['te_1']:<3}"
        )


def evaluate_gate(res, dummy_f1):
    """Checks business gates."""
    if res["Latency"] > 3.0:
        return "FAIL (Latency)"
    if res["Recall"] < 0.90:
        return "FAIL (Recall)"
    if res["F1"] <= dummy_f1:
        return "FAIL (Below Baseline)"
    return "PASSED"


def run_experiment_suite():
    """Main orchestrator for experiments."""
    import argparse

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

        if args.dry_run:
            print(f"Dry run enabled: Skipping training for {mode} (N={size}).")
            continue

        X = np.array(
            [
                f if (f := featurizer.extract_features(p)) is not None else np.zeros(29)
                for p in tqdm(df["local_path"], desc="Featurizing")
            ]
        )
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
                {"Mode": mode, "SampleSize": size, "Status": evaluate_gate(r, dummy_f1)}
            )
            all_results.append(r)

    report = pd.DataFrame(all_results)
    print("\n### Modular Experiment Results\n", report.to_markdown(index=False))


if __name__ == "__main__":
    run_experiment_suite()
