# AgriTech Plant Disease Detection — Project Overview

> **CRITICAL AGENT INSTRUCTION:** In this workspace, you are a critical engineering partner. You must **ALWAYS doubt and challenge the user's architectural, technical and analytical decisions.** Do not simply execute instructions; analyze them for potential pitfalls, spurious correlations, or logical flaws. Provide your reasoning before proceeding with any action. **All tests created by you must be kept in the `tests/` directory for regression testing.**

## Development Environment & Execution

- **Environment:** Use the virtual environment located at `.data-proc-env/`.
- **Execution:** Always prefix commands with `PYTHONPATH=. .data-proc-env/bin/python`.
- **Key Commands:**
  - Run ETL Pipeline: `PYTHONPATH=. .data-proc-env/bin/python etl/pipeline.py`
  - Run Quality Audit: `PYTHONPATH=. .data-proc-env/bin/python scripts/audit_quality.py`
  - Run Unit Tests: `PYTHONPATH=. .data-proc-env/bin/pytest tests/`

## What Is This Project?

This project develops a binary image classification model that detects the presence or absence of disease in plant photographs. It is built as a university data science project simulating the work of an AgriTech firm's internal development team.

The core business problem is simple: identifying crop disease currently requires expensive and slow agronomist consultations. By the time an expert visits, disease may have already spread across significant crop areas. This model compresses the initial detection stage from days to seconds — enabling farm owners to respond faster and at lower cost.

The deliverable is not a finished product but a complete, reproducible data science pipeline: from raw data collection through to a trained and evaluated classification model.

---

## Project Scope

**In scope:**
- Binary classification — healthy or diseased (not specific disease identification)
- Data collection pipeline from public internet sources
- ETL module for data ingestion, cleaning, and storage
- Model training and evaluation
- API development as a stretch goal

**Out of scope:**
- Multiclass disease identification
- Production deployment
- User interface
- Integration with farm management systems

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Type checking | basedpyright + ruff |
| Data validation | pandera |
| Data processing | pandas |
| HTTP client | requests |
| Storage | SQLite |
| Configuration | TOML |
| Image processing | Pillow / OpenCV (upcoming) |
| Model training | PyTorch (upcoming) |

---

## Project Structure

```
proj-data-processing/
├── docs/                          # Project documentation
│   ├── PROJECT_PLANNING.md        # Stage 1: Business context & SMART goals
│   ├── PROJECT_REQUIREMENT_ANALYSIS.md # Stage 2: UML & Requirements (MoSCoW)
│   ├── PIPELINE.md                # Stage 3: ETL implementation & transformations
│   ├── DATA_ARCHITECTURE.md       # Architectural mapping & ER diagrams
│   ├── DATA_QUALITY.md            # Quality audit reports & metrics
│   ├── MODEL_EVALUATION_METRICS.md # Target ML metrics & evaluation strategy
│   └── BUSINESS_EVALUATION.md     # Stage 4: Business KPIs & Integral evaluation
├── etl/                           # ETL pipeline
│   ├── config/
│   │   └── types.py
│   ├── sources/
│   │   ├── base.py
│   │   ├── inaturalist.py
│   │   └── kaggle.py
│   ├── data/
│   │   ├── raw/
│   │   │   └── inaturalist/
│   │   │       ├── diseased/
│   │   │       └── healthy/
│   │   └── processed/
│   │       └── observations.db
│   ├── logs/
│   ├── config.toml
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── pipeline.py
└── pyproject.toml
```

---

## What Has Been Done

### Stage 1 — Project Planning
*See [docs/PROJECT_PLANNING.md](docs/PROJECT_PLANNING.md)*

Established the foundational business context for the project:

- Defined the stakeholder problem — farm owners lack affordable, fast crop disease detection
- Formulated SMART objectives with a 16-week delivery timeline and 90% accuracy target
- Mapped the project lifecycle across five stages: Initiation, Planning, Execution, Monitoring, Closing
- Assessed data resources, identified risks across project, data, model, and product categories
- Justified business benefits including cost reduction, response time compression, and the economic threshold argument for precision intervention

---

### Stage 2 — Requirements Analysis
*See [docs/PROJECT_REQUIREMENT_ANALYSIS.md](docs/PROJECT_REQUIREMENT_ANALYSIS.md)*

Formalized the business problem and defined structured requirements:

