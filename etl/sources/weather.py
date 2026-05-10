import logging
import pandas as pd
import requests_cache
import time
from retry_requests import retry
import openmeteo_requests

logger = logging.getLogger(__name__)

# Setup Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(
    "data/raw/weather_http_cache", expire_after=-1
)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)  # pyright: ignore[reportArgumentType]


class RateLimitError(Exception):
    """Raised when the API rate limit is exceeded and we cannot recover immediately."""

    def __init__(self, reason: str, is_hourly: bool = False):
        self.reason = reason
        self.is_hourly = is_hourly
        super().__init__(self.reason)


from collections.abc import Iterator


def get_weather_bulk(
    locations: list[tuple[float, float, str]], max_retries: int = 3
) -> Iterator[tuple[tuple[float, float, str], tuple[float | None, float | None]]]:
    """
    Fetches weather data for multiple locations in batches.
    'locations' is a list of (lat, lon, date_str).
    Yields ((lat, lon, date_str), (temperature, precipitation)) as they are fetched.
    """
    if not locations:
        return

    url = "https://archive-api.open-meteo.com/v1/archive"

    # Process in chunks of 50 (Open-Meteo allows up to 50 locations per request)
    chunk_size = 50
    total_chunks = (len(locations) + chunk_size - 1) // chunk_size

    logger.info(
        f"Starting bulk weather fetch for {len(locations)} unique pairs in {total_chunks} chunks"
    )

    for i in range(0, len(locations), chunk_size):
        chunk_idx = (i // chunk_size) + 1
        chunk = locations[i : i + chunk_size]

        # Group chunk by date to minimize API calls
        date_map: dict[str, list[int]] = {}
        for idx, (_, _, date_str) in enumerate(chunk):
            date_map.setdefault(date_str, []).append(idx)

        logger.info(
            f"Processing chunk {chunk_idx}/{total_chunks} ({len(date_map)} unique dates)"
        )

        for date_str, chunk_indices in date_map.items():
            sub_lats = [chunk[idx][0] for idx in chunk_indices]
            sub_lons = [chunk[idx][1] for idx in chunk_indices]

            params = {
                "latitude": sub_lats,
                "longitude": sub_lons,
                "start_date": date_str,
                "end_date": date_str,
                "daily": ["temperature_2m_mean", "precipitation_sum"],
            }

            success = False
            for attempt in range(max_retries):
                try:
                    # Small mandatory sleep to avoid burst limit
                    time.sleep(0.5)
                    responses = openmeteo.weather_api(url, params=params)

                    for sub_idx, response in enumerate(responses):
                        daily = response.Daily()
                        temp, precip = None, None
                        if daily:
                            var0 = daily.Variables(0)
                            var1 = daily.Variables(1)
                            if var0 and var1:
                                temp_val = float(var0.ValuesAsNumpy()[0])
                                precip_val = float(var1.ValuesAsNumpy()[0])
                                temp = temp_val if not pd.isna(temp_val) else None
                                precip = precip_val if not pd.isna(precip_val) else None

                        loc = chunk[chunk_indices[sub_idx]]
                        yield loc, (temp, precip)
                    success = True
                    break  # Success
                except Exception as e:
                    err_msg = str(e).lower()
                    if "limit exceeded" in err_msg:
                        wait_time = (attempt + 1) * 20  # Increased wait
                        logger.warning(
                            f"Rate limit hit for {date_str}. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    logger.warning(
                        f"Bulk weather fetch failed for date {date_str}: {e}"
                    )
                    break

            if not success:
                # Yield None for these indices so the caller knows they failed
                for sub_idx in chunk_indices:
                    yield chunk[sub_idx], (None, None)

    logger.info("Bulk fetch complete")
