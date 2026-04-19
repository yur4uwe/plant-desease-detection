# Data Quality Assessment System

## 1. Role of Data Quality in the Project

### Data Used
The primary data source is the **iNaturalist API**, providing plant observations including:
- Photographs (JPEG/PNG) — The primary input for the model.
- Metadata (IDs, taxon names, quality grades) — Used for filtering and traceability.
- Spatiotemporal data (coordinates, dates) — Used for metadata enrichment and debiasing.
- Annotations (diseased/healthy indicators) — The target label for supervised learning.

### Stratified Metadata Enrichment
The system derives environmental context (Biological Season, Solar Status, Weather) from (latitude, longitude, date) using exact astronomical calculations and historical weather APIs. This is a powerful tool for **model debiasing** — by categorizing observations into these bins, we perform stratified sampling to ensure the model does not learn "shortcuts" or spurious correlations (e.g., associating low-light conditions, specific seasons, or heavy precipitation with disease status).

### Criticality of Data Quality
Data quality ensures the reliability of the training pipeline:
- **Dataset Construction:** Accurate labels and high-quality images are the **critical** requirements.
- **Model Debiasing:** Valid spatiotemporal metadata is **important** to prevent environmental shortcuts. While its absence is acceptable for some sources, its presence allows for a much more robust training process.
- **Traceability:** Unique identifiers prevent data leakage and ensure reproducibility.

**Linkage:**
`High Data Quality` → `Clean & Unbiased (where possible) Training Sets` → `Robust Model` → `Precise Business Decisions`.

---

## 2. Selection of Data Quality Criteria

We have selected 8 criteria relevant to the project, focusing on both raw image quality and the metadata used for debiasing:

### 1. Повнота (Completeness)
- **Importance:** Crucial for training. An observation MUST have an `image_url` and an `is_diseased` label. Spatiotemporal fields are **important** for the debiasing strategy.
- **Measurement:** % of null/missing values in critical and important columns.

### 2. Коректність (Accuracy / Validity)
- **Importance:** Labels must be correct for the model to learn. When coordinates and dates are provided, they must be accurate to allow for reliable environmental binning.
- **Measurement:** % of records passing schema validation (coordinates in range, valid URLs).

### 3. Збалансованість (Balance)
- **Importance:** Crucial. We target a 1:1 ratio between Healthy and Diseased. **Stratified balance** across derived metadata (seasons, lighting) is also pursued to improve generalization.
- **Measurement:** Ratio of `is_diseased=True` vs `False` records globally and within available environmental bins.

### 4. Унікальність (Uniqueness)
- **Importance:** Prevents data leakage between training and testing sets.
- **Measurement:** Count of duplicate `external_id` values.

---

## 3. Data Quality Criteria, Metrics, and Verification Rules

| # | Quality Criterion | What is checked | Metric / Estimation Method | Threshold Value | Action on Violation |
|---|-------------------|-----------------|----------------------------|-----------------|---------------------|
| 1 | **Completeness** | Mandatory fields (`image_url`, `is_diseased`) | % missing values (null/NaN) | 0% | Drop records |
| 2 | **Uniqueness** | Record duplicates by `external_id` | % duplicate rows | 0% | Deduplicate |
| 3 | **Accuracy** | Coordinate ranges (lat, lon) | % invalid entries | 100% valid | Filter out invalid entries |
| 4 | **Balance** | Target class distribution | Class ratio (diseased / healthy) | 0.4 - 0.6 | Re-extract or resample |
| 5 | **Metadata Presence** | Lat/Lon/Date availability | % non-null metadata | ≥ 80% | Warn; tag as "un-debiased" |
| 6 | **Relevance** | Community quality grade | % research grade records | ≥ 70% | Priority for training |

---

## 4. Critical and Non-Critical Data Attributes

| Attribute | Data Type | Role in Project | Importance Level | Main Quality Risks |
|-----------|-----------|-----------------|------------------|-------------------|
| `image_url` | STRING | Link to training image | **Critical** | Broken links |
| `is_diseased` | BOOLEAN | Target label for model | **Critical** | Incorrect labeling |
| `external_id` | STRING | Unique identifier | **Critical** | Duplication |
| `latitude` | FLOAT | Model debiasing | **Important** | Out-of-range values |
| `longitude` | FLOAT | Model debiasing | **Important** | Out-of-range values |
| `observation_date`| DATETIME | Model debiasing | **Important** | Future dates |

---

## 5. Integral Quality Scoring System (Q)

The dataset is evaluated using a weighted integral score ($Q \in [0, 1]$):
- **w1 (0.50) - Essential:** Completeness of critical fields (`image_url`, `is_diseased`).
- **w2 (0.20) - Essential:** Uniqueness of `external_id` (Traceability).
- **w3 (0.20) - Robustness:** Presence of spatiotemporal metadata for debiasing.
- **w4 (0.10) - Stability:** Global class balance (Ideal = 0.5 ratio).

**Formula:** $Q = 0.50 \cdot q_1 + 0.20 \cdot q_2 + 0.20 \cdot q_3 + 0.10 \cdot q_4$

---

## 6. Initial Data Evaluation (Audit Results)

Based on the primary iNaturalist extraction (~6,400 records):

| Metric | Value | Status |
|---|---|---|
| **Integral Score (Q)** | **0.9359** | **High Quality** |
| Critical Completeness | 1.000 | 0 missing critical fields |
| Uniqueness | 1.000 | 0 duplicates |
| Metadata Coverage | 0.9986 | Almost all records have GPS/Date |
| Class Balance | **0.3614** | **CRITICAL IMBALANCE** (18% diseased) |

---

## 7. Risk Analysis and Mitigation

### Identified Risks:
1. **Majority Class Bias:** The 82/18 imbalance will make the model "lazy," predicting "Healthy" by default to achieve high accuracy.
   - *Mitigation:* Apply **Oversampling** (augmentation) for diseased samples or **Weighted Cross-Entropy** loss.
2. **Shortcut Bias (Environmental):** The model may associate "autumn colors" or "low-light GPS regions" with disease rather than the biological symptoms.
   - *Mitigation:* Use the 99.8% metadata coverage to perform **stratified sampling** to balance environments.
3. **Label Noise:** Crowdsourced labels may be inaccurate.
   - *Mitigation:* Prefer `research grade` observations and use **Label Smoothing** during training.

### Conclusion:
The dataset is technically sound ($Q > 0.9$) but analytically dangerous due to class imbalance. The next stage MUST focus on balancing the training set using the metadata tools we have built.
