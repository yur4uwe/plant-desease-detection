<!-- Step: 12 -->
# Algorithm Research and Model Selection

## 1. Task Definition
**Objective:** Binary classification of plant images (Healthy vs. Diseased).
**Baseline Algorithm Requirement:** Must provide a balance of high Recall (sensitivity) and reasonable Precision.

## 2. Experimental Setup
*   **Dataset:** 10,000 images sampled from `observations.db`.
*   **Class Balance:** ~85% Diseased / ~15% Healthy (Reflecting local availability).
*   **Sources:** `local_ccmt_ghana`, `yolo_mcdd_india`, and `inaturalist` (Healthy samples).
*   **Features:** Classical Computer Vision features.
    *   **Color:** RGB and HSV histograms (to detect chlorosis and necrosis).
    *   **Texture:** Laplacian-based edge intensity (to detect lesion patterns and spots).

## 3. Model Comparison Results

| Model | Accuracy | Precision | Recall | F1-score |
| :--- | :---: | :---: | :---: | :---: |
| **XGBoost (Selected)** | **0.958** | **0.961** | **0.993** | **0.977** |
| Random Forest | 0.952 | 0.957 | 0.990 | 0.974 |
| Logistic Regression | 0.894 | 0.899 | 0.991 | 0.943 |

*Metrics obtained on a 20% hold-out test set.*

## 4. Hyperparameter Optimization
Randomized Search was performed on the XGBoost model.
*   **Optimized Parameters:** `n_estimators: 200`, `learning_rate: 0.1`, `max_depth: 5`.
*   **Result:** Optimization maintained stability but did not significantly improve the baseline, suggesting that the bottleneck lies in **Feature Engineering** (Classical vs. Deep Learning) rather than model tuning.

## 5. Data Drift and Generalization Analysis (Critical Finding)

A source-specific performance audit revealed significant **Concept Drift**:

| Source | F1-score | Observations |
| :--- | :---: | :--- |
| **local_ccmt_ghana** | 0.983 | Excellent performance on specific crop diseases. |
| **yolo_mcdd_india** | 0.975 | High robustness for agricultural field data. |
| **inaturalist** | **0.000** | **Total failure.** The model misclassifies healthy crowdsourced images as diseased. |

### Interpretation:
The model has learned a "narrow concept" of healthy plants based on the backgrounds and lighting of the CCMT/MCDD datasets. When presented with the diverse backgrounds of iNaturalist (different biomes, camera types), the classical color/texture features are insufficient to distinguish true disease from natural variation.

## 6. Decision and Justification
**Selected Model:** XGBoost with Classical Features.
**Justification:** While the model shows poor generalization to crowdsourced data, it is highly effective for controlled field observations (CCMT). It serves as a strong **baseline** for the next stage (Deep Learning), where we will use CNNs to extract more abstract features that should better resist source-based drift.

---
*(Confusion Matrices are located in docs/images/step12/)*
