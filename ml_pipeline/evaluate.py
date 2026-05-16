import os
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from torchvision import transforms
from tqdm import tqdm

# --- Constants ---
PROJECT_ROOT = Path(".").resolve()
CM_OUTPUT_DIR = PROJECT_ROOT / "docs/images/confusion_matrices"
ROC_OUTPUT_DIR = PROJECT_ROOT / "docs/images/roc_curves"

def get_model_scores(
    name: str,
    actual: list[Any],
    preds: list[Any],
    latency: float,
    train_time: float = 0.0,
    probs: list[float] | None = None,
):
    roc_auc = 0.0
    if probs is not None:
        try:
            roc_auc = roc_auc_score(actual, probs)
        except Exception:
            pass

    return {
        "Model": name,
        "Accuracy": accuracy_score(actual, preds),
        "F1": f1_score(actual, preds, zero_division=0),
        "Recall": recall_score(actual, preds, zero_division=0),
        "Precision": precision_score(actual, preds, zero_division=0),
        "ROC_AUC": roc_auc,
        "Latency": latency,
        "TrainTime": train_time,
    }

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

def evaluate_gate(res, dummy_f1):
    """Checks business gates."""
    if res["Latency"] > 3.0:
        return "FAIL (Latency)"
    if res["Recall"] < 0.90:
        return "FAIL (Recall)"
    if res["F1"] <= dummy_f1:
        return "FAIL (Below Baseline)"
    return "PASSED"

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
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.relu(torch.sum(weights * self.activations, dim=1).squeeze())
        if output.item() < 0:
            cam = -cam
        cam = torch.relu(cam)
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-7)
        return cam.detach().cpu().numpy()

def save_gradcam_visualizations(model, df, mode, size, cfg, device):
    """Generates and saves Grad-CAM heatmaps."""
    vis_cfg = cfg["visualization"]
    if not vis_cfg.get("save_grad_cam", False):
        return
    os.makedirs(vis_cfg["output_dir"], exist_ok=True)
    model.eval()
    # Assume MobileNetV2 structure
    gcam = GradCAM(model, model.features[-1])
    norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    trans = transforms.Compose(
        [transforms.Resize((224, 224)), transforms.ToTensor(), norm]
    )
    num_total = min(len(df), vis_cfg["num_samples"])
    num_per_class = num_total // 2

    diseased_df = df[df["is_diseased"] == 1]
    healthy_df = df[df["is_diseased"] == 0]

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

            model.zero_grad()
            output = model(input_tensor)
            prob = torch.sigmoid(output).item()
            pred = prob > 0.5
            is_correct = pred == bool(row["is_diseased"])

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
