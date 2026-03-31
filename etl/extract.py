import json
import logging
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from config.types import AppConfig
from sources.interface import RawObservation
from sources.inaturalist import iNaturalistSource

logger = logging.getLogger(__name__)


def load_config(path: str = "config.toml") -> AppConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return cast(AppConfig, cast(object, raw))


def get_source(config: AppConfig) -> iNaturalistSource | None:
    sources = config.get("sources", {})
    if sources.get("inaturalist", {}).get("enabled", False):
        return iNaturalistSource(sources["inaturalist"])
    return None


def save_raw(observations: list[RawObservation], raw_path: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = Path(raw_path)
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


def run_extract(config_path: str = "config.toml") -> Path | None:
    config = load_config(config_path)
    raw_path = config["general"]["raw_data_path"]

    source = get_source(config)
    if source is None:
        logger.warning("No enabled sources found in config")
        return None

    observations: list[RawObservation] = list(source.fetch())
    logger.info(f"Extracted {len(observations)} observations total")

    return save_raw(observations, raw_path)
