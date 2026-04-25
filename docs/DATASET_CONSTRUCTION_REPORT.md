# Dataset Construction Report — Plant Disease Detection (Binary)

## 1. Object of Observation
The **object of observation** is a single **plant photograph** accompanied by its spatiotemporal metadata (location and time). 

- **Justification:** This object is the fundamental unit of the business problem. Agronomists inspect individual plants or clusters to make a diagnosis; similarly, the model must process individual images to provide a detection result.
- **Business Alignment:** Since the goal is a mobile-accessible tool for farm owners, the image-per-observation granularity matches the way users interact with the system (taking a photo of a single leaf or plant).
- **Granularity Consistency:** All records in the dataset represent the same level of granularity (one record = one photographic observation).

## 2. Target Variable
The **target variable** is `is_diseased`.

- **Business Context:** It represents the binary presence or absence of any pathological condition in the photographed plant.
- **Type:** Binary (1 = Diseased, 0 = Healthy).
- **Formation:** 
    - For **iNaturalist** data, it is derived from source project validation (verified disease projects vs. general healthy plant taxa).
    - For **Local Sources**, it is mapped via directory structures or metadata flags provided by the original collectors.

## 3. Dataset Features (Attributes)

| Field Name | Description | Data Type | Role | Source |
|:---|:---|:---|:---|:---|
| `source` | Origin of the data (inaturalist, local_ccmt, etc.) | Categorical | ID | System |
| `external_id` | Unique ID from the original source | Categorical | ID | Source |
| `is_diseased` | **Target:** Presence of disease | Binary | **Target** | Source/ETL |
| `latitude` / `longitude` | Geographic coordinates | Numeric | Feature | Source |
| `observation_date` | Date/time of observation | Date/Time | Feature | Source |
| `label` | Taxonomic name (species/genus) | Text | Feature/Meta | Source |
| `temperature` | Avg temperature on the day of observation | Numeric | Feature (Derived) | Open-Meteo |
| `precipitation` | Precipitation on the day of observation | Numeric | Feature (Derived) | Open-Meteo |
| `season` | Biological season (Spring, Summer, etc.) | Categorical | Feature (Derived) | ETL Logic |
| `solar_status` | Lighting condition (Daylight, Night, etc.) | Categorical | Feature (Derived) | ETL Logic |
| `provenance` | Environment type (Field vs. Laboratory) | Categorical | Meta | System |

## 4. Dataset Structure
- **Format:** SQL Table (`observations` in `observations.db`) / Exportable to Parquet/CSV.
- **Estimated Records:** ~64,500 rows.
- **Estimated Features:** 15 columns.
- **Temporal Component:** Present (2007–2026 coverage).
- **Multimedia:** Linked via `image_url` (remote URLs or relative local paths).

## 5. ETL Logic & Integration
Data is integrated from four distinct sources into a unified SQLite schema:
1. **iNaturalist API:** Real-world field observations (Field provenance).
2. **Local Archives:** Standardized datasets from Ghana and India.
3. **Metadata CSVs:** Mapped from curated laboratory sources.
4. **Open-Meteo API:** Bulk-fetched weather context mapped via coordinates and time.

## 6. Primary Suitability Check
The dataset was audited using the `scripts/audit_quality.py` tool.
- **Completeness:** 100% for critical fields (`image_url`, `is_diseased`).
- **Integrity:** 0 duplicates across (source, external_id) pairs.
- **Class Balance:** **79% diseased / 21% healthy**. While significantly improved from earlier iterations, this remains a limitation.
- **Diversity:** ~1,900 unique taxonomic labels.

## 7. Dataset Passport
- **Name:** AgriTech-Plant-Obs-v1
- **Business Theme:** Agricultural Crop Protection
- **Business Task:** Early detection of plant disease to reduce crop loss and expert consultation costs.
- **Object of Observation:** Individual plant photograph.
- **Target Variable:** `is_diseased` (Binary).
- **Primary Sources:** iNaturalist, CCMT (Ghana), MCDD (India), PlantSeg.
- **Date of Formation:** 2026-04-25
- **Format:** SQLite
- **Potential Limitations:** 
    1. **Class Imbalance:** Strong bias toward diseased samples (79%).
    2. **API Limits:** iNaturalist fetching is restricted to 10k results per query window.
    3. **Metadata Coverage:** Weather and location metadata are available for ~10% of the total dataset.

## Conclusion
The dataset is **fit for purpose** for the development of a prototype binary classifier. The high taxonomic diversity and presence of environmental context (weather/season) provide a robust foundation for building a model that generalizes beyond lab conditions.
