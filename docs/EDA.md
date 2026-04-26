# Exploratory Data Analysis (EDA)

## 1. General Dataset Description
- **Business Context:** Machine learning task for an AgriTech company focused on binary image classification (Healthy vs. Diseased plants) to accelerate disease diagnosis on farms.
- **Data Sources:** A combined dataset sourced from iNaturalist (real-world field photography) and several specialized datasets (CCMT Ghana, MCDD India, PlantSeg).
- **Dataset Size:** 64,120 rows.
- **Key Attributes:** `source`, `external_id`, `image_url` (path/link to the photo), `label` (category), `is_diseased` (target variable), `latitude`, `longitude`, `observation_date`, `extracted_at`, `raw_json`, `provenance` (Field/Laboratory), `season`, `solar_status`, `temperature`, `precipitation`.
- **Data Types:**
  - **Text (string):** `source`, `external_id`, `image_url`, `label`, `provenance`, `season`, `solar_status`, `raw_json`.
  - **Numerical (float):** `latitude`, `longitude`, `temperature`, `precipitation`.
  - **Boolean (bool):** `is_diseased`.
  - **Temporal (datetime):** `observation_date`, `extracted_at`.
- **Feature Roles:**
  - **Identifiers:** `external_id`, `source`.
  - **Features:** `image_url` (primary feature for Computer Vision), environmental/geographical data.
  - **Target Variable:** `is_diseased` (0 = Healthy, 1 = Diseased).

## 2. Loading & Initial Overview
Data was loaded successfully within a Jupyter Notebook environment (`research/eda_observations.ipynb`) from the SQLite database (`observations.db`) using the `pandas` and `sqlite3` libraries. `matplotlib` and `seaborn` were utilized for visualization. The initial overview (`df.head()`, `df.info()`, `df.describe()`) confirmed schema integrity, column types, and foundational statistics.

### Data Preview
The first 10 records of the integrated dataset are shown below.

|  | id | source | external_id | image_url | label | is_diseased | latitude | longitude | observation_date | extracted_at | loaded_at | season | solar_status | temperature | precipitation | provenance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | inaturalist | 330798518 | https://inaturalist-open-data.s3.amazonaws.com... | Acer saccharinum | 1 | 44.940953 | -73.032345 | 2025-09-27 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Autumn | Daylight | 15.841667 | 0.0 | Field |
| 1 | 2 | inaturalist | 330767688 | https://inaturalist-open-data.s3.amazonaws.com... | Plantago major | 1 | 44.267068 | -72.272529 | 2025-09-24 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Autumn | Daylight | 16.535667 | 0.0 | Field |
| 2 | 3 | inaturalist | 330628454 | https://inaturalist-open-data.s3.amazonaws.com... | Convallaria majalis | 1 | 43.015294 | -71.586769 | 2025-08-28 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Summer | Daylight | 17.595835 | 0.0 | Field |
| 3 | 4 | inaturalist | 330030361 | https://inaturalist-open-data.s3.amazonaws.com... | Trillium erectum | 1 | 44.272735 | -72.278350 | 2025-07-31 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Summer | Night | 17.424999 | 0.7 | Field |
| 4 | 5 | inaturalist | 326671736 | https://inaturalist-open-data.s3.amazonaws.com... | Phoradendron juniperinum | 1 | 44.095539 | -121.330475 | 2025-11-08 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Autumn | Night | 3.266667 | 0.0 | Field |
| 5 | 6 | inaturalist | 300020531 | https://inaturalist-open-data.s3.amazonaws.com... | Holodiscus discolor | 1 | 45.415628 | -121.831787 | 2025-07-13 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Summer | Night | 20.763000 | 0.0 | Field |
| 6 | 7 | inaturalist | 297146627 | https://inaturalist-open-data.s3.amazonaws.com... | Phytolacca americana | 1 | 39.550136 | -74.570469 | 2025-07-11 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Summer | Night | 24.081251 | 2.4 | Field |
| 7 | 8 | inaturalist | 297127777 | https://inaturalist-open-data.s3.amazonaws.com... | Arceuthobium americanum | 1 | 44.620922 | -110.435822 | 2025-07-11 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Summer | Night | 13.839583 | 0.1 | Field |
| 8 | 9 | inaturalist | 296633279 | https://inaturalist-open-data.s3.amazonaws.com... | Quercus lobata | 1 | 37.621519 | -121.747261 | 2025-07-09 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Summer | Night | 19.296749 | 0.0 | Field |
| 9 | 10 | inaturalist | 294473862 | https://inaturalist-open-data.s3.amazonaws.com... | Arceuthobium americanum | 1 | 44.715205 | -110.475600 | 2025-06-22 | 2026-04-19T19:26:54 | 2026-04-19T19:30:57.041236+00:00 | Summer | Night | 4.114084 | 4.2 | Field |


