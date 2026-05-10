import os
import pickle
import pytest
import pandas as pd
from etl.utils.checkpoints import CheckpointManager
from etl.sources.interface import RawObservation
from datetime import datetime, timezone

@pytest.fixture
def checkpoint_manager(tmp_path):
    return CheckpointManager(checkpoint_dir=str(tmp_path))

def test_atomic_save_and_load(checkpoint_manager):
    obs = [
        RawObservation(
            source="test",
            external_id="1",
            image_url=None,
            label=None,
            is_diseased=False,
            latitude=None,
            longitude=None,
            observation_date=None,
            extracted_at=datetime.now(timezone.utc),
            provenance="test",
            raw_json="{}",
        )
    ]
    checkpoint_manager.save_observations(obs, ["test"])
    
    loaded_obs, loaded_sources = checkpoint_manager.load_observations()
    assert len(loaded_obs) == 1
    assert loaded_obs[0].external_id == "1"
    assert loaded_sources == ["test"]

def test_robust_load_corrupt_file(checkpoint_manager, tmp_path):
    path = os.path.join(tmp_path, "extract_checkpoint.pkl")
    with open(path, "w") as f:
        f.write("corrupt data")
    
    # Should not raise exception, but return empty
    loaded_obs, loaded_sources = checkpoint_manager.load_observations()
    assert loaded_obs == []
    assert loaded_sources == []

def test_atomic_save_dataframe(checkpoint_manager):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    checkpoint_manager.save_dataframe(df)
    
    loaded_df = checkpoint_manager.load_dataframe()
    assert loaded_df is not None
    assert loaded_df.equals(df)

def test_robust_load_corrupt_dataframe(checkpoint_manager, tmp_path):
    path = os.path.join(tmp_path, "transform_checkpoint.pkl")
    with open(path, "w") as f:
        f.write("corrupt data")
    
    loaded_df = checkpoint_manager.load_dataframe()
    assert loaded_df is None

def test_save_quality_json(checkpoint_manager):
    results = {"score": 0.95}
    checkpoint_manager.save_quality(results)
    
    loaded_results = checkpoint_manager.load_quality()
    assert loaded_results == results

def test_robust_load_corrupt_quality(checkpoint_manager, tmp_path):
    path = os.path.join(tmp_path, "quality_checkpoint.json")
    with open(path, "w") as f:
        f.write("not json")
    
    loaded_results = checkpoint_manager.load_quality()
    assert loaded_results is None
