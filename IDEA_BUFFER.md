# Idea Buffer & Technical Debt

## Architectural Goals
- **Source Agnosticity:** Transition from source-specific extraction logic to a unified Integration Layer. Source classes should handle their own mechanics (pagination, auth, local vs remote), while the pipeline treats them as `RawObservation` generators.
- **Weather API Rotation:** Monitor Open-Meteo usage (~27 calls/run currently). If scaling beyond 10k/day, implement a rotation strategy with secondary providers (e.g., Pirate Weather or Visual Crossing).

## Data Quality & Model Bias
- **Class Imbalance:** Address the current skew (964 Healthy vs 387 Diseased) by integrating secondary sources (Kaggle/Local) specifically for diseased samples.
- **Environmental Context (The "Lab Trap"):** 
    - **Problem:** Datasets like PlantVillage are "laboratory-clean" (uniform backgrounds, perfect lighting), while iNaturalist is "field-messy."
    - **Solution:** Add a `condition_type` or `environment` metadata field. Categories: `Field`, `Laboratory`, `Unknown`.
    - **Impact:** Use this field during model training for domain adaptation or to prevent the model from learning "clean background = diseased" shortcuts.
- **Data Enrichment & Recovery (`scripts/backfill.py`):**
    - **Objective:** Create a dedicated utility to populate missing metadata columns (`temperature`, `precipitation`, `observation_date`, `latitude`, `longitude`) for existing records in `observations.db`.
    - **Strategy 1 (Weather):** Re-trigger Open-Meteo bulk calls for rows where coordinates and date exist but weather data is NULL.
    - **Strategy 2 (EXIF):** For local source images (`source='local'`), extract embedded EXIF metadata (GPS, DateTimeOriginal) to fill missing spatial/temporal fields.
    - **Strategy 3 (Imputation):** Use seasonal/regional averages for records where external APIs fail to provide data.

## Candidate Sources
- **Kaggle (PlantVillage):** High volume, high quality, but strictly `Laboratory`. Needs mapping: `*___healthy` -> 0, others -> 1.
- **Kaggle (PlantDoc):** Real-world conditions (Field), useful for object detection but can be adapted for classification.
- **CCMT (Ghana):** Organizational field data for tropical crops.
- **MCDD (India):** Large-scale multi-crop field dataset.
- **PlantSeg:** Precise disease labeling with metadata mapping.

## Pipeline Robustness & DX
- **Weather Fetching Progress:** Implement a progress bar (e.g., `tqdm`) or incremental logging (e.g., "Fetched 500/2200...") to provide visual feedback during long, rate-limited Open-Meteo bulk calls.
- **Data Checkpoints:**
    - **Problem:** If the pipeline fails at the `Load` stage, all `Transform` work is lost.
    - **Solution:** Implement an intermediate "Checkpoint" (e.g., saving the transformed DataFrame to a temporary Parquet file). 
    - **Logic:** `run_pipeline` should check for a valid checkpoint and offer to skip directly to `Load` if one exists, saving API credits and compute time.
