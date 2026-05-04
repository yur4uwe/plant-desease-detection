import logging
import sys

from etl.config.types import AppConfig
from etl.extract import load_config, run_extract
from etl.transform import run_transform
from etl.load import run_load
from etl.quality import calculate_quality_score
from logging.setup import setup_logging

logger = logging.getLogger(__name__)

# ─── Orchestration ───────────────────────────────────────────────


def run_pipeline(config_path: str = "etl/config.toml") -> None:

    config: AppConfig = load_config(config_path)
    setup_logging(config.general.log_level)

    logger.info("=" * 50)
    logger.info("Starting ETL pipeline")
    logger.info("=" * 50)

    # Extract
    logger.info("[ EXTRACT ] Starting data extraction")
    observations = run_extract(config)
    if not observations:
        logger.error("Extract failed — no data source enabled or no observations found")
        sys.exit(1)
    logger.info(f"[ EXTRACT ] Complete — fetched {len(observations)} observations")

    # Transform
    logger.info("[ TRANSFORM ] Starting data transformation")
    df = run_transform(observations)
    logger.info(f"[ TRANSFORM ] Complete — {len(df)} clean observations")

    # Quality Assessment
    calculate_quality_score(df)

    # Load
    logger.info("[ LOAD ] Starting data load")
    run_load(df, config)
    logger.info("[ LOAD ] Complete")

    logger.info("=" * 50)
    logger.info("ETL pipeline finished successfully")
    logger.info("=" * 50)


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "etl/config.toml"
    run_pipeline(config_path)
