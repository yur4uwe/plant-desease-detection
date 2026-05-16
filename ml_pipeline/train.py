import time
from pathlib import Path

import numpy as np
import optuna
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader
from torchvision import models, transforms
from tqdm import tqdm
from xgboost import XGBClassifier

from ml_pipeline.data import PlantDataset
from ml_pipeline.evaluate import (
    get_model_scores,
    save_confusion_matrix,
    save_roc_curve,
)

PROJECT_ROOT = Path(".").resolve()


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
        return f1_score(y_val, preds, zero_division=0)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=25)
    return study.best_params


def optimize_random_forest(X_tr, y_tr, X_val, y_val) -> dict:
    """Use Optuna to find best hyperparameters for Random Forest using Val set."""

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 200),
            "max_depth": trial.suggest_int("max_depth", 2, 20),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            "class_weight": "balanced",
        }
        model = RandomForestClassifier(**params)
        pipe = Pipeline([("scaler", StandardScaler()), ("clf", model)])
        pipe.fit(X_tr, y_tr)
        preds = pipe.predict(X_val)
        return f1_score(y_val, preds, zero_division=0)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=25)
    return study.best_params


def train_classical_models(
    X_tr, y_tr, X_val, y_val, X_te, y_te, mode, size, cfg
) -> list[dict]:
    """Trains and evaluates classical models."""
    results = []

    factories = {
        "Dummy": lambda: DummyClassifier(strategy="most_frequent"),
        "RandomForest": lambda: RandomForestClassifier(
            **{
                **optimize_random_forest(X_tr, y_tr, X_val, y_val),
                "class_weight": "balanced",
            }
        ),
        "XGBoost": lambda: XGBClassifier(
            **{
                **optimize_xgboost(X_tr, y_tr, X_val, y_val),
                "scale_pos_weight": (len(y_tr) - y_tr.sum()) / y_tr.sum()
                if y_tr.sum() > 0
                else 1.0,
                "eval_metric": "logloss",
            }
        ),
    }

    for name in cfg["models"]["list"]:
        if name not in factories:
            continue

        print(f"Training {name}...")
        train_start = time.time()
        model = factories[name]()

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

        preds_proba = None
        if hasattr(pipe, "predict_proba"):
            preds_proba = pipe.predict_proba(X_te)[:, 1]
            save_roc_curve(y_te, preds_proba, name, mode, size, cfg)

        save_confusion_matrix(y_te, preds, name, mode, size)
        results.append(
            get_model_scores(
                name, y_te, preds, latency, train_time, probs=preds_proba
            )
        )
    return results


def train_deep_learning(df_tr, df_te, mode, size, cfg, device):
    """Trains and evaluates MobileNetV2 with optimized hyperparameters."""
    norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    # Relaxed crop to ensure disease features are preserved
    train_trans = transforms.Compose(
        [
            transforms.RandomResizedCrop(224, scale=(0.5, 1.0)),
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
    # Adding scheduler for better convergence
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=m_cfg["epochs"])
    
    # Calculate pos_weight for BCEWithLogitsLoss to handle imbalance
    num_neg = (df_tr["is_diseased"] == 0).sum()
    num_pos = (df_tr["is_diseased"] == 1).sum()
    pos_weight_val = num_neg / num_pos if num_pos > 0 else 1.0
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight_val]).to(device))

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
            crit(model(imgs).view(-1), lbls).backward()
            opt.step()
        sched.step()
        train_time += time.time() - ep_start

    model.eval()
    preds, actuals, latencies, preds_proba = [], [], [], []
    with torch.no_grad():
        for imgs, lbls in tqdm(loaders["test"], desc="Evaluating DL", leave=False):
            start = time.time()
            out = torch.sigmoid(model(imgs.to(device)).view(-1))
            latencies.append((time.time() - start) / len(imgs))

            preds_proba.extend(out.detach().cpu().numpy())
            preds.extend((out > 0.5).detach().cpu().numpy())
            actuals.extend(lbls.detach().cpu().numpy())

    save_confusion_matrix(actuals, preds, "MobileNetV2", mode, size)
    save_roc_curve(actuals, preds_proba, "MobileNetV2", mode, size, cfg)

    checkpoint_dir = PROJECT_ROOT / "data" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    model_path = checkpoint_dir / f"mobilenetv2_{mode}_{size}.pt"
    torch.save(model.state_dict(), model_path)
    print(f"Model weights saved to {model_path}")

    return (
        get_model_scores(
            "MobileNetV2",
            actuals,
            preds,
            float(np.mean(latencies)),
            train_time,
            probs=preds_proba,
        ),
        model,
    )
