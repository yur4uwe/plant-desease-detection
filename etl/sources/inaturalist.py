from http import HTTPStatus
import json
import logging
from pathlib import Path
import sqlite3
import time
from typing import Any, final, override
from collections.abc import Iterator
from datetime import datetime, timezone
import requests

from etl.config.helpers import PROJECT_ROOT
from etl.config.types import iNaturalistSourceConfig
from etl.sources.interface import SourceInterface, RawObservation

logger = logging.getLogger(__name__)


@final
class iNaturalistSource(SourceInterface):
    def __init__(self, config: iNaturalistSourceConfig) -> None:
        self.config = config
        self.name = config.name
        self.session = requests.Session()
        # iNaturalist API guidelines recommend including contact info in User-Agent
        self.session.headers.update(
            {
                "User-Agent": "PlantDiseaseETL/1.0 (University Research Project; contact: YURII.TSAR@lnu.edu.ua)"
            }
        )
        self.cache_dir = PROJECT_ROOT / "data" / "raw" / "inaturalist"
        self.seen_ids: set[str] = self._load_seen_ids()

    def _load_seen_ids(self) -> set[str]:
        """Loads all existing iNaturalist external_ids from the database."""
        db_path = PROJECT_ROOT / "data" / "processed" / "observations.db"
        if not db_path.exists():
            return set()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT external_id FROM observations WHERE source = 'inaturalist'")
                return {str(row[0]) for row in cursor.fetchall()}
        except Exception as e:
            logger.warning(f"Could not load seen_ids from DB: {e}")
            return set()

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

    # Cache path is guaranteed to exist
    def _return_cached(self, cache_path: Path) -> tuple[list[RawObservation], int]:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            observations = [RawObservation.from_dict(d) for d in data]
            max_id = max((int(obs.external_id) for obs in observations), default=0)
            return observations, max_id

    def _try_request(self, params: dict[str, Any], id_below: int | None):
        # Rate limiting
        time.sleep(self.config.rate_limit_seconds)

        max_retries = 3
        attempt = 0
        while attempt < max_retries:
            try:
                resp = self.session.get(
                    f"{str(self.config.base_url)}/observations",
                    params=params,
                    timeout=30,
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                wait_time = (attempt + 1) * 30
                logger.warning(
                    f"Network issue on batch below {id_below} (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait_time}s..."
                )
                time.sleep(wait_time)
                attempt += 1
                continue

            if resp.status_code == HTTPStatus.OK:
                return resp.json().get("results", []), id_below
            elif resp.status_code == HTTPStatus.FORBIDDEN:
                logger.warning(
                    f"Reached iNaturalist API result limit (403) on batch below {id_below}. "
                    "Stopping this fetch."
                )
                return [], id_below
            elif resp.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                wait_time = (attempt + 1) * 30
                logger.warning(
                    f"Rate limit hit on batch below {id_below}. Waiting {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                wait_time = (attempt + 1) * 10
                logger.warning(
                    f"Unexpected status {resp.status_code} on batch below {id_below}. "
                    f"Waiting {wait_time}s..."
                )
                time.sleep(wait_time)

            attempt += 1
        else:
            logger.error(
                f"Failed to fetch batch below {id_below} after {max_retries} attempts"
            )
            return [], id_below

    def fetch_batch(
        self, id_below: int | None, is_diseased: bool, project_id: int | None = None, q: str | None = None
    ) -> tuple[list[RawObservation], int]:
        # Include project_id or q in cache path if provided
        subdir = "diseased" if is_diseased else "healthy"
        cursor_str = f"below_{id_below}" if id_below else "newest"
        
        if project_id:
            filename = f"proj_{project_id}_{cursor_str}.json"
        elif q:
            filename = f"query_{q}_{cursor_str}.json"
        else:
            filename = f"batch_{cursor_str}.json"
            
        cache_path = self.cache_dir / subdir / filename
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.config.refetch and cache_path.exists():
            return self._return_cached(cache_path)

        params: dict[str, Any] = {
            "taxon_id": self.config.taxon_id,
            "per_page": self.config.per_page,
            "order_by": "id",
            "order": "desc",
            "photos": "true",
            "quality_grade": "research,needs_id",
        }
        if id_below:
            params["id_below"] = id_below
        if q:
            params["q"] = q

        if is_diseased and project_id:
            params["project_id"] = project_id
        elif not is_diseased:
            # For healthy, exclude observations from our disease projects
            if self.config.project_ids:
                params["not_in_project"] = ",".join(map(str, self.config.project_ids))

        msg = f"Fetching {'diseased' if is_diseased else 'healthy'} batch {cursor_str}"
        if project_id:
            msg += f" (project {project_id})"
        elif q:
            msg += f" (query '{q}')"
        logger.info(msg)

        results, _ = self._try_request(params, id_below if id_below else 0)

        observations = []
        lowest_id = id_below if id_below else float('inf')
        for r in results:
            obs = self._parse_observation(r, is_diseased)
            observations.append(obs)
            obs_id = int(obs.external_id)
            if obs_id < lowest_id:
                lowest_id = obs_id

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump([obs.to_dict() for obs in observations], f)

        logger.debug(
            f"Wrote {len(observations)} observations to {cache_path}, with lowest id: {lowest_id}"
        )

        return observations, int(lowest_id) if lowest_id != float('inf') else 0

    def _get_last_id(self, is_diseased: bool, project_id: int | None = None) -> int:
        """Retrieves the highest ID actually stored for this project from cache or DB."""
        subdir = "diseased" if is_diseased else "healthy"
        folder = self.cache_dir / subdir

        max_id = 0
        if folder.exists():
            pattern = f"proj_{project_id}_since_*.json" if project_id else "batch_since_*.json"
            for p in folder.glob(pattern):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data:
                            # Find the real max ID inside the file
                            file_max = max((int(obs["external_id"]) for obs in data), default=0)
                            if file_max > max_id:
                                max_id = file_max
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

        if max_id > 0:
            logger.debug(f"Found max_id {max_id} for {'project '+str(project_id) if project_id else 'healthy'} in cache")

        return max_id
    def _fetch_until_target(
        self, target: int, is_diseased: bool, project_id: int | None = None, q: str | None = None
    ) -> Iterator[RawObservation]:
        yielded = 0
        current_id_below = None # Start from newest

        target_desc = f"project {project_id}" if project_id else (f"query '{q}'" if q else "healthy")
        logger.info(f"Target: {target} for {target_desc}. Starting from newest.")

        while yielded < target:
            observations, next_id_below = self.fetch_batch(
                current_id_below, is_diseased, project_id, q
            )

            if not observations:
                logger.debug(f"No observations returned in batch below {current_id_below}. Terminating loop.")
                break

            batch_yielded = 0
            for obs in observations:
                if obs.external_id in self.seen_ids:
                    continue

                self.seen_ids.add(obs.external_id)
                yield obs
                yielded += 1
                batch_yielded += 1
                if yielded >= target:
                    break
            
            logger.info(f"Batch below {current_id_below} yielded {batch_yielded}/{len(observations)} new observations. Total: {yielded}/{target}")

            if current_id_below and next_id_below >= current_id_below:
                logger.debug(f"next_id ({next_id_below}) not progressing below current_id ({current_id_below}). Terminating loop.")
                break
            current_id_below = next_id_below


    # I left this here for reference, it won't be used as its simply function call for the sake of fucntion call
    # def _fetch_healthy(self, target: int) -> Iterator[RawObservation]:
    #     return self._fetch_until_target(target, is_diseased=False)

    def _fetch_diseased(self, target: int) -> Iterator[RawObservation]:
        num_projects = len(self.config.project_ids)
        
        # 1. First, fetch from specific projects (High quality/Verified)
        project_target = target // (num_projects + 1) if num_projects > 0 else 0
        
        for project_id in self.config.project_ids:
            yield from self._fetch_until_target(project_target, True, project_id=project_id)

        # 2. Then, fill the remainder with a global keyword search
        yield from self._fetch_until_target(target, True, q="disease")

    @override
    def fetch(self) -> Iterator[RawObservation]:
        diseased_target = self.config.target_count
        healthy_target = self.config.target_count
        if self.config.fetch_mode == "all":
            diseased_target //= 2
            healthy_target = healthy_target - diseased_target

        if self.config.fetch_mode in ("all", "diseased"):
            logger.info(
                f"Fetching {diseased_target} diseased observations from iNaturalist"
            )
            yield from self._fetch_diseased(target=diseased_target)
        if self.config.fetch_mode in ("all", "healthy"):
            logger.info(
                f"Fetching {healthy_target} healthy observations from iNaturalist"
            )
            yield from self._fetch_until_target(healthy_target, False)
