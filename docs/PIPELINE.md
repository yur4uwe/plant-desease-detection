# AgriTech Plant Disease Detection — ETL Module Documentation

## 1. Data Source Selection

### Source: iNaturalist API
- **URL:** https://api.inaturalist.org/v1
- **Relevance:** iNaturalist contains millions of real-world plant observations photographed by ordinary people in field conditions — varying lighting, angles, camera quality, and backgrounds. This closely mirrors the conditions under which a farm owner would photograph crops, making it the most realistic training data source for a binary plant disease classifier compared to controlled lab datasets like PlantVillage.
- **Data Format:** JSON REST API responses containing observation objects with photos, taxonomic labels, annotations, geolocation, and observation date.
- **Access Constraints:**
  - No authentication required for read access
  - Maximum 200 results per page
  - Rate limiting recommended at 1 second between requests
  - Research-grade observations filtered for label quality
  - Update frequency: continuous — new observations added daily

---

## 2. Input Data Structure Analysis

### Key Entities and Attributes

| Field | Description | Type | Example | Role in Analysis |
|---|---|---|---|---|
| `id` | Unique observation identifier | `int` | `12345678` | Primary key |
| `photos[].url` | URL of observation photograph | `str` | `https://...` | Image source for model training |
| `taxon.name` | Scientific plant name | `str` | `Solanum lycopersicum` | Taxonomic label |
| `annotations[].controlled_attribute_id` | Annotation type identifier | `int` | `9` | Disease/health status detection |
| `annotations[].controlled_value.label` | Annotation value label | `str` | `Disease` | Binary label derivation |
| `location` | Comma-separated lat/lon string | `str` | `50.4501,30.5234` | Geographic filtering |
| `observed_on` | Observation date | `str` | `2024-03-15` | Temporal metadata |
| `quality_grade` | Community verification status | `str` | `research` | Data quality filter |

### Potential Data Problems
- **Missing labels:** `is_diseased` cannot always be derived — many observations lack disease annotations, resulting in `None` values that must be dropped during Transform
- **Inconsistent coordinates:** `location` field is a raw string requiring parsing; may be absent or malformed
- **Label noise:** Annotations are community-contributed and may be inaccurate
- **Class imbalance:** Healthy plant observations significantly outnumber diseased ones in public data
- **Image quality variance:** Real field photographs vary widely in resolution, focus, and lighting

### Fields Used in Further Analysis
- `external_id` — deduplication and traceability
- `image_url` — future image download for model training
- `is_diseased` — binary classification target label
- `label` — taxonomic context
- `observation_date` — temporal filtering and drift analysis
- `latitude`, `longitude` — geographic distribution analysis

---

## 3. ETL Module Structure

```
etl/
├── config/
│   └── types.py          # TypedDict definitions for all config structures
├── sources/
│   ├── interface.py           # Abstract base class and RawObservation dataclass
│   ├── inaturalist.py    # iNaturalist API source implementation
├── data/
│   ├── raw/              # Raw JSONL files from Extract stage
│   └── processed/        # Cleaned observations in SQLite
├── logs/                 # ETL execution logs
├── config.toml           # Pipeline configuration
├── extract.py            # Extract stage orchestration
├── transform.py          # Transform stage orchestration
├── load.py               # Load stage orchestration
└── pipeline.py           # Entry point — runs full ETL
```

---

## 4. Configuration

```toml
[general]
download_images = false
log_level = "INFO"
raw_data_path = "data/raw"
processed_data_path = "data/processed"

[sources.inaturalist]
enabled = true
base_url = "https://api.inaturalist.org/v1"
taxon_id = 47126        # Plantae
term_id = 9             # Plant disease annotation
per_page = 200          # Maximum allowed by API
max_pages = 10
rate_limit_seconds = 1.0

[sources.kaggle]
enabled = false
dataset = "plantvillage/plantvillage-dataset"

[load]
format = "sqlite"
target_path = "data/processed/observations.db"
table_name = "observations"
```

---

## 5. Module Descriptions

### `config/types.py` — Configuration Type Definitions
Defines `TypedDict` structures for all configuration sections — `GeneralConfig`, `iNaturalistSourceConfig`, `KaggleSourceConfig`, `SourcesConfig`, `LoadConfig`, and `AppConfig`. Enables strict static type checking across all modules without runtime overhead.

### `sources/base.py` — Abstract Base and Data Contract
Defines `RawObservation` dataclass — the strict typed contract that every source must produce regardless of its origin. Defines `BaseSource` abstract class with two required methods: `parse_config()` and `fetch()`. Adding a new data source requires only implementing these two methods in a new file under `sources/`.

```python
@dataclass
class RawObservation:
    source: str
    external_id: str
    image_url: str | None
    label: str | None
    is_diseased: bool | None
    latitude: float | None
    longitude: float | None
    observation_date: datetime | None
    raw_json: str  # JSON-serialized original response for debugging
```

### `sources/inaturalist.py` — iNaturalist Source Implementation
Implements `BaseSource` for the iNaturalist REST API. Key responsibilities:
- `parse_config()` — validates and strictly types the raw TOML config section
- `_fetch_page()` — retrieves a single page of observations with error handling for HTTP errors, connection errors, and timeouts
- `_is_diseased()` — derives binary label from community annotations
- `_parse_observation()` — maps raw API response to `RawObservation`
- `fetch()` — generator that yields observations page by page with rate limiting

