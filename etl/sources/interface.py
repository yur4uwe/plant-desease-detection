from abc import ABC, abstractmethod
from typing import Any
from _collections_abc import Iterator
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawObservation:
    source: str
    external_id: str
    image_url: str | None
    label: str | None
    is_diseased: bool
    latitude: float | None
    longitude: float | None
    observation_date: datetime | None
    raw_json: str  # json.dumps(cast(dict[str, Any], raw))


class SourceInterface(ABC):
    @abstractmethod
    def fetch(self) -> Iterator[RawObservation]:
        """Fetches raw observations from the source"""
        pass

    @abstractmethod
    def parse_conf(self, conf: dict[str, Any]) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
        """Validates configuration setup"""
        pass
