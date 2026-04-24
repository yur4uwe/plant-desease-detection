import json
import logging
import re
from pathlib import Path
from typing import final, override
from collections.abc import Iterator
from datetime import datetime, timezone

from etl.config.helpers import ETL_ROOT
from etl.config.types import LocalSourceConfig
from etl.sources.interface import SourceInterface, RawObservation

logger = logging.getLogger(__name__)


@final
class LocalSource(SourceInterface):
    def __init__(self, config: LocalSourceConfig) -> None:
        self.config = config
        self.root_path = Path(config.root_path)
        if not self.root_path.is_absolute():
            self.root_path = ETL_ROOT / self.root_path

        self.healthy_re = (
            re.compile(config.healthy_regex) if config.healthy_regex else None
        )
        self.diseased_re = (
            re.compile(config.diseased_regex) if config.diseased_regex else None
        )

    def _determine_is_diseased(self, path: Path) -> bool:
        path_str = str(path)

        if self.healthy_re and self.healthy_re.search(path_str):
            return False
        if self.diseased_re and self.diseased_re.search(path_str):
            return True

        return self.config.default_is_diseased

    @override
    def fetch(self) -> Iterator[RawObservation]:
        if not self.root_path.exists():
            logger.warning(f"Local source path does not exist: {self.root_path}")
            return

        logger.info(f"Crawling local source: {self.config.name} at {self.root_path}")

        count = 0
        for img_path in self.root_path.glob(self.config.include_glob):
            is_diseased = self._determine_is_diseased(img_path)

            # Use relative path for image_url to ensure portability across environments
            rel_path = str(img_path.relative_to(ETL_ROOT.parent))

            # Build raw_json for persistence
            raw_data = {
                "file_path": rel_path,
                "provenance": self.config.provenance,
                "status_extracted": is_diseased,
            }

            yield RawObservation(
                source=f"local_{self.config.name}",
                external_id=img_path.name,
                image_url=rel_path,
                label=None,
                is_diseased=is_diseased,
                latitude=None,
                longitude=None,
                observation_date=None,
                extracted_at=datetime.now(timezone.utc),
                raw_json=json.dumps(raw_data),
            )
            count += 1

        logger.info(
            f"Local source '{self.config.name}' completed: {count} observations found"
        )
