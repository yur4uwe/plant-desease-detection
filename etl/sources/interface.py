from abc import ABC, abstractmethod
from typing import Any
from collections.abc import Iterator
from dataclasses import asdict, dataclass
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
    extracted_at: datetime | None
    raw_json: str
    provenance: str = "Unknown"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["observation_date"] = (
            self.observation_date.isoformat()
            if self.observation_date is not None
            else None
        )
        d["extracted_at"] = (
            self.extracted_at.isoformat() if self.extracted_at is not None else None
        )
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RawObservation":
        return cls(
            source=d["source"],
            external_id=d["external_id"],
            image_url=d["image_url"],
            label=d["label"],
            is_diseased=bool(d["is_diseased"]),
            latitude=d.get("latitude"),
            longitude=d.get("longitude"),
            observation_date=(
                datetime.fromisoformat(d["observation_date"])
                if d.get("observation_date") is not None
                else None
            ),
            extracted_at=(
                datetime.fromisoformat(d["extracted_at"])
                if d.get("extracted_at") is not None
                else None
            ),
            raw_json=d["raw_json"],
            provenance=d.get("provenance", "Unknown"),
        )


class SourceInterface(ABC):
    @abstractmethod
    def fetch(self) -> Iterator[RawObservation]:
        """Fetches raw observations from the source, handling its own caching and balance."""
        pass
