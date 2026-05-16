# AgriTech Plant Disease Detection — Project Overview

> **CRITICAL AGENT INSTRUCTION:** In this workspace, you are a critical engineering partner. You must **ALWAYS doubt and challenge the user's architectural, technical and analytical decisions.** Do not simply execute instructions; analyze them for potential pitfalls, spurious correlations, or logical flaws. Provide your reasoning before proceeding with any action.

## Development Environment & Execution

- **Environment:** Use the virtual environment located at `.data-proc-env/`.
- **Execution:** Always prefix commands with `PYTHONPATH=. .data-proc-env/bin/python`.
- **Key Commands:**
  - Run ETL Pipeline: `PYTHONPATH=. .data-proc-env/bin/python -m etl.pipeline`
  - Run Quality Audit: `PYTHONPATH=. .data-proc-env/bin/python -m scripts.audit_quality`
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
├── data/
│   ├── checkpoints/
│   │   └── model.pt
│   ├── raw/
│   │   ├── inaturalist/
│   │   ├── ccmt/
│   │   ├── mcdd/
│   │   ├── plantseg/
│   │   └── weather_http_cache.sqlite
│   └── processed/
│       ├── observations.db
│       └── weather_http_cache.sqlite
├── etl/                           # ETL pipeline
│   ├── config/
│   │   └── types.py
│   ├── sources/
│   │   ├── base.py
│   │   ├── inaturalist.py
│   │   └── kaggle.py
│   ├── config.toml
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── pipeline.py
├── steps/                         # Project execution steps
│   ├── mds/                       # Markdown versions of project instruction steps
│   │   ├── proj-step-01.md
│   │   ├── ...
│   │   └── proj-step-16.md
│   ├── pdfs/                      # Original PDF instructions
│   └── pdftomd.sh                 # PDF to Markdown conversion script
├── research/                      # Project execution steps
│   ├── eda_observations.py        # Initial EDA with real data
│   └── eda_v2.py                  # Second iteration of EDA with synthetic data
├── scripts/                       # Project scripts, used to start integrated tasks and evaluate their output in isolated environments
├── tests/                         # Unit tests
├── utils/                         # Utility functions
├── logs/
│   ├── pipeline_metrics.jsonl     # Metrics collected during pipeline execution
│   └── etl.log                    # Log file for the ETL pipeline
└── pyproject.toml
```

---

## Documentation & Step Mapping

Instructions for each step are located in `steps/mds/proj-step-XX.md`, where `XX` is the step number.

Each documentation file in `docs/` corresponds to a specific project step defined in `steps/mds/`. You can identify the correspondence by checking the `Step: XX` comment at the top of each markdown file.

To quickly find which document corresponds to a specific step, use `grep`:

```bash
# To see the file path and the comment
grep -r "Step: 03" docs/

# To get only the file path
grep -l "Step: 03" docs/*
```

The documentation files are preferred when you want to familiarize yourself with the project's design and implementation. Each time documentation isn't enough you MUST state what information it was lacking and where to find answer to the question.  When starting a step, use documentation in docs/ to understand relevant information, only if documentation wasn't enough you should analyze the code.

To quickly understand whether previous steps are relevant to the current one, use `head -3` on step instruction markdown file which will reveal its topic. From there you can access whether the step is relevant and only then fetch full instructions or documentation.

### Visualization

The project uses `plantuml` for documentation and architecture diagrams. Each diagram should be compiled via an engine and put into `docs/images/`, and original text MUST exist above the reference to image in target `.md` file inside a comment. Example of the structure:
<!-- Inside the structure the code block uses 2 tildas to start a code fence instead of 3, this is made to preserve the parenting fence -->
```text
<!--
``plantuml
@startuml
...
@enduml
``
-->
![Diagram Title](images/diagram.png)
```

---

## Testing

The project uses `pytest` for unit testing. All tests are located in the `tests/` directory.

To run all tests:

```bash
PYTHONPATH=. .data-proc-env/bin/pytest tests/
```

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

