import logging
import pandas as pd
from etl.sources.interface import RawObservation, SourceInterface

logger = logging.getLogger(__name__)


def observations_to_df(observations: list[RawObservation]) -> pd.DataFrame:
    """Converts a list of RawObservations into a Pandas DataFrame for inspection."""
    if not observations:
        return pd.DataFrame()

    data = [obs.to_dict() for obs in observations]
    df = pd.DataFrame(data)

    # Cast dates
    if "observation_date" in df.columns:
        df["observation_date"] = pd.to_datetime(df["observation_date"])
    if "extracted_at" in df.columns:
        df["extracted_at"] = pd.to_datetime(df["extracted_at"])

    return df


def inspect_source_data(source: SourceInterface, name: str):
    """Fetches data from a source and prints statistical information."""
    logger.info(f"--- Inspecting Source: {name} ---")
    observations = list(source.fetch())

    if not observations:
        logger.warning(f"No data retrieved from source: {name}")
        return

    df = observations_to_df(observations)

    print(f"\n[ {name.upper()} INFO ]")
    print(df.info())

    print(f"\n[ {name.upper()} SAMPLE ]")
    print(df.head())

    print(f"\n[ {name.upper()} TARGET BALANCE ]")
    if "is_diseased" in df.columns:
        print(df["is_diseased"].value_counts(normalize=True))

    print(f"\n[ {name.upper()} MISSING VALUES ]")
    print(df.isnull().sum())

    return df
