import logging
import sys
import tomllib

from etl.config.types import AppConfig
from etl.sources.interface import RawObservation, SourceInterface
from etl.sources.inaturalist import iNaturalistSource
from etl.sources.local import LocalSource
from etl.sources.local_metadata import LocalMetadataSource

logger = logging.getLogger(__name__)


def load_config(path: str = "etl/config.toml") -> AppConfig:
    try:
        with open(path, "rb") as f:
            raw_data = tomllib.load(f)
        return AppConfig.model_validate(raw_data)
    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load or validate config: {e}")
        sys.exit(1)


def get_enabled_sources(config: AppConfig) -> list[SourceInterface]:
    enabled: list[SourceInterface] = []
    if config.sources.inaturalist.enabled:
        enabled.append(iNaturalistSource(config=config.sources.inaturalist))

    for local_cfg in config.sources.local_sources:
        if local_cfg.enabled:
            enabled.append(LocalSource(config=local_cfg))

    for meta_cfg in config.sources.metadata_sources:
        if meta_cfg.enabled:
            enabled.append(LocalMetadataSource(config=meta_cfg))
    return enabled


def run_extract(config: AppConfig) -> list[RawObservation]:
    sources = get_enabled_sources(config)

    if not sources:
        logger.error("No enabled sources found in config")
        sys.exit(1)

    all_observations: list[RawObservation] = []
    for source in sources:
        logger.info(f"Extracting data from {source.__class__.__name__}")
        observations = list(source.fetch())
        all_observations.extend(observations)

    logger.info(
        f"Extract complete — {len(all_observations)} total observations fetched"
    )
    return all_observations
