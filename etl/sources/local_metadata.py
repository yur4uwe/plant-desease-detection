import json
import logging
import re
from typing import Any, final, override
import pandas as pd
from pathlib import Path
from collections.abc import Iterator
from datetime import datetime, timezone

from etl.config.helpers import ETL_ROOT
from etl.config.types import LocalMetadataSourceConfig
from etl.sources.interface import SourceInterface, RawObservation

logger = logging.getLogger(__name__)


@final
class LocalMetadataSource(SourceInterface):
    def __init__(self, config: LocalMetadataSourceConfig) -> None:
        self.config = config
        self.metadata_path = Path(config.metadata_path)
        if not self.metadata_path.is_absolute():
            self.metadata_path = ETL_ROOT / self.metadata_path
            
        self.images_root = Path(config.images_root)
        if not self.images_root.is_absolute():
            self.images_root = ETL_ROOT / self.images_root
            
        self.healthy_re = re.compile(config.healthy_regex) if config.healthy_regex else None

    def _determine_is_diseased(self, status_val: Any) -> bool:
        if not status_val:
            return self.config.default_is_diseased
            
        status_str = str(status_val)
        if self.healthy_re and self.healthy_re.search(status_str):
            return False
            
        return self.config.default_is_diseased

    @override
    def fetch(self) -> Iterator[RawObservation]:
        if not self.metadata_path.exists():
            logger.warning(f"Metadata file not found: {self.metadata_path}")
            return

        logger.info(f"Loading metadata from {self.metadata_path}")
        
        # Load the CSV
        df = pd.read_csv(self.metadata_path)
        
        mapping = self.config.column_mapping
        id_col = mapping.get("external_id", "id")
        img_col = mapping.get("image_path", "image")
        status_col = mapping.get("status", "disease")
        label_col = mapping.get("label", status_col)

        count = 0
        for _, row in df.iterrows():
            img_filename = str(row[img_col])
            full_img_path = self.images_root / img_filename
            
            # Use relative path from project root for image_url
            rel_path = str(full_img_path.relative_to(ETL_ROOT.parent))
            
            is_diseased = self._determine_is_diseased(row[status_col])
            
            # Preserve original label in raw_json
            raw_data = {
                "original_row": row.to_dict(),
                "provenance": self.config.provenance,
                "mapped_label": str(row[label_col])
            }

            yield RawObservation(
                source=f"meta_{self.config.name}",
                external_id=str(row[id_col]),
                image_url=rel_path,
                label=str(row[label_col]),
                is_diseased=is_diseased,
                latitude=None,
                longitude=None,
                observation_date=None,
                extracted_at=datetime.now(timezone.utc),
                raw_json=json.dumps(raw_data),
            )
            count += 1
            
        logger.info(f"Metadata source '{self.config.name}' completed: {count} observations mapped")
