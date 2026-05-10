import sqlite3
import logging
import time
import os
from datetime import datetime
from typing import Optional
from etl.config.helpers import PROJECT_ROOT

logger = logging.getLogger(__name__)


class StageContext:
    def __init__(self, manager: "TelemetryManager", name: str, is_resume: bool):
        self.manager = manager
        self.name = name
        self.is_resume = is_resume
        self.start_time = 0.0
        self.extra_metrics = {}

    def __enter__(self):
        self.start_time = time.time()
        return self

    def set_metrics(self, **kwargs):
        self.extra_metrics.update(kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            duration = time.time() - self.start_time
            count = self.extra_metrics.get("count", 0)
            self.manager.log_stage(self.name, duration, count, is_resume=self.is_resume)


class TelemetryManager:
    def __init__(
        self,
        db_path: str = "data/processed/metrics.db",
        checkpoint_dir: str = "data/checkpoints",
    ):
        self.db_path = PROJECT_ROOT / db_path
        self.checkpoint_dir = PROJECT_ROOT / checkpoint_dir
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

        self.run_id: Optional[int] = None
        self.start_time: float = 0.0
        self.completed_stages: set[str] = set()
        self.pipeline_start_iso = ""

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    total_duration REAL,
                    error TEXT
                );
                CREATE TABLE IF NOT EXISTS stage_metrics (
                    run_id INTEGER,
                    stage TEXT,
                    duration REAL,
                    item_count INTEGER,
                    is_resume INTEGER DEFAULT 0,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                );
                CREATE TABLE IF NOT EXISTS quality_history (
                    run_id INTEGER,
                    integral_score REAL,
                    q1_critical REAL,
                    q2_uniqueness REAL,
                    q3_metadata REAL,
                    q4_balance REAL,
                    total_rows INTEGER,
                    diseased_ratio REAL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                );
            """)

    def start_pipeline(self, resume: bool = False):
        self.start_time = time.time()
        self.pipeline_start_iso = datetime.now().isoformat()

        if resume:
            self.completed_stages = self._get_completed_stages()
            logger.info(f"Resuming pipeline. Completed stages: {self.completed_stages}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("INSERT INTO runs (status) VALUES (?)", ("running",))
            self.run_id = cursor.lastrowid

    def _get_completed_stages(self) -> set[str]:
        # Query the stages from the most recent run that has any metrics
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT MAX(run_id) FROM stage_metrics")
            latest_run_with_metrics = cursor.fetchone()[0]

            if latest_run_with_metrics is None:
                return set()

            cursor = conn.execute(
                """
                SELECT stage FROM stage_metrics WHERE run_id = ?
                """,
                (latest_run_with_metrics,),
            )
            db_stages = {row[0] for row in cursor.fetchall()}

        # Verify that checkpoints actually exist for these stages
        # If we cleared checkpoints (e.g. after a successful run), we can't resume even if DB says it was done.
        if not self.checkpoint_dir.exists():
            return set()

        files = os.listdir(self.checkpoint_dir)
        valid_resumes = set()

        if "extract" in db_stages and any(
            f.startswith("extract_checkpoint") for f in files
        ):
            valid_resumes.add("extract")
        if "transform" in db_stages and any(
            f.startswith("transform_checkpoint") for f in files
        ):
            valid_resumes.add("transform")
        if "quality" in db_stages and any(
            f.startswith("quality_checkpoint") for f in files
        ):
            valid_resumes.add("quality")
        # Load stage doesn't have a checkpoint, it's just a state in DB
        if "load" in db_stages:
            valid_resumes.add("load")

        return valid_resumes

    def should_run(self, stage_name: str) -> bool:
        return stage_name not in self.completed_stages

    def stage(self, name: str):
        is_resume = not self.should_run(name)
        return StageContext(self, name, is_resume)

    def log_stage(
        self, stage: str, duration: float, count: int = 0, is_resume: bool = False
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO stage_metrics (run_id, stage, duration, item_count, is_resume) VALUES (?, ?, ?, ?, ?)",
                (self.run_id, stage, duration, count, 1 if is_resume else 0),
            )

    def log_quality(self, results: dict):
        m = results["metrics"]
        c = results["raw_counts"]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO quality_history 
                   (run_id, integral_score, q1_critical, q2_uniqueness, q3_metadata, q4_balance, total_rows, diseased_ratio) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.run_id,
                    results["integral_score"],
                    m["q1_completeness_critical"],
                    m["q2_uniqueness"],
                    m["q3_metadata"],
                    m["q4_balance"],
                    c["total_rows"],
                    c["diseased_ratio"],
                ),
            )

    def finish_pipeline(self, status: str = "success", error: str | None = None):
        duration = time.time() - self.start_time
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE runs SET status = ?, total_duration = ?, error = ? WHERE run_id = ?",
                (status, duration, error, self.run_id),
            )
