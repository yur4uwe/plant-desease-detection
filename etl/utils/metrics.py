import json
import os
import time
from datetime import datetime
from typing import Any


class StageContext:
    def __init__(self, collector, name):
        self.collector = collector
        self.name = name
        self.extra_metrics = {}

    def __enter__(self):
        self.collector.start_stage(self.name)
        return self

    def set_metrics(self, **kwargs):
        self.extra_metrics.update(kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.collector.end_stage(self.name, **self.extra_metrics)


class MetricsCollector:
    def __init__(self, metrics_file: str = "logs/pipeline_metrics.jsonl"):
        self.metrics_file = metrics_file
        self.start_time = 0.0
        self.metrics: dict[str, Any] = {
            "timestamp": "",
            "stages": {},
            "counts": {},
            "quality": {},
            "storage": {},
            "status": "success",
            "error": None,
        }
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)

    def start_pipeline(self):
        self.start_time = time.time()
        self.metrics["timestamp"] = datetime.now().isoformat()

    def start_stage(self, stage_name: str):
        self.metrics["stages"][stage_name] = {"start": time.time()}

    def end_stage(self, stage_name: str, **extra_metrics):
        if stage_name in self.metrics["stages"]:
            duration = time.time() - self.metrics["stages"][stage_name]["start"]
            self.metrics["stages"][stage_name]["duration_sec"] = round(duration, 4)
            self.metrics["stages"][stage_name].update(extra_metrics)
            del self.metrics["stages"][stage_name]["start"]
            self._save_partial_metrics(stage_name)

    def _save_partial_metrics(self, stage_name: str):
        """Saves current state of a stage to the log immediately."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "pipeline_start": self.metrics["timestamp"],
            "event": "stage_complete",
            "stage": stage_name,
            "metrics": self.metrics["stages"][stage_name],
        }
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def stage(self, stage_name: str):
        """Returns a context manager for a pipeline stage."""

        return StageContext(self, stage_name)

    def log_counts(
        self,
        extracted: int = 0,
        transformed: int = 0,
        loaded: int = 0,
        sources: list[str] | None = None,
    ):
        self.metrics["counts"] = {
            "extracted": extracted,
            "transformed": transformed,
            "loaded": loaded,
            "sources": sources or [],
        }

    def log_quality(self, quality_results: dict):
        self.metrics["quality"] = quality_results

    def log_storage(self, db_path: str, raw_dir: str, processed_dir: str):
        def get_size(path):
            if os.path.isfile(path):
                return os.path.getsize(path)
            total_size = 0
            if os.path.exists(path):
                for dirpath, _, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)
            return total_size

        self.metrics["storage"] = {
            "db_size_mb": round(get_size(db_path) / (1024 * 1024), 2),
            "raw_images_mb": round(get_size(raw_dir) / (1024 * 1024), 2),
            "processed_images_mb": round(get_size(processed_dir) / (1024 * 1024), 2),
        }

    def finish_pipeline(self, status: str = "success", error: str | None = None):
        self.metrics["status"] = status
        self.metrics["error"] = error
        self.metrics["total_duration_sec"] = round(time.time() - self.start_time, 4)

        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(self.metrics) + "\n")
