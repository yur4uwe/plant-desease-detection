import logging
import sys
from pathlib import Path
from etl.config.helpers import PROJECT_ROOT


def setup_logging(log_level: str) -> None:
    log_dir = Path(PROJECT_ROOT) / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "etl.log", encoding="utf-8"),
        ],
    )
