import json
import logging
from pathlib import Path
from typing import Any, cast, final, override
from collections.abc import Iterator
from datetime import datetime, timezone
import requests

from etl.config.helpers import ETL_ROOT
from etl.config.types import iNaturalistSourceConfig
from etl.sources.interface import SourceInterface, RawObservation

logger = logging.getLogger(__name__)


@final
class iNaturalistSource(SourceInterface):
    def __init__(self, config: iNaturalistSourceConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PlantDiseaseETL/1.0"})
        self.cache_dir = ETL_ROOT / "data" / "raw" / "inaturalist"

    def _get_cache_path(self, page: int, is_diseased: bool) -> Path:
        subdir = "diseased" if is_diseased else "healthy"
        path = self.cache_dir / subdir / f"page_{page}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _parse_observation(
        self, raw: dict[str, Any], is_diseased: bool
    ) -> RawObservation:
        photos = raw.get("photos", [])
        image_url = photos[0].get("url") if photos else None

        coords = raw.get("location", "")
        lat, lon = None, None
        if coords and "," in coords:
            try:
                parts = coords.split(",")
                lat, lon = float(parts[0]), float(parts[1])
            except (ValueError, IndexError):
                pass

        return RawObservation(
            source="inaturalist",
            external_id=str(raw["id"]),
            image_url=image_url,
            label=raw.get("taxon", {}).get("name"),
            is_diseased=is_diseased,
            latitude=lat,
            longitude=lon,
            observation_date=self._parse_date(raw.get("observed_on")),
            extracted_at=datetime.now(timezone.utc),
            raw_json=json.dumps(raw),
        )

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    def fetch_page(self, page: int, is_diseased: bool) -> list[RawObservation]:
        cache_path = self._get_cache_path(page, is_diseased)

        if cache_path.exists() and not self.config.refetch:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [RawObservation.from_dict(d) for d in data]

        params = {
            "taxon_id": self.config.taxon_id,
            "per_page": self.config.per_page,
            "page": page,
            "photos": "true",
            "quality_grade": "research",
        }
        if is_diseased:
            params["term_id"] = self.config.term_id
            params["term_value_id"] = self.config.term_value_id

        logger.info(
            f"Fetching {'diseased' if is_diseased else 'healthy'} page {page} from iNaturalist"
        )
        # HttpUrl from pydantic needs to be converted to string
        resp = self.session.get(f"{str(self.config.base_url)}/observations", params=params)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        observations = [self._parse_observation(r, is_diseased) for r in results]

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump([obs.to_dict() for obs in observations], f)

        return observations

    @override
    def fetch(self) -> Iterator[RawObservation]:
        # Balanced fetching: alternate between diseased and healthy pages
        for page in range(1, self.config.max_pages + 1):
            # Fetch diseased
            for obs in self.fetch_page(page, is_diseased=True):
                yield obs
            # Fetch healthy
            for obs in self.fetch_page(page, is_diseased=False):
                yield obs
