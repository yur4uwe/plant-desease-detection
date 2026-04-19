import pandas as pd
from datetime import datetime, timezone
from etl.transform import _get_season, _get_solar_status, enrich_environmental_metadata


def test_get_season():
    # Northern Hemisphere
    assert _get_season(45.0, 4) == "Spring"
    assert _get_season(45.0, 7) == "Summer"
    assert _get_season(45.0, 10) == "Autumn"
    assert _get_season(45.0, 1) == "Winter"

    # Southern Hemisphere
    assert _get_season(-45.0, 4) == "Autumn"
    assert _get_season(-45.0, 7) == "Winter"
    assert _get_season(-45.0, 10) == "Spring"
    assert _get_season(-45.0, 1) == "Summer"

    # Edge Cases
    assert _get_season(None, 4) is None  # pyright: ignore[reportArgumentType]
    assert _get_season(45.0, None) is None  # pyright: ignore[reportArgumentType]


def test_get_solar_status():
    # Typical daylight (noon)
    dt = datetime(2026, 3, 21, 12, 0, 0, tzinfo=timezone.utc)
    # Equator on equinox
    status = _get_solar_status(0.0, 0.0, dt)
    assert status == "Daylight"

    # Typical night (midnight)
    dt_night = datetime(2026, 3, 21, 0, 0, 0, tzinfo=timezone.utc)
    status_night = _get_solar_status(0.0, 0.0, dt_night)
    assert status_night == "Night"

    # Polar Day (Longyearbyen, June)
    dt_polar = datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)
    status_polar = _get_solar_status(78.2, 15.6, dt_polar)
    assert status_polar in ["Daylight", "Polar"]


def test_enrich_environmental_metadata(mocker):
    # Mock weather API to avoid network calls
    mocker.patch("etl.transform.get_weather_for_location", return_value=(20.5, 0.0))

    df = pd.DataFrame(
        {
            "latitude": [45.0, -45.0],
            "longitude": [0.0, 0.0],
            "observation_date": [
                datetime(2026, 6, 21, 12, 0, 0),
                datetime(2026, 6, 21, 12, 0, 0),
            ],
        }
    )

    enriched_df = enrich_environmental_metadata(df)

    assert "season" in enriched_df.columns
    assert "solar_status" in enriched_df.columns
    assert "temperature" in enriched_df.columns
    assert "precipitation" in enriched_df.columns

    assert enriched_df.loc[0, "season"] == "Summer"
    assert enriched_df.loc[1, "season"] == "Winter"
    assert enriched_df.loc[0, "temperature"] == 20.5
