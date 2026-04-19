from pydantic import HttpUrl
from etl.sources.inaturalist import iNaturalistSource
from etl.config.types import iNaturalistSourceConfig


def test_inaturalist_parse_observation_with_hour():
    # Mock config
    config = iNaturalistSourceConfig(
        enabled=True,
        refetch=False,
        base_url=HttpUrl("https://api.inaturalist.org/v1"),
        taxon_id=47126,
        term_id=9,
        term_value_id=11,
        per_page=1,
        max_pages=1,
        rate_limit_seconds=1.0,
    )

    source = iNaturalistSource(config)

    raw_data = {
        "id": 12345,
        "photos": [{"url": "http://example.com/image.jpg"}],
        "location": "45.0,-122.0",
        "observed_on": "2026-03-31",
        "observed_on_details": {"hour": 16},
        "taxon": {"name": "Test Plant"},
    }

    obs = source._parse_observation(raw_data, is_diseased=True)

    assert obs.external_id == "12345"
    assert obs.observation_date is not None
    assert obs.observation_date.year == 2026
    assert obs.observation_date.month == 3
    assert obs.observation_date.day == 31
    assert obs.observation_date.hour == 16
    assert obs.latitude == 45.0
    assert obs.longitude == -122.0
    assert obs.is_diseased is True
