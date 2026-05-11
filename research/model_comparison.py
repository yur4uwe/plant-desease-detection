import os
import sqlite3
import tomllib
from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image, ImageFilter, ImageOps
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from tqdm import tqdm
from xgboost import XGBClassifier

# --- Constants ---
DB_PATH = Path("data/processed/observations.db")
PROJECT_ROOT = Path(".").resolve()
CONFIG_PATH = Path("research/experiment_config.toml")
LOG_PATH = Path("docs/EXPERIMENT_LOG.md")


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
                # Histograms
                hists = [
                    np.histogram(arr[:, :, i], bins=8, range=(0, 255))[0]
                    for i in range(3)
                ]
                # HSV
                hsv_means = np.mean(np.array(img.convert("HSV")), axis=(0, 1))
                # Texture
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
    """Gradient-weighted Class Activation Mapping for visualizing model focus."""

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients: Any = None
        self.activations: Any = None
        self._hook_layers()

    def _hook_layers(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate(self, input_tensor):
        self.model.zero_grad()
        output = self.model(input_tensor)

        # For binary (1 output), we backprop the raw logit.
        output.backward()

        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1).squeeze()

        # If model predicts Healthy (output < 0), we want to see what
        # contributed to that negative score (flip the CAM).
        if output.item() < 0:
            cam = -cam

        cam = torch.relu(cam)
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-7)
        return cam.detach().cpu().numpy()


def save_gradcam_visualizations(model, df, cfg, device):
    """Generates and saves Grad-CAM heatmaps for a sample of images."""
    vis_cfg = cfg["visualization"]
    if not vis_cfg["enabled"]:
        return

    print(f"Generating Grad-CAM visualizations to {vis_cfg['output_dir']}...")
    os.makedirs(vis_cfg["output_dir"], exist_ok=True)

    model.eval()
    # For MobileNetV2, the last conv layer is the last item in 'features'
    target_layer = model.features[-1]
    gcam = GradCAM(model, target_layer)

    norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    trans = transforms.Compose(
        [transforms.Resize((224, 224)), transforms.ToTensor(), norm]
    )

    samples = df.sample(n=min(len(df), vis_cfg["num_samples"]), random_state=42)

    for _, row in tqdm(samples.iterrows(), total=len(samples), desc="Grad-CAM"):
        try:
            img_pil = Image.open(row["local_path"]).convert("RGB")
            input_tensor = trans(img_pil).unsqueeze(0).to(device)  # pyright: ignore[reportAttributeAccessIssue]

            mask = gcam.generate(input_tensor)

            # Resize original for plotting
            img_res = img_pil.resize((224, 224))

            plt.figure(figsize=(10, 5))
            plt.subplot(1, 2, 1)
            plt.imshow(img_res)
            plt.title(f"Original\nID: {row['external_id']}")
            plt.axis("off")

            plt.subplot(1, 2, 2)
            plt.imshow(img_res)
            # Extent is (left, right, bottom, top) - note the inverted top/bottom for image coords
            plt.imshow(mask, cmap="jet", alpha=0.5, extent=(0, 224, 224, 0))
            plt.title(f"Grad-CAM\nDiseased: {bool(row['is_diseased'])}")
            plt.axis("off")

            out_path = Path(vis_cfg["output_dir"]) / f"gcam_{row['external_id']}.png"
            plt.savefig(out_path, bbox_inches="tight")
            plt.close()
        except Exception as e:
            print(f"Error on {row['external_id']}: {e}")


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


def sample_by_disease(
    df: pd.DataFrame,
    is_diseased: bool,
    source: str,
    source_n: int,
    source_cfg: dict,
    seed: int,
) -> pd.DataFrame | None:
    conf_pct_key = "diseased_pct" if is_diseased else "healthy_pct"
    pct = source_cfg.get(conf_pct_key, 0) / 100.0
    n_target = int(source_n * pct)
    full_sample = df[(df["source"] == source) & (df["is_diseased"] == is_diseased)]

    n = min(len(full_sample), n_target)
    if n <= 0:
        return None
    return cast(pd.DataFrame, full_sample.sample(n=n, random_state=seed))


def sample_by_composition(df: pd.DataFrame, total_size: int, cfg: dict) -> pd.DataFrame:
    """Samples data based on source/label composition rules."""
    sampled = []
    seed = cfg["sampling"]["random_state"]
    for source, source_cfg in cfg["composition"].items():
        # Calculate samples for this source
        source_n = int(total_size * source_cfg.get("dataset_weight", 0))
        if source_n <= 0:
            continue

        print(f"Sampling {source}:")

        diseased_sample = sample_by_disease(
            df,
            is_diseased=True,
            source=source,
            source_n=source_n,
            source_cfg=source_cfg,
            seed=seed,
        )
        if diseased_sample is not None:
            sampled.append(diseased_sample)
            print(f"+--Diseased: {len(diseased_sample)}")

        healthy_sample = sample_by_disease(
            df,
            is_diseased=False,
            source=source,
            source_n=source_n,
            source_cfg=source_cfg,
            seed=seed,
        )
        if healthy_sample is not None:
            sampled.append(healthy_sample)
            print(f"+--Healthy: {len(healthy_sample)}")

    if not sampled:
        return pd.DataFrame(columns=df.columns)

    final = pd.concat(sampled).sample(frac=1, random_state=seed)
    return final


