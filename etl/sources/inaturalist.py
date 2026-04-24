import json
import logging
import time
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

        # Try to get date with hour for better solar status calculation
        obs_date = self._parse_date(raw.get("observed_on"))
        details = raw.get("observed_on_details")
        if obs_date and details and "hour" in details:
            try:
                obs_date = obs_date.replace(hour=int(details["hour"]))
            except (ValueError, TypeError):
                pass

        return RawObservation(
            source="inaturalist",
            external_id=str(raw["id"]),
            image_url=image_url,
            label=raw.get("taxon", {}).get("name"),
            is_diseased=is_diseased,
            latitude=lat,
            longitude=lon,
            observation_date=obs_date,
            extracted_at=datetime.now(timezone.utc),
            raw_json=json.dumps(raw),
            provenance="Field",
        )

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    def fetch_page(
        self, page: int, is_diseased: bool, project_id: int | None = None
    ) -> list[RawObservation]:
        # Include project_id in cache path if provided
        subdir = "diseased" if is_diseased else "healthy"
        filename = f"page_{page}.json"
        if project_id:
            filename = f"proj_{project_id}_page_{page}.json"
        cache_path = self.cache_dir / subdir / filename
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        if cache_path.exists() and not self.config.refetch:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [RawObservation.from_dict(d) for d in data]

        params: dict[str, Any] = {
            "taxon_id": self.config.taxon_id,
            "per_page": self.config.per_page,
            "page": page,
            "photos": "true",
            "quality_grade": "research",
        }

        if is_diseased and project_id:
            params["project_id"] = project_id
        elif not is_diseased:
            # For healthy, exclude observations from our disease projects
            if self.config.project_ids:
                params["not_in_project"] = ",".join(map(str, self.config.project_ids))

        msg = f"Fetching {'diseased' if is_diseased else 'healthy'} page {page}"
        if project_id:
            msg += f" (project {project_id})"
        logger.info(msg)

        # Rate limiting
        time.sleep(self.config.rate_limit_seconds)

        resp = self.session.get(
            f"{str(self.config.base_url)}/observations", params=params, timeout=30
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])

        observations = [self._parse_observation(r, is_diseased) for r in results]

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump([obs.to_dict() for obs in observations], f)

        return observations

    @override
    def fetch(self) -> Iterator[RawObservation]:
        # Balanced fetching:
        # For diseased: distribute max_pages across verified projects
        num_projects = len(self.config.project_ids)
        if num_projects > 0:
            pages_per_project = max(1, self.config.max_pages // num_projects)
            for project_id in self.config.project_ids:
                for page in range(1, pages_per_project + 1):
                    for obs in self.fetch_page(page, is_diseased=True, project_id=project_id):
                        yield obs

        # For healthy: fetch from general taxon but exclude disease projects
        for page in range(1, self.config.max_pages + 1):
            for obs in self.fetch_page(page, is_diseased=False):
                yield obs
