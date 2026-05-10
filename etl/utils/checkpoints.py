import json
import os
import pickle
from typing import cast
import pandas as pd
from etl.sources.interface import RawObservation


class CheckpointManager:
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def _get_path(self, stage: str) -> str:
        return os.path.join(self.checkpoint_dir, f"{stage}_checkpoint.pkl")

    def save_observations(
        self, observations: list[RawObservation], source_names: list[str]
    ):
        path = self._get_path("extract")
        data = {"observations": observations, "source_names": source_names}
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load_observations(self) -> tuple[list[RawObservation], list[str]]:
        path = self._get_path("extract")
        if not os.path.exists(path):
            return [], []
        with open(path, "rb") as f:
            data = pickle.load(f)
            return data["observations"], data["source_names"]

    def save_dataframe(self, df: pd.DataFrame):
        path = self._get_path("transform")
        df.to_pickle(path)

    def load_dataframe(self) -> pd.DataFrame | None:
        path = self._get_path("transform")
        if not os.path.exists(path):
            return None
        return cast(pd.DataFrame, pd.read_pickle(path))

    def save_quality(self, results: dict):
        path = self._get_path("quality")
        with open(path, "w") as f:
            json.dump(results, f)

    def load_quality(self) -> dict | None:
        path = self._get_path("quality")
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def clear(self):
        """Clears all checkpoints to start fresh."""
        for f in os.listdir(self.checkpoint_dir):
            if f.endswith("_checkpoint.pkl") or f.endswith("_checkpoint.json"):
                os.remove(os.path.join(self.checkpoint_dir, f))
