import time
import logging
import os
from pathlib import Path
from datetime import datetime

from etl.config.types import AppConfig
from etl.extract import load_config
from etl.transform import run_transform
from etl.load import run_load
from etl.sources.interface import RawObservation
from utils.logging.setup import setup_logging

logger = logging.getLogger("benchmark")


def create_synthetic_data(count: int) -> list[RawObservation]:
    return [
        RawObservation(
            source="synthetic",
            external_id=f"syn_{i}",
            image_url="http://example.com/img.jpg",
            latitude=45.0,
            longitude=30.0,
            observation_date=datetime(2024, 5, 10),
            extracted_at=datetime.now(),
            label="healthy",
            is_diseased=False,
            raw_json="{}",
            provenance="Synthetic",
        )
        for i in range(count)
    ]


def run_benchmark(config: AppConfig, sizes: list[int]):
    results = []

    # Use a temporary DB for benchmarking
    original_target = config.load.target_path
    config.load.target_path = "data/processed/benchmark_temp.db"

    for size in sizes:
        logger.info(f"Benchmarking with {size} records...")
        observations = create_synthetic_data(size)

        # Transform
        start = time.time()
        df = run_transform(observations)
        transform_time = time.time() - start

        # Load
        start = time.time()
        _ = run_load(df, config)
        load_time = time.time() - start

        total_time = transform_time + load_time
        throughput = size / total_time if total_time > 0 else 0

        results.append(
            {
                "size": size,
                "transform_sec": round(transform_time, 4),
                "load_sec": round(load_time, 4),
                "total_sec": round(total_time, 4),
                "throughput_rec_sec": round(throughput, 2),
            }
        )

    # Cleanup benchmark DB
    db_path = Path("data/processed/benchmark_temp.db")
    if db_path.exists():
        os.remove(db_path)

    # Restore original config
    config.load.target_path = original_target

    return results


def print_results(results):
    print("\n" + "=" * 80)
    print(
        f"{'Size':>10} | {'Transform (s)':>15} | {'Load (s)':>15} | {'Total (s)':>15} | {'Rec/sec':>10}"
    )
    print("-" * 80)
    for res in results:
        print(
            f"{res['size']:10d} | {res['transform_sec']:15.4f} | {res['load_sec']:15.4f} | {res['total_sec']:15.4f} | {res['throughput_rec_sec']:10.2f}"
        )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    config = load_config("etl/config.toml")
    test_sizes = [100, 500, 1000, 5000]
    results = run_benchmark(config, test_sizes)
    setup_logging(config.general.log_level)
    print_results(results)
