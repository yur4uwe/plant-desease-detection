import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
from tqdm import tqdm
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, ConfusionMatrixDisplay
)
from xgboost import XGBClassifier
import os

# --- Configuration ---
DB_PATH = Path("data/processed/observations.db")
PROJECT_ROOT = Path(".").resolve()
SAMPLE_SIZE = 10000 
RANDOM_STATE = 42

# --- Feature Extraction ---
class ImageFeaturizer:
    def __init__(self, target_size=(128, 128)):
        self.target_size = target_size

    def extract_features(self, image_path: Path):
        try:
            if not image_path.exists():
                return None
            
            with Image.open(image_path) as img:
                img = img.convert("RGB").resize(self.target_size)
                arr = np.array(img)
                
                # 1. Color Histograms (RGB) - 8 bins/channel = 24 feats
                r_hist = np.histogram(arr[:,:,0], bins=8, range=(0, 255))[0]
                g_hist = np.histogram(arr[:,:,1], bins=8, range=(0, 255))[0]
                b_hist = np.histogram(arr[:,:,2], bins=8, range=(0, 255))[0]
                
                # 2. HSV Means - 3 feats
                hsv_arr = np.array(img.convert("HSV"))
                hsv_means = np.mean(hsv_arr, axis=(0, 1))
                
                # 3. Texture: Edge Intensity (Laplacian-like) - 2 feats
                gray = ImageOps.grayscale(img)
                edges = gray.filter(ImageFilter.FIND_EDGES)
                edge_arr = np.array(edges)
                edge_mean = np.mean(edge_arr)
                edge_std = np.std(edge_arr)
                
                return np.concatenate([r_hist, g_hist, b_hist, hsv_means, [edge_mean, edge_std]])
        except Exception:
            return None

def run_research():
    print(f"Loading data from {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT external_id, image_url, is_diseased, source FROM observations", conn)
    conn.close()

    # Resolve paths and filter
    def resolve_path(row):
        # 1. Check direct path (for CCMT/MCDD)
        p = PROJECT_ROOT / row['image_url']
        if p.exists(): return p
        
        # 2. Check iNaturalist download folder
        p = PROJECT_ROOT / "data" / "raw" / "inaturalist" / "images" / f"{row['external_id']}.jpg"
        if p.exists(): return p
        
        return None

    print("Resolving local image paths...")
    df['local_path'] = df.apply(resolve_path, axis=1)
    df = df[df['local_path'].notnull()].copy()
    
    if len(df) > SAMPLE_SIZE:
        _, df = train_test_split(
            df, 
            test_size=SAMPLE_SIZE, 
            random_state=RANDOM_STATE, 
            stratify=df[['is_diseased', 'source']]
        )

    print(f"Extracting features for {len(df)} images...")
    featurizer = ImageFeaturizer()
    X, y, sources = [], [], []
    
    for _, row in tqdm(df.iterrows(), total=len(df)):
        feat = featurizer.extract_features(row['local_path'])
        if feat is not None:
            X.append(feat)
            y.append(row['is_diseased'])
            sources.append(row['source'])
            
    X, y, sources = np.array(X), np.array(y), np.array(sources)

    # Splits
    X_train, X_test, y_train, y_test, s_train, s_test = train_test_split(
        X, y, sources, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=100),
        "XGBoost": XGBClassifier(eval_metric='logloss')
    }

    results = []
    os.makedirs("docs/images/step12", exist_ok=True)

    for name, model in models.items():
        print(f"Training {name}...")
        pipe = Pipeline([('scaler', StandardScaler()), ('clf', model)])
        pipe.fit(X_train, y_train)
        
        y_pred = pipe.predict(X_test)
        
        res = {
            "Model": name,
            "Accuracy": accuracy_score(y_test, y_pred),
            "Precision": precision_score(y_test, y_pred),
            "Recall": recall_score(y_test, y_pred),
            "F1-score": f1_score(y_test, y_pred)
        }
        results.append(res)
        
        # Save CM
        fig, ax = plt.subplots()
        ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=ax, cmap='Greens')
        ax.set_title(f"CM: {name}")
        plt.savefig(f"docs/images/step12/cm_{name.lower().replace(' ', '_')}.png")
        plt.close()

    # --- Hyperparameter Optimization (XGBoost) ---
    print("\nOptimizing XGBoost...")
    param_grid = {
        'clf__n_estimators': [50, 100, 200],
        'clf__learning_rate': [0.01, 0.1, 0.2],
        'clf__max_depth': [3, 5, 7]
    }
    search = RandomizedSearchCV(
        Pipeline([('scaler', StandardScaler()), ('clf', XGBClassifier(eval_metric='logloss'))]),
        param_grid, n_iter=5, cv=3, scoring='f1', random_state=RANDOM_STATE
    )
    search.fit(X_train, y_train)
    
    y_opt_pred = search.predict(X_test)
    results.append({
        "Model": "XGBoost (Optimized)",
        "Accuracy": accuracy_score(y_test, y_opt_pred),
        "Precision": precision_score(y_test, y_opt_pred),
        "Recall": recall_score(y_test, y_opt_pred),
        "F1-score": f1_score(y_test, y_opt_pred)
    })

    # --- Drift Analysis ---
    print("\n--- Drift Analysis (F1-score by Source) ---")
    best_pipe = search.best_estimator_
    drift_data = []
    for src in np.unique(s_test):
        mask = s_test == src
        if mask.sum() > 0:
            f1 = f1_score(y_test[mask], best_pipe.predict(X_test[mask]))
            drift_data.append({"Source": src, "F1": f1, "Count": mask.sum()})
    
    # --- Final Report ---
    print("\n### Model Ranking")
    print(pd.DataFrame(results).sort_values("F1-score", ascending=False).to_markdown(index=False))
    
    print("\n### Drift Report")
    print(pd.DataFrame(drift_data).to_markdown(index=False))

if __name__ == "__main__":
    run_research()
