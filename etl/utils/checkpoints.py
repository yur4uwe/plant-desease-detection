import json
import os
import pickle
import logging
import tempfile
from typing import cast
import pandas as pd
from etl.sources.interface import RawObservation

logger = logging.getLogger(__name__)


class CheckpointManager:
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def _get_path(self, stage: str) -> str:
        ext = "json" if stage == "quality" else "pkl"
        return os.path.join(self.checkpoint_dir, f"{stage}_checkpoint.{ext}")

    def _atomic_save(self, path: str, data: any, method: str = "pickle"):
        fd, temp_path = tempfile.mkstemp(dir=self.checkpoint_dir)
        try:
            if method == "pickle":
                with os.fdopen(fd, "wb") as f:
                    pickle.dump(data, f)
            elif method == "pandas":
                os.close(fd)
                cast(pd.DataFrame, data).to_pickle(temp_path)
            elif method == "json":
                with os.fdopen(fd, "w") as f:
                    json.dump(data, f)
            os.replace(temp_path, path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error(f"Failed to save checkpoint to {path}: {e}")
            raise

    def save_observations(
        self, observations: list[RawObservation], source_names: list[str]
    ):
        path = self._get_path("extract")
        data = {"observations": observations, "source_names": source_names}
        self._atomic_save(path, data)

    def load_observations(self) -> tuple[list[RawObservation], list[str]]:
        path = self._get_path("extract")
        if not os.path.exists(path):
            return [], []
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
                return data["observations"], data["source_names"]
        except (pickle.UnpicklingError, EOFError, AttributeError, Exception) as e:
            logger.warning(f"Failed to load extract checkpoint: {e}. Checkpoint might be corrupt.")
            return [], []

    def save_dataframe(self, df: pd.DataFrame):
        path = self._get_path("transform")
        self._atomic_save(path, df, method="pandas")

    def load_dataframe(self) -> pd.DataFrame | None:
        path = self._get_path("transform")
        if not os.path.exists(path):
            return None
        try:
            return cast(pd.DataFrame, pd.read_pickle(path))
        except (pickle.UnpicklingError, EOFError, Exception) as e:
            logger.warning(f"Failed to load transform checkpoint: {e}. Checkpoint might be corrupt.")
            return None

    def save_quality(self, results: dict):
        path = self._get_path("quality")
        self._atomic_save(path, results, method="json")

    def load_quality(self) -> dict | None:
        path = self._get_path("quality")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to load quality checkpoint: {e}. Checkpoint might be corrupt.")
            return None

    def clear(self):
        """Clears all checkpoints to start fresh."""
        for f in os.listdir(self.checkpoint_dir):
            if f.endswith("_checkpoint.pkl") or f.endswith("_checkpoint.json"):
                os.remove(os.path.join(self.checkpoint_dir, f))
