import logging
import pandas as pd
import requests_cache
import time
from retry_requests import retry
import openmeteo_requests

logger = logging.getLogger(__name__)

# Setup Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(".weather_cache", expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)  # pyright: ignore[reportArgumentType]


class RateLimitError(Exception):
    """Raised when the API rate limit is exceeded and we cannot recover immediately."""

    def __init__(self, reason: str, is_hourly: bool = False):
        self.reason = reason
        self.is_hourly = is_hourly
        super().__init__(self.reason)


def get_weather_for_location(
    lat: float, lon: float, date_str: str, max_retries: int = 3
) -> tuple[float | None, float | None]:
    """
    Fetches daily mean temperature and total precipitation for a specific coordinate and date.
    Returns (temperature_2m_mean, precipitation_sum).
    Handles API rate limits with internal retries for recoverable errors.
    """
    if pd.isna(lat) or pd.isna(lon) or pd.isna(date_str):
        return None, None

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "daily": ["temperature_2m_mean", "precipitation_sum"],
    }

    for attempt in range(max_retries):
        try:
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]

            daily = response.Daily()

            # 1. Guard against 'daily' being None
            if daily is None:
                return None, None

            var0 = daily.Variables(0)
            var1 = daily.Variables(1)

            # 2. Guard against individual variables being None
            if var0 is None or var1 is None:
                return None, None

            # Now the type checker knows var0 and var1 are definitively NOT None
            temp = var0.ValuesAsNumpy()[0]
            precip = var1.ValuesAsNumpy()[0]

            # Convert nan to None for database compatibility
            temp = float(temp) if not pd.isna(temp) else None
            precip = float(precip) if not pd.isna(precip) else None
            return temp, precip

        except Exception as e:
            err_msg = str(e).lower()

            if "hourly api request limit exceeded" in err_msg:
                logger.error(
                    "CRITICAL: Hourly rate limit exceeded. Aborting to prevent further blocks."
                )
                raise RateLimitError("Hourly limit reached", is_hourly=True) from e

            if "minutely api request limit exceeded" in err_msg:
                wait_time = (attempt + 1) * 10
                logger.warning(
                    f"Minutely rate limit reached. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}..."
                )
                time.sleep(wait_time)
                continue

            logger.warning(
                f"Weather fetch failed for lat={lat} lon={lon} date={date_str}: {e}"
            )
            return None, None

    return None, None
