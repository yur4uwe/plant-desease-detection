# Migration: Disease Identification Strategy

## 1. Problem Identification
During a data audit, it was discovered that the `is_diseased` label in the ETL pipeline was based on an incorrect mapping of iNaturalist controlled terms.

*   **Previous (Faulty) Mapping:**
    *   `term_id=9` (Expected: Health Status | Actual: **Sex**)
    *   `term_value_id=11` (Expected: Diseased | Actual: **Male**)
*   **Impact:** The current dataset consists of "Male Plants" labeled as "Diseased" and "Female/Other Plants" labeled as "Healthy." This makes the trained model a gender classifier for plants rather than a disease classifier.

---

## 2. New Identification Strategy
Instead of relying on global controlled terms, which are not standardized for disease on iNaturalist, the pipeline will depend on project-based strategy. We will fetch observations from curated, research-grade projects dedicated specifically to plant pathology.

### Target Projects & IDs:
| Project Slug | Project ID | Region / Focus |
| :--- | :--- | :--- |
| `non-metazoan-plant-diseases-of-north-america` | 49595 | North America |
| `plants-afflicted-by-pests-and-diseases-in-nz` | 124267 | New Zealand |
| `rogue-valley-plant-pathogen-mapping` | 227684 | US (Regional) |
| `plant-pathogens-of-the-eastern-united-states` | 47428 | US (Eastern) |
| `plant-pathogens-phd` | 255039 | Global / PhD Research |

---

## 3. Required Changes

### Phase A: Configuration Update
*   Modify `etl/config/types.py` to include `project_ids` in the `iNaturalistConfig` model.
*   Update `etl/config.toml` to remove `term_id`/`term_value_id` and replace them with the list of verified project IDs.

### Phase B: Source Code Update
*   Update `etl/sources/inaturalist.py`:
    *   Modify `fetch()` to use the `project_id` parameter when requesting diseased observations.
    *   Implement a "Healthy Control" fetcher that queries the general `taxon_id=47126` but filters observations *out* of those specific disease projects.

### Phase C: Data Purge & Reload
*   Delete existing cache: `rm -rf etl/data/raw/inaturalist/*`.
*   Drop existing database records to prevent pollution.
*   Execute `PYTHONPATH=. .data-proc-env/bin/python etl/pipeline.py` to rebuild the dataset.

---

## 4. Confirmation & Validation
1.  **Visual Audit:** Randomly select 10 images from `data/raw/inaturalist/diseased/` and confirm they show visible symptoms (rust, spots, blight).
2.  **Metadata Audit:** Confirm that observations in the `diseased` folder contain one of the project IDs listed above in their raw metadata.
3.  **Schema Validation:** Re-run `scripts/audit_quality.py` to ensure the new data maintains structural integrity.

---

## 5. Status Log
- **[2026-04-19]:** Migration document created. Problem confirmed via API manual check. Project IDs verified.
- **[2026-04-19]:** Phase A & B complete. Configuration and source code updated with rate limiting and project-based logic.
- **[2026-04-19]:** Phase C complete. Cache purged, DB reset, and pipeline executed successfully.
- **[2026-04-19]:** Migration Successful. Dataset rebuilt with 1351 observations (387 Diseased, 964 Healthy). Preliminary audit confirms presence of parasitic plants (Arceuthobium) and algae-based diseases (Cephaleuros).
