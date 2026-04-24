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


def get_weather_bulk(
    locations: list[tuple[float, float, str]], max_retries: int = 3
) -> list[tuple[float | None, float | None]]:
    """
    Fetches weather data for multiple locations in batches.
    'locations' is a list of (lat, lon, date_str).
    Returns a list of (temperature, precipitation) in the same order.
    """
    if not locations:
        return []

    results: list[tuple[float | None, float | None]] = [(None, None)] * len(locations)
    url = "https://archive-api.open-meteo.com/v1/archive"

    # Process in chunks of 50 (Open-Meteo allows up to 50 locations per request)
    chunk_size = 50
    for i in range(0, len(locations), chunk_size):
        chunk = locations[i : i + chunk_size]
        lats = [c[0] for c in chunk]
        lons = [c[1] for c in chunk]
        
        # Open-Meteo bulk requires same start/end date or a single date if consistent
        # For simplicity in this project, we'll group by date if dates vary, 
        # but here we'll assume we can pass the lists.
        # Actually, Open-Meteo historical bulk works best when dates are also passed as lists
        # but the archive API expects a single start/end date per request.
        
        # REVISED STRATEGY: Group chunk by date to minimize API calls
        date_map: dict[str, list[int]] = {}
        for idx, (_, _, date_str) in enumerate(chunk):
            date_map.setdefault(date_str, []).append(idx)
            
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
            
            for attempt in range(max_retries):
                try:
                    # Small mandatory sleep to avoid burst limit
                    time.sleep(0.5)
                    responses = openmeteo.weather_api(url, params=params)
                    
                    for sub_idx, response in enumerate(responses):
                        daily = response.Daily()
                        if daily:
                            var0 = daily.Variables(0)
                            var1 = daily.Variables(1)
                            if var0 and var1:
                                temp = float(var0.ValuesAsNumpy()[0])
                                precip = float(var1.ValuesAsNumpy()[0])
                                temp = temp if not pd.isna(temp) else None
                                precip = precip if not pd.isna(precip) else None
                                
                                # Map back to original results list
                                original_idx = i + chunk_indices[sub_idx]
                                results[original_idx] = (temp, precip)
                    break # Success
                except Exception as e:
                    err_msg = str(e).lower()
                    if "limit exceeded" in err_msg:
                        wait_time = (attempt + 1) * 10
                        logger.warning(f"Rate limit hit in bulk. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    logger.warning(f"Bulk weather fetch failed for date {date_str}: {e}")
                    break

    return results
