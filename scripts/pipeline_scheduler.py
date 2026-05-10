import logging
import time
import sys
import argparse
from etl.pipeline import run_pipeline
from utils.logging.setup import setup_logging

logger = logging.getLogger("scheduler")


def main():
    parser = argparse.ArgumentParser(description="ETL Pipeline Scheduler")
    parser.add_argument(
        "--interval", type=int, default=60, help="Interval between runs in minutes"
    )
    parser.add_argument(
        "--config", type=str, default="etl/config.toml", help="Path to config file"
    )
    args = parser.parse_args()

    setup_logging("INFO")

    logger.info("=" * 50)
    logger.info(f"Starting ETL Scheduler (Interval: {args.interval} minutes)")
    logger.info("=" * 50)

    try:
        while True:
            logger.info(
                f"Triggering scheduled run at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            try:
                run_pipeline(args.config)
            except SystemExit as e:
                if e.code != 0:
                    logger.error(f"Pipeline exited with error code {e.code}")
            except Exception as e:
                logger.exception(f"Unexpected error during scheduled run: {e}")

            logger.info(f"Scheduled run complete. Waiting {args.interval} minutes...")
            time.sleep(args.interval * 60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.exception(f"Scheduler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