### Schema Overview
The output of `df.info()` shows the schema, column types, and missing values of the dataset.

![Schema Overview](images/eda-schema-overview.png)
**Figure 1**: Schema overview showing the schema, column types and missing values of the dataset.

### Statisticsal Overview of Numerical Features
The output of `df.describe()` shows the descriptive statistics of selected numerical features.


|  | latitude | longitude | temperature | precipitation |
|---|---|---|---|---|
| count | 12123.000000 | 12123.000000 | 3841.000000 | 3840.000000 |
| mean | 39.165515 | -11.923393 | 14.261991 | 1.816693 |
| std | 20.165336 | 64.677659 | 6.432541 | 4.726792 |
| min | -51.140646 | -157.916488 | -7.025166 | 0.000000 |
| 25% | 36.107679 | -75.496890 | 8.791667 | 0.000000 |
| 50% | 43.376428 | -0.976545 | 13.376502 | 0.100000 |
| 75% | 50.576772 | 18.244351 | 18.895832 | 1.300000 |
| max | 67.288559 | 175.856107 | 34.016666 | 52.400002 |


### Statisticsal Overview of Categorical Features
The output of `df.select_dtypes(include=["object", "string"]).describe()` shows the descriptive statistics of selected categorical features.

| **field name** | **count** | **unique** | **top** | **freq** |
|---|---|---|---|---|
| **source** | 64120 | 4 | local_ccmt_ghana | 22339 |
| **external_id** | 64120 | 64120 | 330798518 | 1 |
| **image_url** | 64120 | 64117 | https://inaturalist-open-data.s3.amazonaws.com... | 2 |
| **label** | 64120 | 3003 | banana_yb_sigatoka | 2791 |
| **observation_date** | 64119 | 290 | 1970-01-01 | 51987 |
| **extracted_at** | 64120 | 130 | 2026-04-26T18:31:30 | 12502 |
| **loaded_at** | 64120 | 7 | 2026-04-26T18:31:42.018482+00:00 | 51987 |
| **season** | 12122 | 4 | Spring | 11172 |
| **solar_status** | 12122 | 4 | Daylight | 6589 |
| **provenance** | 64120 | 2 | Field | 55356 |


## 3. Data Quality & Completeness
The primary quality issue identified during the analysis is the high sparsity of metadata (geolocation, date, weather).

- **Missing Values:** Approximately 80% of the dataset lacks environmental metadata.
  - `inaturalist`: Metadata is present in 99.91% of records.
  - `local_ccmt_ghana`, `meta_plantseg`, `yolo_mcdd_india`: 100% missing metadata (these datasets contain only images and labels).
- **Target Distribution Imbalance in Metadata:** Healthy plants (0) have metadata in ~73.6% of cases (predominantly iNaturalist records), while diseased plants (1) possess metadata in only ~0.9% of cases.

### Missing Metadata
Analyzing the missing metadata across all sources.

| **field name** | **Missing** | **Percentage (%)** |
|---|---|---|
| **latitude** | 51997 | 81.093263 |
| **longitude** | 51997 | 81.093263 |
| **observation_date** | 51988 | 81.079226 |
| **season** | 51998 | 81.094822 |
| **solar_status** | 51998 | 81.094822 |
| **temperature** | 60279 | 94.009669 |
| **precipitation** | 60280 | 94.011229 |

### Metadata Presense by Source
Analyzing the presence of metadata by source. The table below shows the percentage of records that have metadata for each source. As expected, the iNaturalist source has the highest percentage of metadata (99.91%).

| **source** | **doesn't have** | **has metadata** |
|---|---|---|
| **inaturalist** | 0.090662 | 99.909338 |
| **local_ccmt_ghana** | 100.000000 | 0.000000 |
| **meta_plantseg** | 100.000000 | 0.000000 |
| **yolo_mcdd_india** | 100.000000 | 0.000000 |

### Metadata Presense by Target Class
Analyzing the presence of metadata by target class. The severe lack of metadata for the Diseased class caused by the sources the images come from which are local ccmt and mcdd.

| **is_diseased** | **doesn't have** | **has metadata** |
|---|---|---|
| **0** | 26.415213 | 73.584787 |
| **1** | 99.096167 | 0.903833 |


