import pytest
from etl.sources.weather import get_weather_bulk
from unittest.mock import MagicMock, patch
import pandas as pd

@patch("etl.sources.weather.openmeteo")
def test_get_weather_bulk_generator(mock_openmeteo):
    # Setup mock response
    mock_response = MagicMock()
    mock_daily = MagicMock()
    mock_response.Daily.return_value = mock_daily
    
    # Mocking two variables (temp, precip)
    mock_var0 = MagicMock()
    mock_var0.ValuesAsNumpy.return_value = [20.0]
    mock_var1 = MagicMock()
    mock_var1.ValuesAsNumpy.return_value = [0.0]
    
    mock_daily.Variables.side_effect = lambda i: mock_var0 if i == 0 else mock_var1
    
    mock_openmeteo.weather_api.return_value = [mock_response]
    
    locations = [(10.0, 20.0, "2023-01-01")]
    
    # Run the generator
    results = list(get_weather_bulk(locations))
    
    assert len(results) == 1
    (loc, (temp, precip)) = results[0]
    assert loc == (10.0, 20.0, "2023-01-01")
    assert temp == 20.0
    assert precip == 0.0

@patch("etl.sources.weather.openmeteo")
def test_get_weather_bulk_failure_yields_none(mock_openmeteo):
    # Simulate failure
    mock_openmeteo.weather_api.side_effect = Exception("API Error")
    
    locations = [(10.0, 20.0, "2023-01-01")]
    
    results = list(get_weather_bulk(locations, max_retries=1))
    
    assert len(results) == 1
    (loc, (temp, precip)) = results[0]
    assert temp is None
    assert precip is None
