from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from etl.config.helpers import PROJECT_ROOT


def generate_report(
    db_path: Path = Path("data/processed/metrics.db"),
    output_dir: Path = Path("observability"),
):
    db_path = PROJECT_ROOT / db_path
    output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        print(f"Metrics database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)

    # 1. Pipeline Run History
    runs_df = pd.read_sql_query("SELECT * FROM runs", conn)
    runs_df["timestamp"] = pd.to_datetime(runs_df["timestamp"])

    # 2. Quality History
    quality_df = pd.read_sql_query(
        "SELECT * FROM quality_history JOIN runs USING(run_id)", conn
    )
    quality_df["timestamp"] = pd.to_datetime(quality_df["timestamp"])

    # 3. Stage Performance
    stages_df = pd.read_sql_query(
        "SELECT * FROM stage_metrics JOIN runs USING(run_id)", conn
    )
    stages_df["timestamp"] = pd.to_datetime(stages_df["timestamp"])

    sns.set_theme(style="whitegrid")

    # Chart 1: Quality Score Trend
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=quality_df, x="timestamp", y="integral_score", marker="o")
    plt.title("Integral Quality Score (Q) Trend")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "quality_trend.png")

    # Chart 2: Row Counts over time
    plt.figure(figsize=(10, 6))
    sns.barplot(data=quality_df, x="timestamp", y="total_rows", color="skyblue")
    plt.title("Dataset Size Growth")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "growth_trend.png")

    # Chart 3: Stage Durations
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=stages_df, x="timestamp", y="duration", hue="stage", marker="s")
    plt.title("Stage Duration Trends (Latency)")
    plt.ylabel("Duration (seconds)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "performance_trend.png")

    # Chart 4: Disease Ratio stability
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=quality_df, x="timestamp", y="diseased_ratio", color="red", marker="x"
    )
    plt.axhline(0.5, ls="--", color="gray", alpha=0.5)
    plt.title("Target Class Balance Stability (Target: 0.5)")
    plt.ylim(0, 1.0)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "balance_trend.png")

    conn.close()
    print(f"Observability reports generated in {output_dir}")


if __name__ == "__main__":
    generate_report()
