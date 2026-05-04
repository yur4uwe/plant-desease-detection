# Data Cleaning and Re-exploration Report (Step 10)

## 1. Limits and Thresholds for Numerical Attributes
Based on the initial EDA and domain constraints, the following boundaries were established for the attributes:

- **Latitude**: `[-51.14, 67.28]` (Hard limits applied: `[-90, 90]`)
- **Longitude**: `[-157.91, 175.85]` (Hard limits applied: `[-180, 180]`)
- **Temperature**: `[-7.02, 34.01]` °C (Values above ~50°C and below ~-20°C are highly unlikely and flagged as anomalies by the Isolation Forest).
- **Precipitation**: `[0.0, 52.4]` mm (Hard limits applied: values cannot be negative).

Synthetic data was injected containing extreme anomalies out of these bounds (e.g. Temperature > 80°C, Latitude > 95, Precipitation < 0), which were successfully identified and removed using a combination of hard logical rules and an `IsolationForest` model.

## 2. Automated Cleaning Pipeline Overview
The `scripts/cleaning_script.py` employs the following steps to ensure data quality:
1. **Deduplication**: Drops records identical in `source` and `external_id` and complete exact duplicates.
2. **Imputation**: Missing numerical metadata is filled via the feature's Median (`SimpleImputer(strategy='median')`), and categorical data is assigned 'Unknown'.
3. **Anomaly Detection**: `IsolationForest` with `contamination=0.01` detects multivariable outliers among `latitude`, `longitude`, `temperature`, and `precipitation`. Hard rules also filter logical impossibilities.
4. **Standardization**: Numerical columns are scaled with `StandardScaler` to normalize distributions (mean = 0, std = 1), preparing them for ML training.

## 3. Cleaning Methods to Attributes Mapping

| Method ↓ \ Attribute → | latitude | longitude | temperature | precipitation | season | solar_status | source | external_id |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Drop Duplicates** | | | | | | | Yes | Yes |
| **Imputation (Median)** | Yes | Yes | Yes | Yes | | | | |
| **Imputation ('Unknown')** | | | | | Yes | Yes | | |
| **Anomaly (Limits/Hard Rules)** | Yes | Yes | | Yes | | | | |
| **Isolation Forest** | Yes | Yes | Yes | Yes | | | | |
| **Standardization (Scaler)** | Yes | Yes | Yes | Yes | | | | |

*Note: Target variable (`is_diseased`), Image metadata (`image_url`, `label`) and Temporal metadata are left untouched as they represent the primary objective of classification or require separate processing routines.*
