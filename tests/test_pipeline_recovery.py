import os
import sqlite3
import pytest
import pandas as pd
from pathlib import Path
from etl.utils.telemetry import TelemetryManager
from etl.utils.checkpoints import CheckpointManager
from etl.config.helpers import PROJECT_ROOT

@pytest.fixture
def test_env(tmp_path):
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    db_path = tmp_path / "metrics.db"
    jsonl_path = tmp_path / "metrics.jsonl"
    
    # We need paths relative to PROJECT_ROOT for TelemetryManager as it prepends it
    # But since tmp_path might be anywhere, we might have issues if it's not under PROJECT_ROOT.
    # Actually TelemetryManager uses PROJECT_ROOT / db_path. 
    # Let's try to use absolute paths by bypassing PROJECT_ROOT if possible, 
    # or just use a subdir in project root for testing.
    
    test_root = PROJECT_ROOT / "data" / "test_recovery"
    if test_root.exists():
        import shutil
        shutil.rmtree(test_root)
    test_root.mkdir(parents=True)
    checkpoint_dir = test_root / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    
    yield {
        "checkpoint_dir": checkpoint_dir,
        "db_path": test_root / "metrics.db",
        "jsonl_path": test_root / "metrics.jsonl",
        "test_root": test_root
    }
    
    import shutil
    shutil.rmtree(test_root)

def test_pipeline_resume_logic(test_env):
    tm = TelemetryManager(
        db_path=str(test_env["db_path"].relative_to(PROJECT_ROOT)),
        jsonl_path=str(test_env["jsonl_path"].relative_to(PROJECT_ROOT)),
        checkpoint_dir=str(test_env["checkpoint_dir"].relative_to(PROJECT_ROOT))
    )
    
    # 1. First run: completes 'extract'
    tm.start_pipeline(resume=False)
    with tm.stage("extract") as s:
        s.set_metrics(count=10)
    
    test_env["checkpoint_dir"].mkdir(exist_ok=True)
    (test_env["checkpoint_dir"] / "extract_checkpoint.pkl").write_text("dummy")
    tm.finish_pipeline(status="error", error="Simulated crash")
    
    # 2. Second run: crashes immediately (creates empty run)
    tm2 = TelemetryManager(
        db_path=str(test_env["db_path"].relative_to(PROJECT_ROOT)),
        jsonl_path=str(test_env["jsonl_path"].relative_to(PROJECT_ROOT)),
        checkpoint_dir=str(test_env["checkpoint_dir"].relative_to(PROJECT_ROOT))
    )
    tm2.start_pipeline(resume=True)
    # No stages completed.
    
    # 3. Third run: should still find 'extract' from run 1
    tm3 = TelemetryManager(
        db_path=str(test_env["db_path"].relative_to(PROJECT_ROOT)),
        jsonl_path=str(test_env["jsonl_path"].relative_to(PROJECT_ROOT)),
        checkpoint_dir=str(test_env["checkpoint_dir"].relative_to(PROJECT_ROOT))
    )
    tm3.start_pipeline(resume=True)
    assert "extract" in tm3.completed_stages

def test_telemetry_is_resume_flag(test_env):
    tm = TelemetryManager(
        db_path=str(test_env["db_path"].relative_to(PROJECT_ROOT)),
        jsonl_path=str(test_env["jsonl_path"].relative_to(PROJECT_ROOT)),
        checkpoint_dir=str(test_env["checkpoint_dir"].relative_to(PROJECT_ROOT))
    )
    
    # Initial run
    tm.start_pipeline(resume=False)
    with tm.stage("extract") as s:
        s.set_metrics(count=10)
    (test_env["checkpoint_dir"] / "extract_checkpoint.pkl").write_text("dummy")
    tm.finish_pipeline(status="error")
    
    # Resume run
    tm.start_pipeline(resume=True)
    with tm.stage("extract") as s:
        assert s.is_resume is True
        s.set_metrics(count=10)
    tm.finish_pipeline(status="success")
    
    # Verify DB
    conn = sqlite3.connect(test_env["db_path"])
    cursor = conn.cursor()
    
    # Run 1
    cursor.execute("SELECT is_resume FROM stage_metrics WHERE run_id = 1 AND stage = 'extract'")
    assert cursor.fetchone()[0] == 0
    
    # Run 2
    cursor.execute("SELECT is_resume FROM stage_metrics WHERE run_id = 2 AND stage = 'extract'")
    assert cursor.fetchone()[0] == 1
    conn.close()
