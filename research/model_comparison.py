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
LOG_PATH = Path("docs/EXPERIMENT_LOG.md")
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
        p = (
            PROJECT_ROOT
            / "data"
            / "raw"
            / "inaturalist"
            / "images"
            / f"{row['external_id']}.jpg"
        )
        return p if p.exists() else None

    df["local_path"] = df.apply(_resolve, axis=1)
    return cast(pd.DataFrame, df[df["local_path"].notnull()].copy())


def sample_by_composition(df: pd.DataFrame, total_size: int, cfg: dict) -> pd.DataFrame:
    """Samples data based on source/label composition rules."""
    sampled = []
    seed = cfg["sampling"]["random_state"]
    for source, s_cfg in cfg["composition"].items():
        source_n = int(total_size * s_cfg.get("dataset_weight", 0))
        if source_n <= 0:
            continue
        print(f"Sampling {source}:")
        for is_d in [True, False]:
            pct = s_cfg.get("diseased_pct" if is_d else "healthy_pct", 0) / 100.0
            n_target = int(source_n * pct)
            full_sample = df[(df["source"] == source) & (df["is_diseased"] == is_d)]
            n = min(len(full_sample), n_target)
            if n > 0:
                sampled.append(full_sample.sample(n=n, random_state=seed))
                print(f"+--{'Diseased' if is_d else 'Healthy'}: {n}")
    return (
        pd.concat(sampled).sample(frac=1, random_state=seed)
        if sampled
        else pd.DataFrame(columns=df.columns)
    )


def get_train_test_split(
    base_df: pd.DataFrame, mode: str, size: int, cfg: dict
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray] | None:
    """Splits the data into training, val, and testing sets based on the mode."""
    seed = cfg["sampling"]["random_state"]
    test_pct = cfg["sampling"]["test_size"]
    val_pct = cfg["sampling"].get("val_size", 0.15)

    if mode == "cross_source":
        field_df = base_df[
            base_df["source"].isin(["local_ccmt_ghana", "yolo_mcdd_india"])
        ]
        target_df = base_df[base_df["source"] == "inaturalist"]
        if field_df.empty or target_df.empty:
            return None
        df_train_full = field_df.sample(n=min(len(field_df), size), random_state=seed)
        df_test = target_df.sample(
            n=min(len(target_df), int(size * test_pct)), random_state=seed
        )

        # Split train_full into train and val
        val_relative_size = val_pct / (1.0 - test_pct)
        if val_relative_size >= 1.0:
            val_relative_size = 0.5
        idx_tr, idx_val = train_test_split(
            np.arange(len(df_train_full)),
            test_size=val_relative_size,
            random_state=seed,
            stratify=df_train_full["is_diseased"],
        )
        df = cast(
            pd.DataFrame, pd.concat([df_train_full, df_test]).reset_index(drop=True)
        )
        idx_te = np.arange(len(df_train_full), len(df))
        idx_tr = np.array(idx_tr)
        idx_val = np.array(idx_val)
        return df, idx_tr, idx_val, idx_te

    df = (
        base_df.sample(n=min(len(base_df), size), random_state=seed)
        if mode == "standard"
        else sample_by_composition(base_df, size, cfg)
    )
    if df.empty:
        return None

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
            transforms.RandomResizedCrop(224, scale=(0.65, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(0.2, 0.2, 0.2, 0.1),
            transforms.RandomGrayscale(0.2),
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
    disp = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name=model_name)
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
    samples = df.sample(n=min(len(df), vis_cfg["num_samples"]), random_state=42)

    for _, row in tqdm(samples.iterrows(), total=len(samples), desc="Grad-CAM"):
        try:
            img_pil = Image.open(row["local_path"]).convert("RGB")
            mask = gcam.generate(trans(img_pil).unsqueeze(0).to(device))  # pyright: ignore[reportAttributeAccessIssue]
            img_res = img_pil.resize((224, 224))
            plt.figure(figsize=(10, 5))
            plt.subplot(1, 2, 1)
            plt.imshow(img_res)
            plt.axis("off")
            plt.title(f"Original\nID: {row['external_id']}")
            plt.subplot(1, 2, 2)
            plt.imshow(img_res)
            plt.imshow(mask, cmap="jet", alpha=0.5, extent=(0, 224, 224, 0))
            plt.axis("off")
            plt.title(f"Grad-CAM\nDiseased: {bool(row['is_diseased'])}")
            plt.savefig(
                Path(vis_cfg["output_dir"])
                / f"gcam_{row['external_id']}_{mode}_{size}.png",
                bbox_inches="tight",
            )
            plt.close()
        except Exception as e:
            print(f"Error on {row['external_id']}: {e}")


# --- Reporting & Orchestration ---


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
    if not LOG_PATH.exists():
        LOG_PATH.write_text("# Experimentation Progress Log\n")
    with open(LOG_PATH, "a") as f:
        f.write(f"\n## Run: {pd.Timestamp.now()}\n{report.to_markdown(index=False)}\n")


if __name__ == "__main__":
    run_experiment_suite()
