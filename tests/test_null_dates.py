import pandas as pd
from etl.transform import parse_dates, enrich_environmental_metadata


def test_parse_dates_with_nulls():
    df = pd.DataFrame(
        {
            "observation_date": [None, "2023-01-01", "invalid"],
            "extracted_at": ["2023-01-01", None, "invalid"],
        }
    )

    parsed_df = parse_dates(df)

    # Check that observation_date[0] and observation_date[2] are NaT
    assert pd.isna(parsed_df.loc[0, "observation_date"])
    assert pd.isna(parsed_df.loc[2, "observation_date"])
    assert parsed_df.loc[1, "observation_date"] == pd.Timestamp("2023-01-01")

    # Check that extracted_at[1] and extracted_at[2] are NaT
    assert pd.isna(parsed_df.loc[1, "extracted_at"])
    assert pd.isna(parsed_df.loc[2, "extracted_at"])


def test_enrich_with_null_dates():
    df = pd.DataFrame(
        {
            "latitude": [45.0, 45.0],
            "longitude": [0.0, 0.0],
            "observation_date": [pd.NaT, pd.Timestamp("2023-06-21")],
        }
    )

    # Add required columns for schema if needed or just test the enrichment
    enriched_df = enrich_environmental_metadata(df)

    assert pd.isna(enriched_df.loc[0, "season"])
    assert pd.isna(enriched_df.loc[0, "solar_status"])
    assert enriched_df.loc[1, "season"] == "Summer"
