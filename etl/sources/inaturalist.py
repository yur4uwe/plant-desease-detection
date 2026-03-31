import json
from pathlib import Path
import logging
from typing import Any, cast, final, override, TypedDict
import requests
from _collections_abc import Iterator
from etl.config.helpers import ETL_ROOT
from etl.config.types import iNaturalistSourceConfig
from etl.sources.interface import SourceInterface, RawObservation
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_observed_on(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"Could not parse date: {value}")
        return None


class iNaturalistConfig(TypedDict):
    refetch: bool
    base_url: str
    taxon_id: int
    term_id: int
    per_page: int
    max_pages: int
    rate_limit_seconds: float


class iNaturalistAnnotationValue(TypedDict):
    label: str


class iNaturalistAnnotation(TypedDict):
    controlled_attribute_id: int
    controlled_value: iNaturalistAnnotationValue


class iNaturalistPhoto(TypedDict):
    url: str


class iNaturalistTaxon(TypedDict):
    name: str


class iNaturalistObservation(TypedDict):
    id: int
    photos: list[iNaturalistPhoto]
    annotations: list[iNaturalistAnnotation]
    taxon: iNaturalistTaxon
    location: str
    observed_on: str


class iNaturalistResponse(TypedDict):
    results: list[iNaturalistObservation]


@final
class iNaturalistSource(SourceInterface):
    def __init__(self, config: iNaturalistSourceConfig) -> None:
        self.config = self.parse_conf(cast(dict[str, Any], cast(object, config)))  # pyright: ignore[reportExplicitAny]
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PlantDiseaseETL/1.0"})

    @override
    def parse_conf(self, conf: dict[str, Any]) -> iNaturalistConfig:  # pyright: ignore[reportExplicitAny]
        per_page = int(conf["per_page"])  # pyright: ignore[reportAny]
        if per_page > 200:
            raise ValueError(f"per_page cannot exceed 200, got {per_page}")

        return iNaturalistConfig(
            refetch=bool(conf["refetch"]),  # pyright: ignore[reportAny]
            base_url=str(conf["base_url"]),  # pyright: ignore[reportAny]
            taxon_id=int(conf["taxon_id"]),  # pyright: ignore[reportAny]
            term_id=int(conf["term_id"]),  # pyright: ignore[reportAny]
            per_page=per_page,
            max_pages=int(conf["max_pages"]),  # pyright: ignore[reportAny]
            rate_limit_seconds=float(conf["rate_limit_seconds"]),  # pyright: ignore[reportAny]
        )

    def _is_diseased(self, observation: iNaturalistObservation) -> bool | None:
        annotations = observation.get("annotations", [])
        for annotation in annotations:
            value = annotation.get("controlled_value", {})
            label = value.get("label", "").lower()
            if "disease" in label or "dead" in label:
                return True
            if "healthy" in label or "alive" in label:
                return False
        return None

    def _get_cache_path(self, page: int) -> Path:
        cache_dir = ETL_ROOT / "data" / "raw" / "inaturalist"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"page_{page}.json"

    def _parse_observation(self, raw: iNaturalistObservation) -> RawObservation:
        photos = raw.get("photos", [])
        image_url: str | None = photos[0]["url"] if photos else None

        coords = raw.get("location", "")
        latitude: float | None = None
        longitude: float | None = None
        if coords and "," in coords:
            try:
                lat, lon = coords.split(",")
                latitude = float(lat.strip())
                longitude = float(lon.strip())
            except ValueError:
                pass

        is_diseased = self._is_diseased(raw)
        return RawObservation(
            source="inaturalist",
            external_id=str(raw["id"]),
            image_url=image_url,
            label=raw.get("taxon", {}).get("name"),
            is_diseased=is_diseased if is_diseased is not None else False,
            latitude=latitude,
            longitude=longitude,
            observation_date=parse_observed_on(raw.get("observed_on")),
            extracted_at=datetime.now(),
            raw_json=json.dumps(cast(dict[str, Any], cast(object, raw))),  # pyright: ignore[reportExplicitAny]
        )

    def fetch_page(self, page: int) -> list[RawObservation] | None:
        cache_path = self._get_cache_path(page)

        if cache_path.exists() and not self.config["refetch"]:
            logger.info(f"Loading page {page} from cache")
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data: list[RawObservation] = json.load(f)
            return cached_data

        logger.info(f"Fetching page {page} from API")
        try:
            response = self.session.get(
                f"{self.config['base_url']}/observations",
                params={
                    "taxon_id": self.config["taxon_id"],
                    "per_page": self.config["per_page"],
                    "page": page,
                    "photos": "true",
                    "quality_grade": "research",
                    "term_id": self.config["term_id"],
                },
                timeout=30,
            )
            response.raise_for_status()
            data: iNaturalistResponse = response.json()

            observations: list[RawObservation] = []
            for raw in data["results"]:
                observations.append(self._parse_observation(raw))

            return observations
        except requests.HTTPError as e:
            logger.error(f"HTTP error on page {page}: {e}")
            return None
        except requests.ConnectionError as e:
            logger.error(f"Connection error on page {page}: {e}")
            return None
        except requests.Timeout:
            logger.error(f"Timeout on page {page}")
            return None

    @override
    def fetch(self) -> Iterator[RawObservation]:
        cache_dir = ETL_ROOT / "data" / "raw" / "inaturalist"

        if not cache_dir.exists():
            logger.warning("Cache directory does not exist — run extract first")
            return

        for cache_file in sorted(cache_dir.glob("page_*.json")):
            with open(cache_file, "r", encoding="utf-8") as f:
                data: list[RawObservation] = json.load(f)
            for raw in data:
                yield raw
