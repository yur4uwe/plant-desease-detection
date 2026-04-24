import argparse
import logging
from etl.extract import load_config, get_enabled_sources
from etl.extract.inspector import inspect_source_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
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

    if not sources:
        logger.error("No enabled sources found in config.")
        return

    found = False
    for source in sources:
        # Check source name (handling both class name and custom local names)
        source_name = source.__class__.__name__.lower()
        if hasattr(source, "config") and hasattr(source.config, "name"):
            source_name = source.config.name

        if args.all or (args.source and args.source.lower() in source_name.lower()):
            inspect_source_data(source, source_name)
            found = True

    if not found:
        print(f"No source matching '{args.source}' was found among enabled sources.")
        print(
            "Enabled sources:",
            [
                s.config.name
                if hasattr(s, "config") and hasattr(s.config, "name")
                else s.__class__.__name__
                for s in sources
            ],
        )


if __name__ == "__main__":
    main()
