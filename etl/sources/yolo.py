import json
import logging
import re
from pathlib import Path
from typing import final, override
from collections.abc import Iterator
from datetime import datetime, timezone

from etl.config.helpers import ETL_ROOT
from etl.config.types import YoloSourceConfig
from etl.sources.interface import SourceInterface, RawObservation

logger = logging.getLogger(__name__)


@final
class YoloSource(SourceInterface):
    def __init__(self, config: YoloSourceConfig) -> None:
        self.config = config
        self.root_path = Path(config.root_path)
        if not self.root_path.is_absolute():
            self.root_path = ETL_ROOT / self.root_path

    def _parse_yaml_names(self, yaml_path: Path) -> list[str]:
        """Simple regex-based parser for data.yaml names list."""
        if not yaml_path.exists():
            return []
        
        content = yaml_path.read_text()
        # Find 'names: [...]' block
        match = re.search(r"names:\s*\[(.*?)\]", content, re.DOTALL)
        if not match:
            return []
        
        # Extract individual names (handles single or double quotes)
        names_str = match.group(1)
        names = re.findall(r"['\"](.*?)['\"]", names_str)
        return [n.strip() for n in names]

    @override
    def fetch(self) -> Iterator[RawObservation]:
        if not self.root_path.exists():
            logger.warning(f"YOLO source path does not exist: {self.root_path}")
            return

        yaml_path = self.root_path / "data.yaml"
        class_names = self._parse_yaml_names(yaml_path)
        if not class_names:
            logger.error(f"Could not parse class names from {yaml_path}")
            return

        logger.info(f"Crawling YOLO source: {self.config.name} at {self.root_path}")
        
        count = 0
        # Iterate through common YOLO splits
        for split in ["train", "valid", "test"]:
            img_dir = self.root_path / split / "images"
            label_dir = self.root_path / split / "labels"
            
            if not img_dir.exists():
                continue
                
            for img_path in img_dir.glob("*.jpg"):
                label_path = label_dir / (img_path.stem + ".txt")
                
                label_name = "Unknown"
                if label_path.exists():
                    try:
                        content = label_path.read_text().strip()
                        if content:
                            # YOLO format: class_id x_center y_center width height
                            class_id = int(content.split()[0])
                            if 0 <= class_id < len(class_names):
                                label_name = class_names[class_id]
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse label file {label_path}: {e}")

                # If we couldn't get a label from YOLO, use parent as fallback (unlikely to be better but safe)
                if label_name == "Unknown":
                    continue

                is_diseased = "healthy" not in label_name.lower()
                rel_path = str(img_path.relative_to(ETL_ROOT.parent))

                raw_data = {
                    "file_path": rel_path,
                    "provenance": self.config.provenance,
                    "yolo_split": split,
                    "class_name": label_name
                }

                yield RawObservation(
                    source=f"yolo_{self.config.name}",
                    external_id=img_path.name,
                    image_url=rel_path,
                    label=label_name,
                    is_diseased=is_diseased,
                    latitude=None,
                    longitude=None,
                    observation_date=None,
                    extracted_at=datetime.now(timezone.utc),
                    provenance=self.config.provenance,
                    raw_json=json.dumps(raw_data),
                )
                count += 1

        logger.info(f"YOLO source '{self.config.name}' completed: {count} observations extracted")
