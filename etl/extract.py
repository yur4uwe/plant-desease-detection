import json
import logging
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from etl.config.helpers import ETL_ROOT
from etl.config.types import AppConfig
from etl.sources.interface import RawObservation
from etl.sources.inaturalist import iNaturalistResponse, iNaturalistSource

logger = logging.getLogger(__name__)


def load_config(path: str = "config.toml") -> AppConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return cast(AppConfig, cast(object, raw))


def get_source(config: AppConfig) -> iNaturalistSource | None:
    sources = config.get("sources", {})
    if sources.get("inaturalist", {}).get("enabled", False):
        return iNaturalistSource(config=sources["inaturalist"])
    return None


def save_raw(observations: list[RawObservation], raw_path: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = Path(ETL_ROOT, raw_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"observations_{timestamp}.jsonl"

    with open(output_file, "w", encoding="utf-8") as f:
        for obs in observations:
            record = {
                "source": obs.source,
                "external_id": obs.external_id,
                "image_url": obs.image_url,
                "label": obs.label,
                "is_diseased": obs.is_diseased,
                "latitude": obs.latitude,
                "longitude": obs.longitude,
                "observation_date": obs.observation_date.isoformat()
                if obs.observation_date
                else None,
                "raw_json": obs.raw_json,
                "extracted_at": timestamp,
            }
            _ = f.write(json.dumps(record) + "\n")

    logger.info(f"Saved {len(observations)} observations to {output_file}")
    return output_file


def _save_page_cache(page: int, data: list[RawObservation], cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"page_{page}.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump([obs.to_dict() for obs in data], f)
    return cache_path


def run_extract(config_path: str = "config.toml") -> list[Path]:
    config = load_config(config_path)
    source = get_source(config)
    if source is None:
        logger.error("No enabled sources found in config")
        sys.exit(1)

    cache_dir = ETL_ROOT / "data" / "raw" / "inaturalist"
    cached_files: list[Path] = []

    for page in range(1, source.config["max_pages"] + 1):
        cache_path = cache_dir / f"page_{page}.json"

        if cache_path.exists() and not source.config["refetch"]:
            logger.info(f"Page {page} already cached — skipping")
            cached_files.append(cache_path)
            continue

        data = source.fetch_page(page)
        if not data or len(data) == 0:
            logger.info(f"No results on page {page} — stopping early")
            break

        saved = _save_page_cache(page, data, cache_dir)
        cached_files.append(saved)
        logger.info(f"Cached page {page} — {len(data)} observations")

    logger.info(f"Extract complete — {len(cached_files)} pages cached")
    return cached_files