### `extract.py` — Extract Stage
Loads configuration, instantiates the enabled source, collects all observations, and saves them to a timestamped JSONL file in `data/raw/`. Each line is a self-contained JSON record. Records the `extracted_at` timestamp on every observation.

### `transform.py` — Transform Stage
Loads raw JSONL, applies a sequential transformation pipeline, and validates the result against a Pandera schema before returning a clean DataFrame.

Transformations applied:
1. Column name normalization — strips whitespace, lowercases
2. Duplicate removal — by `(source, external_id)` composite key
3. Date parsing — `observation_date` to `datetime`
4. Type casting — numeric coordinates, boolean `is_diseased`
5. Invalid coordinate filtering — out-of-range lat/lon removed
6. Missing label removal — observations without `is_diseased` dropped
7. Schema validation — Pandera enforces types, ranges, and constraints

### `load.py` — Load Stage
Connects to SQLite, initializes the schema, and inserts clean observations using `INSERT OR IGNORE` for idempotent loading. Verifies record count after insertion.

SQLite schema:
```sql
CREATE TABLE IF NOT EXISTS observations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source            TEXT    NOT NULL,
    external_id       TEXT    NOT NULL,
    image_url         TEXT,
    label             TEXT,
    is_diseased       INTEGER,
    latitude          REAL,
    longitude         REAL,
    observation_date  TEXT,
    extracted_at      TEXT    NOT NULL,
    loaded_at         TEXT    NOT NULL,
    UNIQUE (source, external_id)
)
```

### `pipeline.py` — Entry Point
Orchestrates the full ETL sequence: Extract → Transform → Load. Configures logging to both stdout and `logs/etl.log`. Accepts optional config path as a command-line argument.

```bash
python pipeline.py                    # uses config.toml
python pipeline.py config_test.toml  # uses alternate config
```

---

## 6. ETL Process Schema

```
┌─────────────────────────────────────────────────────────────┐
│                        EXTRACT                              │
│  iNaturalist API → paginated fetch → RawObservation list   │
│  → timestamped JSONL → data/raw/observations_YYYYMMDD.jsonl│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                       TRANSFORM                             │
│  Load JSONL → normalize → deduplicate → parse dates        │
│  → cast types → filter invalid → drop missing labels       │
│  → Pandera schema validation → clean DataFrame             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                         LOAD                                │
│  SQLite connection → init schema → INSERT OR IGNORE        │
│  → verify count → data/processed/observations.db           │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Raw vs Cleaned Data Examples

### Raw observation (JSONL line from `data/raw/`):
```json
{
  "source": "inaturalist",
  "external_id": "12345678",
  "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/123/medium.jpg",
  "label": "Solanum lycopersicum",
  "is_diseased": true,
  "latitude": 50.4501,
  "longitude": 30.5234,
  "observation_date": "2024-03-15T00:00:00",
  "extracted_at": "20240315_142301",
  "raw_json": "{\"id\": 12345678, \"photos\": [...], ...}"
}
```

### Cleaned observation (SQLite row from `data/processed/`):

| id | source | external_id | image_url | label | is_diseased | latitude | longitude | observation_date | extracted_at | loaded_at |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | inaturalist | 12345678 | https://... | Solanum lycopersicum | 1 | 50.4501 | 30.5234 | 2024-03-15 | 20240315_142301 | 2024-03-15T14:23:05Z |

---

## 8. Error Handling

| Error Type | Where | Handling Strategy |
|---|---|---|
| HTTP 4xx / 5xx | `_fetch_page()` | Log error, return empty list, continue to next page |
| Connection timeout | `_fetch_page()` | Log error, return empty list, continue to next page |
| Missing config key | `parse_config()` | Raise `KeyError` immediately at startup |
| Invalid config value | `parse_config()` | Raise `ValueError` immediately at startup |
| Unparseable date | `parse_observed_on()` | Log warning, return `None` |
| Invalid coordinates | `drop_invalid_coordinates()` | Log count, drop affected rows |
| Missing disease label | `drop_missing_labels()` | Log count, drop affected rows |
| Schema validation failure | `observation_schema.validate()` | Raise `SchemaError` with detailed report |
| SQLite insert failure | `load_observations()` | Log error per record, continue with remaining |
| No enabled source | `run_extract()` | Log error, exit with code 1 |

---

## 9. Dataset Suitability Assessment

### Strengths
- Real field photography conditions closely match intended deployment environment
- Research-grade quality filter removes unverified observations
- Multi-source architecture allows dataset expansion without pipeline changes
- Raw JSON preserved for every observation enabling label correction without re-fetching

### Limitations
- Binary label derivation from annotations is imprecise — a significant portion of observations will have `is_diseased = None` and be dropped
- Class imbalance between healthy and diseased observations is expected and must be addressed during model training through oversampling or weighted loss
- Dataset does not yet include downloaded images — `download_images = false` in current config; must be enabled before model training stage

### Conclusion
The dataset obtained through this ETL pipeline is suitable for the next project stage. It provides a structured, validated, and reproducible collection of plant observation metadata with binary disease labels derived from community annotations. The raw JSON layer ensures full traceability and the ability to re-derive labels without API re-fetching. Image downloading is architecturally supported and can be activated via a single configuration change when the model training stage begins.