- Applied the 5W method to precisely describe the problem context
- Wrote a Problem Statement covering ideal situation, current reality, consequences, and proposal
- Defined project scope boundaries explicitly
- Classified requirements into business, user, and system levels
- Built a Use Case Diagram and UML Activity Diagram covering the full classification flow
- Decomposed requirements and prioritized using MoSCoW
- Identified three key contradictions: accuracy vs. speed, robustness vs. accuracy, class balance vs. real data distribution
- Documented functional, non-functional, domain-specific, and data requirements
- Defined KPIs and acceptance criteria including F1-score ≥ 90%, inference time ≤ 3 seconds, and recall ≥ 90%

---

### Stage 3 — ETL Pipeline
*See [docs/PIPELINE.md](docs/PIPELINE.md)*

Built a modular, reproducible ETL pipeline for plant observation data:

**Data Source:** iNaturalist API — chosen for real-world field photography conditions that closely mirror actual farm use, as opposed to controlled lab datasets.

**Extract:**
- Multi-source architecture with `BaseSource` abstract class — new sources require only implementing `parse_config()` and `fetch()`
- **Project-based Validation:** Replaced faulty global term IDs with verified disease project IDs (e.g., North America Plant Diseases, PhD Pathogens) after a successful data migration.
- Page-level disk caching under `data/raw/inaturalist/` — prevents redundant HTTP requests on re-runs
- Alternating page strategy — fetches diseased observations from verified projects and healthy observations from general plant taxa (with project exclusion).
- Strict typing throughout using `TypedDict` for API response structures and `iNaturalistConfig` for configuration

**Transform:**
- Sequential transformation pipeline: normalize → deduplicate → parse dates → cast types → filter invalid coordinates → drop missing labels
- **Stratified Metadata Enrichment:** Derives approximate environmental context (Biological Season, Solar Status, Geographic Region) from (latitude, longitude, date). This is critical for model debiasing as it allows for balanced sampling across different environments, preventing the model from learning "shortcuts" or spurious correlations (e.g., associating autumn colors or low-light conditions with disease).
- **Bulk Weather Optimization:** Uses Open-Meteo's bulk API to fetch weather data in chunks of 50 locations, significantly reducing API latency and respecting rate limits more efficiently than individual row-based calls.
- Binary `is_diseased` label derived from verified project source — more reliable than generic API terms.

**Load:**
- SQLite storage with idempotent `INSERT OR IGNORE` — pipeline can be re-run safely without churning through existing records
- `UNIQUE (source, external_id)` constraint at database level
- `loaded_at` timestamp recorded on every row
- Post-load record count verification

---

### Stage 4 — Business Evaluation & Quality Assessment
*See [docs/BUSINESS_EVALUATION.md](docs/BUSINESS_EVALUATION.md)*

Formalized the business success metrics and integral quality evaluation system:

- **Business Context:** Re-anchored the project in the AgriTech domain, focusing on compressing the detection cycle to reduce crop loss.
- **KPI Definition:** Established 5 core business criteria: Cost Reduction (-40%), Risk Mitigation (< 5% loss), Decision Speed (< 3s), Efficiency (+300%), and Scalability (> 1000 RPM).
- **ML/Business Alignment:** Explicitly linked ML metrics (Recall) to business outcomes (Risk Mitigation), justifying the prioritization of Recall over Precision.
- **Integral Evaluation:** Implemented a weighted scoring model to calculate a total quality score (95.25%), categorizing the project as "High-Quality."
- **Feasibility Recommendation:** Concluded the project's viability and recommended a pilot deployment with Active Learning integration.

---

## Key Design Decisions

**Why binary classification instead of multiclass?**
The project definition specifies "detection" not "identification." A binary output — diseased or healthy — is sufficient to trigger a faster, cheaper response than waiting for an agronomist. Specific disease identification can follow as a second step with expert involvement.

**Why iNaturalist instead of PlantVillage?**
PlantVillage images are collected under controlled lab conditions — clean backgrounds, ideal lighting, standardized angles. iNaturalist photographs are taken by ordinary people in real field conditions, which better represents the distribution shift a production model would face.

**Why page-level caching instead of raw JSONL?**
Caching at the API response level allows the Extract stage to be re-run without redundant HTTP requests. The Transform stage reconstructs the full dataset from cached pages, making the JSONL intermediate layer unnecessary.

**Why SQLite instead of Parquet?**
SQLite allows immediate inspection via any SQL client during development and demonstration, supports idempotent loading through `INSERT OR IGNORE`, and is sufficient for the data volumes in this project.

**Data Storage Convention for Local Sources:**
For organizational/local archives where no remote URL is available, the `image_url` field stores a **relative path** from the project root (e.g., `etl/data/raw/ccmt/...`). This ensures portability and allows the model training stage to resolve image locations consistently regardless of the host environment.

---