def train_classical_models(
    X_train, y_train, X_test, y_test, model_list: list
) -> list[dict]:
    """Trains and evaluates classical models."""
    results = []
    scale_pos = (
        (len(y_train) - y_train.sum()) / y_train.sum() if y_train.sum() > 0 else 1.0
    )

    factories = {
        "Dummy": lambda: DummyClassifier(strategy="most_frequent"),
        "RandomForest": lambda: RandomForestClassifier(
            n_estimators=100, class_weight="balanced"
        ),
        "XGBoost": lambda: XGBClassifier(
            eval_metric="logloss", scale_pos_weight=scale_pos
        ),
    }

    for name in model_list:
        if name not in factories:
            continue
        model = factories[name]()
        pipe = (
            Pipeline([("scaler", StandardScaler()), ("clf", model)])
            if name != "Dummy"
            else model
        )
        pipe.fit(X_train, y_train)
        f1 = f1_score(y_test, pipe.predict(X_test), zero_division=0)  # pyright: ignore[reportArgumentType]
        results.append({"Model": name, "F1": f1})
    return results


def train_deep_learning(df_train, df_test, cfg: dict, device: torch.device):
    """Trains and evaluates MobileNetV2."""
    norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    train_trans = transforms.Compose(
        [
            transforms.RandomResizedCrop(224, scale=(0.65, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(
                brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1
            ),
            transforms.RandomGrayscale(p=0.2),
            transforms.ToTensor(),
            norm,
        ]
    )
    test_trans = transforms.Compose(
        [transforms.Resize((224, 224)), transforms.ToTensor(), norm]
    )

    loaders = {
        "train": DataLoader(
            PlantDataset(df_train, train_trans),
            batch_size=cfg["batch_size"],
            shuffle=True,
        ),
        "test": DataLoader(
            PlantDataset(df_test, test_trans), batch_size=cfg["batch_size"]
        ),
    }

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    for p in model.parameters():
        p.requires_grad = False
    for p in model.features[-cfg["fine_tune_last_blocks"] :].parameters():
        p.requires_grad = True
    model.classifier[1] = nn.Linear(model.last_channel, 1)
    model.to(device)

    opt = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=0.001)
    crit = nn.BCEWithLogitsLoss()

    for epoch in range(cfg["epochs"]):
        model.train()
        pbar = tqdm(
            loaders["train"], desc=f"DL Epoch {epoch + 1}/{cfg['epochs']}", leave=False
        )
        for imgs, lbls in pbar:
            imgs, lbls = imgs.to(device), lbls.to(device)
            opt.zero_grad()
            loss = crit(model(imgs).squeeze(), lbls)
            loss.backward()
            opt.step()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

    model.eval()
    preds, actuals = [], []
    with torch.no_grad():
        for imgs, lbls in tqdm(loaders["test"], desc="Evaluating DL", leave=False):
            out = torch.sigmoid(model(imgs.to(device)).squeeze())
            preds.extend((out > 0.5).cpu().numpy())
            actuals.extend(lbls.numpy())

    return {
        "Model": "MobileNetV2",
        "F1": f1_score(actuals, preds, zero_division=0),  # pyright: ignore[reportArgumentType]
    }, model


def run_experiment_suite():
    """Main entry point for experiments."""
    with open(CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    featurizer = ImageFeaturizer()
    base_df = load_data_from_db()
    all_results = []

    for size in cfg["sampling"]["sample_sizes"]:
        print(f"\n>>> Running Experiment: Size={size}")
        df = sample_by_composition(base_df, size, cfg)

        if df.empty:
            print(f"Warning: No samples found for size {size}. Skipping.")
            continue

        # Classical Featurization
        X = np.array(
            [
                (
                    f
                    if (f := featurizer.extract_features(p)) is not None
                    else np.zeros(29)
                )
                for p in tqdm(df["local_path"], desc="Featurizing")
            ]
        )
        y = df["is_diseased"].values

        X_tr, X_te, y_tr, y_te, idx_tr, idx_te = train_test_split(
            X,
            y,
            np.arange(len(df)),
            test_size=cfg["sampling"]["test_size"],
            random_state=cfg["sampling"]["random_state"],
            stratify=y,
        )

        results = train_classical_models(X_tr, y_tr, X_te, y_te, cfg["models"]["list"])
        if "MobileNetV2" in cfg["models"]["list"]:
            res_dl, model_dl = train_deep_learning(
                df.iloc[idx_tr], df.iloc[idx_te], cfg["models"], device
            )
            results.append(res_dl)
            # Run Grad-CAM on the test set samples for this size
            save_gradcam_visualizations(model_dl, df.iloc[idx_te], cfg, device)

        for r in results:
            r["SampleSize"] = size
            all_results.append(r)

    # Reporting
    report = pd.DataFrame(all_results)
    print("\n### Modular Experiment Results", report.to_markdown(index=False))

    if not LOG_PATH.exists():
        LOG_PATH.write_text("# Experimentation Progress Log\n")
    with open(LOG_PATH, "a") as f:
        f.write(
            f"\n## Run: {pd.Timestamp.now()}\n" + report.to_markdown(index=False) + "\n"
        )


if __name__ == "__main__":
    run_experiment_suite()