### Critical Label Defect Discovery
During the EDA process, a significant labeling defect was identified via the "Top 10 Labels". It unexpectedly revealed over 2,800 records assigned the label `IMG`. Deep inspection showed these images originated from the `mcdd_india` dataset. The validation and test splits of this dataset used generic filenames (e.g., `IMG-374.jpg`) instead of incorporating the class name into the file string. The pipeline's original regex extractor mistakenly stored "IMG" as the disease category. After uncovering this during EDA architectural fix was imminent. Dedicated `YoloSource` extractor was implemented to retrieve the true labels directly from the YOLO `.txt` annotation sidecar files, successfully classifying them into their correct categories (e.g., `banana_yb_sigatoka`, `groundnut_late_leaf_spot`).

## 4. Univariate Analysis

- **Target Variable:** There are 15,881 (24.77%) Healthy observations and 48,239 (75.23%) Diseased observations.
- **Categorical Features (Top Classes):** Following the YOLO label fix, the most frequent disease classes are `banana_yb_sigatoka`, `Tomato_septoria leaf spot`, `Cassava_bacterial blight`, `groundnut_late_leaf_spot`, and `Cashew_anthracnose`.

![Top 10 Labels](images/eda-top-labels.png)
**Figure 2**: Top 10 Labels highlighting the dominant disease classes across the integrated dataset.

- **Temporal Features:** Historical data leading up to 2019 is extremely scarce. The period from 2019 to 2025 exhibits a somewhat even distribution, but with notable gaps. Conversely, there is a massive observation spike in recent months due to the bulk ingestion of local static datasets. A logarithmic scale was strictly required to make historical points visible against the recent surge.

![Observation Intensity](images/eda-temporal-distribution.png)
**Figure 3**: Observation Intensity over Time (Log Scale) revealing the massive recent influx of static dataset records versus historical API data.

## 5. Bivariate & Multivariate Analysis

- **Correlation Matrix:** 
  - The correlation between the presence of disease (`is_diseased`) and weather conditions is negligible. The maximum correlation observed with the target variable is with `precipitation` at **0.11**.
  - The strongest correlation overall is between `latitude` and `temperature` at **-0.38**, which represents a natural geographical trend rather than an epidemiological one.

![Correlation Matrix](images/eda-correlation.png)
**Figure 4**: Correlation heatmap demonstrating the weak relationship between environmental metadata and plant disease.

Boxplots and violin plots comparing temperature/precipitation against disease status confirmed that weather conditions alone do not possess strong predictive power for classification within this dataset context.

## 6. Target Variable Analysis

- **Content:** `is_diseased` is a binary variable (0 = Healthy, 1 = Diseased).
- **Class Imbalance:** The dataset suffers from a significant class imbalance at a ratio of approximately 1:3 (Healthy:Diseased).

![Target Balance](images/eda-class-balance.png)
**Figure 5**: Target Class Balance demonstrating the 24.77% vs 75.23% skew toward diseased samples.

- **Implications for Modeling:** Because of this imbalance, `Accuracy` will be a misleading evaluation metric (as was mentioned in prevoius documents, though the balance was tipped the other way earlier). The project must evaluate success using **Precision, Recall, F1-score**, and **ROC-AUC**. Recall is specifically prioritized to minimize the business risk of missing a disease. Algorithm training will require balancing strategies such as class weighting (Class Weights), stratified batch sampling, or data augmentation specifically targeting the minority "Healthy" class.

## 7. Analytical Conclusions

**1. Is the dataset suitable for solving the business problem?**
Yes. With over 64,000 distinct observations, the dataset is sufficiently large to train a Computer Vision model (such as a CNN or Vision Transformer) for binary disease detection.

**2. What are the main data quality problems identified?**
- ~80% sparsity in geographic and environmental metadata.
- A 1:3 class imbalance between healthy and diseased samples.
- A critical labeling error (`IMG` labels from generic filenames) that was identified via EDA and subsequently resolved using a custom YOLO annotations extractor.

**3. Which features are potentially most useful for the model?**
Given the negligible correlation between disease and available weather metrics (max 0.11), the only highly informative and universally present feature is the visual data itself (`image_url`) alongside the target variable (`is_diseased`). The bet on temporal and location metadata usage as debiasing context turned out inconsequentual.

**4. What steps should be taken in the next data cleaning/modeling stage?**
- **Feature Selection:** Ignore missing numerical/weather columns during model training, as they lack predictive power and consistency.
- **Stratification:** Apply strict stratified sampling during the `train/val/test` split to preserve the 1:3 class proportion.
- **Balancing:** Configure Class Weights in the loss function or implement selective Data Augmentation to prevent the model from biasing toward the majority "Diseased" class.
- **Image Preprocessing:** Resize, crop, and normalize the raw images to meet the input tensor requirements of the selected neural network architecture.
