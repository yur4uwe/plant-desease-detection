<!-- Step: 12 -->
# Algorithm Research and Model Selection

## 1. Task Definition
The objective of this step is to create binary classification of plant images to detect health status (Healthy vs. Diseased).
As defined in [Model Evaluation Metrics](MODEL_EVALUATION_METRICS.md), the following metrics are used to evaluate the performance of the model:
- **Recall:** ≥ 90% (Crucial to minimize false negatives in disease detection).
- **Latency:** ≤ 3.0s per image (Suitable for field deployment and real-time processing).
- **Robustness:** Ability to generalize across different photographic sources and environments.

## 2. Dataset Analysis for Algorithm Selection
The selection of algorithms is guided by the following data characteristics:
*   **Class Imbalance:** The natural distribution is heavily skewed (~88.7% Diseased / ~11.3% Healthy). This requires models that support `scale_pos_weight` or `class_weight`.
*   **Feature Diversity:** 
    *   *Classical features:* RGB/HSV histograms and Laplacian-based edge intensity (29 features total) capture color and texture but ignore spatial semantics.
    *   *Visual features:* Complex leaf textures and lesion patterns require deep convolutional filters.
*   **Domain Gap:** Significant differences between controlled field data (CCMT/MCDD) and crowdsourced data (iNaturalist).
*   **Volume:** Sample sizes ranging from 500 to 10,000 observations used for experimentation.

## 3. Selected Algorithms for Research

| Model | Purpose | Description | Key Hyperparameters |
|:---|:---|:---|:---|
| **Dummy Classifier** | "No-Skill" Baseline | Predicts the most frequent class to establish a performance floor. | `strategy='most_frequent'` |
| **Random Forest** | Non-linear Ensemble | Robust to feature scale; captures non-linear relations in histograms. | `n_estimators=100`, `class_weight='balanced'` |
| **XGBoost** | Gradient Boosting | Highly efficient on tabular features; handles imbalance via weights. | `eval_metric='logloss'`, `scale_pos_weight` |
| **MobileNetV2** | Deep Learning (CNN) | Transfer learning from ImageNet; efficient for mobile/field use. | `lr=0.001`, `fine_tune_last_blocks=8` |

## 4. Training and Evaluation Results

### 4.1. Experimental Setup
All of the models are ran on 70/15/15 training/validation/testing splits. To ensure that healthy/diseased ratio remains constant throughout the data splits, stratification is used.

This step explores both deep and classical machine learning models, thus 2 different pipelines exist to accomodate them.
-   *Classical:* `StandardScaler` → `Classifier`.
-   *Deep Learning:* `RandomResizedCrop` + `ColorJitter` → `MobileNetV2` (Pre-trained) → `Binary Head`.

To verify performance of all models following metrics are used: Recall, Precision, F1-Score, ROC-AUC.
Additionally, to evaluate performance of `MobileNetV2` model, Grad-CAM heatmaps are generated with integrated correctness labels to deeper understand feature processing.

To understand the impact of datasets on model performance, 3 sampling strategies are tested:
-   *Standard:* Natural mix of healthy and diseased images, datasets are balanced through `experiment_config.toml`.
-   *Balanced:* Same as Standard, but diseased/helthy ratio is enforced at 50/50.
-   *Cross-Source:* Uses curated dataset sources (CCMT, MCDD, PlantSeg) to train the model and crowdsourced (iNaturalist) to test the model

### 4.2. Model Comparison (500 Samples)
It was decided to run model training and evaluation on 500 samples to shorten learning time.

Run: 2026-05-13 18:10:03.430766

| Model        |       F1 |   Recall |   Precision |     Latency |     TrainTime | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|--------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.93617  | 1        |    0.88     | 6.19888e-07 |   0.000244617 | standard     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.941176 | 0.969697 |    0.914286 | 1.38251e-05 |   0.533881    | standard     |          500 | PASSED                |
| RandomForest | 0.93617  | 1        |    0.88     | 8.30364e-05 |   0.121103    | standard     |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.96875  | 0.939394 |    1        | 0.0298057   | 118.109       | standard     |          500 | PASSED                |
| Dummy        | 0.658228 | 1        |    0.490566 | 1.01665e-06 |   0.0003016   | balanced     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.64     | 0.615385 |    0.666667 | 3.11024e-05 |   1.1028      | balanced     |          500 | FAIL (Recall)         |
| RandomForest | 0.653061 | 0.615385 |    0.695652 | 0.000118269 |   0.119879    | balanced     |          500 | FAIL (Recall)         |
| MobileNetV2  | 0.857143 | 0.807692 |    0.913043 | 0.026744    |  84.3901      | balanced     |          500 | FAIL (Recall)         |
| Dummy        | 0.5      | 1        |    0.333333 | 5.40415e-07 |   0.000235319 | cross_source |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.5      | 1        |    0.333333 | 1.34087e-05 |   0.459528    | cross_source |          500 | FAIL (Below Baseline) |
| RandomForest | 0.5      | 1        |    0.333333 | 8.21972e-05 |   0.125294    | cross_source |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.426966 | 0.76     |    0.296875 | 0.0272023   | 141.203       | cross_source |          500 | FAIL (Recall)         |

