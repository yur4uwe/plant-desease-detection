import json
import logging
import os
import sys
import argparse

from etl.config.types import AppConfig
from etl.extract import load_config, run_extract
from etl.transform import run_transform
from etl.load import run_load
from etl.quality import calculate_quality_score
from etl.utils.metrics import MetricsCollector
from etl.utils.checkpoints import CheckpointManager
from utils.logging.setup import setup_logging

logger = logging.getLogger(__name__)


def get_completed_stages(metrics_file: str) -> set[str]:
    if not os.path.exists(metrics_file):
        return set()

    completed = set()
    try:
        with open(metrics_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("event") == "stage_complete":
                        completed.add(data["stage"])
                    if data.get("status") == "success":
                        completed = set()  # Start fresh if last run was successful
                except (json.JSONDecodeError, KeyError):
                    continue
    except Exception:
        pass
    return completed


def run_pipeline(config_path: str = "etl/config.toml", resume: bool = False) -> None:
    config: AppConfig = load_config(config_path)
    setup_logging(config.general.log_level)

    # Resume overrides
    if resume:
        logger.info("Resume flag detected. Overriding refetch for iNaturalist.")
        config.sources.inaturalist.refetch = False

    metrics_file = "logs/pipeline_metrics.jsonl"
    completed_stages = get_completed_stages(metrics_file) if resume else set()

    checkpoints = CheckpointManager()
    if not resume:
        checkpoints.clear()

    metrics = MetricsCollector(metrics_file)
    metrics.start_pipeline()

    logger.info("=" * 50)
    logger.info(f"Starting ETL pipeline (Resume: {resume})")
    logger.info("=" * 50)

    observations = []
    source_names = []
    df = None
    quality_results = None
    inserted_count = 0

    try:
        # 1. Extract
        if "extract" in completed_stages:
            logger.info("[ EXTRACT ] Resuming from checkpoint...")
            observations, source_names = checkpoints.load_observations()
            if not observations:
                logger.warning(
                    "[ EXTRACT ] Checkpoint file missing or empty. Re-running."
                )
                completed_stages.discard("extract")

        if "extract" not in completed_stages:
            logger.info("[ EXTRACT ] Starting data extraction")
            with metrics.stage("extract") as s:
                observations, source_names = run_extract(config)
                if not observations:
                    logger.error(
                        "Extract failed — no data source enabled or no observations found"
                    )
                    metrics.finish_pipeline(
                        status="failed", error="No observations found"
                    )
                    sys.exit(1)
                s.set_metrics(count=len(observations))
                checkpoints.save_observations(observations, source_names)
            logger.info(
                f"[ EXTRACT ] Complete — fetched {len(observations)} observations"
            )

        # 2. Transform
        if "transform" in completed_stages:
            logger.info("[ TRANSFORM ] Resuming from checkpoint...")
            df = checkpoints.load_dataframe()
            if df is None:
                logger.warning("[ TRANSFORM ] Checkpoint file missing. Re-running.")
                completed_stages.discard("transform")

        if "transform" not in completed_stages:
            logger.info("[ TRANSFORM ] Starting data transformation")
            with metrics.stage("transform") as s:
                df = run_transform(observations)
                s.set_metrics(count=len(df))
                checkpoints.save_dataframe(df)
            logger.info(f"[ TRANSFORM ] Complete — {len(df)} clean observations")

        # 3. Quality Assessment
        if "quality" in completed_stages:
            logger.info("[ QUALITY ] Resuming from checkpoint...")
            quality_results = checkpoints.load_quality()
            if quality_results is None:
                logger.warning("[ QUALITY ] Checkpoint missing. Re-running.")
                completed_stages.discard("quality")

        if "quality" not in completed_stages and df is not None:
            with metrics.stage("quality"):
                quality_results = calculate_quality_score(df)
                metrics.log_quality(quality_results)
                checkpoints.save_quality(quality_results)
        elif df is None:
            logger.warning("[ QUALITY ] No data to calculate quality. Skipping.")

        # 4. Load
        if "load" in completed_stages:
            logger.info("[ LOAD ] Skipping (already completed)")
        elif df is None:
            logger.warning("[ LOAD ] No data to load. Skipping.")
        else:
            logger.info("[ LOAD ] Starting data load")
            with metrics.stage("load") as s:
                inserted_count = run_load(df, config)
                s.set_metrics(count=inserted_count)
            logger.info(f"[ LOAD ] Complete — {inserted_count} rows updated/inserted")

        # Finalize Metrics
        metrics.log_counts(
            extracted=len(observations),
            transformed=len(df) if df is not None else 0,
            loaded=inserted_count,
            sources=source_names,
        )

        metrics.log_storage(
            db_path=config.load.target_path,
            raw_dir=config.general.raw_data_path,
            processed_dir=config.general.processed_data_path,
        )

        metrics.finish_pipeline()
        checkpoints.clear()  # Successfully finished, clear checkpoints

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        metrics.finish_pipeline(status="error", error=str(e))
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("ETL pipeline finished successfully")
    logger.info("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", nargs="?", default="etl/config.toml")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    run_pipeline(args.config, resume=args.resume)
