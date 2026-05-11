import logging
import sys
import argparse
from typing import Any, Callable, Optional

from etl.config.types import AppConfig
from etl.extract import load_config, run_extract
from etl.transform import run_transform
from etl.load import run_load
from etl.quality import calculate_quality_score
from etl.utils.checkpoints import CheckpointManager
from etl.utils.telemetry import TelemetryManager
from utils.logging.setup import setup_logging

logger = logging.getLogger(__name__)


def execute_stage(
    name: str,
    action: Callable[..., Any],
    load_checkpoint: Callable[[], Any],
    save_checkpoint: Callable[[Any], None],
    telemetry: TelemetryManager,
    get_count: Optional[Callable[[Any], int]] = None,
    input_data: Any = None,
) -> Any:
    """Encapsulates the resume/execute/save logic for a single ETL stage."""
    with telemetry.stage(name) as s:
        data = None
        if s.is_resume:
            logger.info(f"[ {name.upper()} ] Resuming from checkpoint...")
            data = load_checkpoint()

        if not s.is_resume or data is None:
            logger.info(f"[ {name.upper()} ] Starting stage...")
            data = action(input_data) if input_data is not None else action()
            if data is None:
                return None
            save_checkpoint(data)

        # Handle special cases for telemetry metrics
        if get_count and data is not None:
            s.set_metrics(count=get_count(data))

        # Re-log quality if it was loaded from checkpoint
        if name == "quality" and data is not None:
            telemetry.log_quality(data)

        return data


def run_pipeline(config_path: str = "etl/config.toml", resume: bool = False) -> None:
    config: AppConfig = load_config(config_path)
    setup_logging(config.general.log_level)

    telemetry = TelemetryManager()
    telemetry.start_pipeline(resume=resume)

    # Resume overrides
    if resume:
        logger.info("Resume flag detected. Overriding refetch for iNaturalist.")
        config.sources.inaturalist.refetch = False

    checkpoints = CheckpointManager()
    if not resume:
        checkpoints.clear()

    logger.info("=" * 50)
    logger.info(
        f"Starting ETL pipeline (Resume: {resume}) (Refetch: {config.sources.inaturalist.refetch})"
    )
    logger.info("=" * 50)

    try:
        # 1. Extract
        extract_result = execute_stage(
            name="extract",
            action=lambda: run_extract(config),
            load_checkpoint=checkpoints.load_observations,
            save_checkpoint=lambda d: checkpoints.save_observations(d[0], d[1]),
            telemetry=telemetry,
            get_count=lambda d: len(d[0]),
        )
        if not extract_result:
            raise RuntimeError("Extraction failed to produce data")
        observations, _ = extract_result

        # 2. Transform
        df = execute_stage(
            name="transform",
            action=run_transform,
            load_checkpoint=checkpoints.load_dataframe,
            save_checkpoint=checkpoints.save_dataframe,
            telemetry=telemetry,
            get_count=len,
            input_data=observations,
        )

        # 3. Quality
        quality_results = execute_stage(
            name="quality",
            action=calculate_quality_score,
            load_checkpoint=checkpoints.load_quality,
            save_checkpoint=checkpoints.save_quality,
            telemetry=telemetry,
            get_count=lambda d: d.get("raw_counts", {}).get("total_rows", 0),
            input_data=df,
        )
        if quality_results:
            logger.info(
                f"[ QUALITY ] Integral Score: {quality_results['integral_score']}"
            )

        # 4. Load
        # Load is slightly different as it doesn't have a file checkpoint (it's the DB itself)
        with telemetry.stage("load") as s:
            if s.is_resume:
                logger.info("[ LOAD ] Already completed. Skipping.")
                # When resuming, we consider 0 new rows added in this run
                s.set_metrics(count=0)
            elif df is not None:
                logger.info("[ LOAD ] Starting data load")
                stats = run_load(df, config)
                # We log 'new' rows to telemetry count to reflect actual dataset growth
                s.set_metrics(count=stats["new"])
                logger.info(
                    f"[ LOAD ] Complete — {stats['new']} new rows, {stats['updated']} updated"
                )
            else:
                logger.warning("[ LOAD ] No data to load. Skipping.")

        telemetry.finish_pipeline(status="success")
        checkpoints.clear()

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        telemetry.finish_pipeline(status="error", error=str(e))
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