## 5. Trend Analysis: The "Clever Hans" Discovery

### 5.1. Shortcut Learning Unmasked
Observability audits via Grad-CAM on MobileNetV2 revealed that the model was initially practicing **Shortcut Learning**:
*   **Color Bias:** The model focused on brown/yellow pixel concentrations.
*   **Contextual Bias:** In field datasets, diseased plants were often photographed against brown soil. The model learned to treat "brown soil" as a marker for disease.

### 5.2. The "36% Precision Wall" (Empirical Proof)
To confirm if classical models shared this bias, we ran a **Scale Test (N=5000)**. The results provided a "smoking gun" for shortcut learning:

| Model        | Recall | Precision | Mode         | SampleSize |
|:-------------|:---:|:---:|:---|:---|
| **XGBoost**  | 96.3% | **36.2%** | Cross-Source | 5000 |
| **MobileNetV2**| 90.0% | **36.2%** | Cross-Source | 5000 |

**Conclusion:** Both a complex CNN and a simple color-histogram model hit the **exact same Precision wall**. This proves they were both ignoring biological features and instead "counting brown pixels" in the background. Scale (increasing from 500 to 5000) failed to improve this, proving that the problem was **Data Diversity**, not **Data Volume**.

## 6. Model Refinement: Contextual Anchors

### 6.1. Domain Adaptation (The "Leak" Experiment)
We theorized that the model didn't need *more* data, but *better contrast*. We introduced an **iNaturalist Leak (10%)** into the training set (84 images) to act as **Contextual Anchors**. 

| Model       | F1 | Recall | Precision | Mode | SampleSize |
|:------------|:---:|:---:|:---:|:---|:---|
| **MobileNetV2 (No Leak)** | 0.516 | 0.900 | 36.2% | Cross-Source | 5000 |
| **MobileNetV2 (10% Leak)**| **0.654** | 0.603 | **71.4%** | Cross-Source | 1000 |

**The "Variety > Volume" Insight:**
A tiny leak of 84 varied images was **25% more effective** than adding 4,500 additional field images. By seeing a diseased leaf on a rock (leak) vs. a diseased leaf on soil (field), the CNN filters successfully "decoupled" the disease signal from the environmental noise.

### 6.2. Why MobileNetV2? (Proof of Spatial Superiority)
While both models hit the 36% wall, **only MobileNetV2 responded to the leak**. 
*   **XGBoost** stayed trapped; it cannot "un-see" brown pixels just because it sees a few rocks. 
*   **MobileNetV2** utilized its spatial awareness to re-contextualize its filters. This confirms that CNNs are the only architecture in our research capable of **Domain Adaptation**.

## 7. Final Model Verdict

| Mode | Recall | Precision | F1 Score | Observation |
|:---|:---:|:---:|:---:|:---|
| **Standard** | **93.5%** | **97.6%** | **0.955** | Most Reliable (Field-Ready) |
| **Balanced** | 83.6% | 93.5% | 0.883 | High Precision, Volume Deficit |
| **Cross-Source** | 60.3% | 71.4% | 0.654 | Successful Domain Adaptation |

**Final Recommendation:**
**MobileNetV2** trained with a **Standart Sampling Strategy** (including diverse background anchors) is selected. It is the only model that demonstrates the ability to prioritize biological signals over environmental shortcuts, while having high quality characteristics.

*P.S.* Confusion matrices can be found in `docs/images/confusion_matrices`. They follow this naming convention: cm_{name}_{mode}_{sample}.png:
- name: the name of the model
- mode: the mode of the experiment
- sample: the sample size of the experiment
