import argparse
import logging
from etl.extract import load_config, get_enabled_sources
from etl.extract.inspector import inspect_source_data
from utils.logging.setup import setup_logging

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Inspect raw data extraction for specific sources."
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Name of the source to inspect (e.g., 'inaturalist', 'ccmt_ghana')",
    )
    parser.add_argument(
        "--all", action="store_true", help="Inspect all enabled sources"
    )

    args = parser.parse_args()
    config = load_config("etl/config.toml")
    sources = get_enabled_sources(config)

    setup_logging(config.general.log_level)

    if not sources:
        logger.error("No enabled sources found in config.")
        return

    found = False
    for source in sources:
        # Check source name (handling both class name and custom local names)

        if args.all or (args.source and args.source.lower() in source.name.lower()):
            inspect_source_data(source, source.name)
            found = True

    if not found:
        print(f"No source matching '{args.source}' was found among enabled sources.")
        print(
            "Enabled sources:",
            [s.name for s in sources],
        )


if __name__ == "__main__":
    main()
