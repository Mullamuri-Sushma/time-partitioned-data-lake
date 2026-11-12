
import json
from pathlib import Path

import duckdb


BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "benchmark_1m_processed"
)

PROFILE_PATH = (
    BASE_DIR
    / "evidence"
    / "performance_results"
    / "duckdb_profile.json"
)

# Find available Parquet files.
parquet_files = list(DATASET_PATH.rglob("*.parquet"))

if not parquet_files:
    raise FileNotFoundError(
        f"No Parquet files found in {DATASET_PATH}"
    )

total_files = len(parquet_files)

# Use the late-arriving event's date.
target_date = "2025-12-02"

connection = duckdb.connect()

try:
    # Enable JSON profiling.
    connection.execute(
        "PRAGMA enable_profiling='json'"
    )

    connection.execute(
        f"PRAGMA profiling_output='{PROFILE_PATH.as_posix()}'"
    )

    # Query only the selected event-date partition.
    query = f"""
        SELECT event_id
        FROM read_parquet(
            '{(DATASET_PATH / "*" / "*.parquet").as_posix()}',
            hive_partitioning=true
        )
        WHERE event_date = DATE '{target_date}'
    """

    result = connection.execute(query).fetchall()

    connection.execute(
        "PRAGMA disable_profiling"
    )

    # Read execution profile.
    with PROFILE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        profile = json.load(file)

    print("\nDUCKDB PARTITION PRUNING RESULTS")
    print("=" * 50)

    print("DuckDB version:", duckdb.__version__)
    print("Total Parquet files:", total_files)
    print("Target event date:", target_date)
    print("Matching records:", len(result))
    print("Matching event IDs:", result)
    print("Profile saved:", PROFILE_PATH)

    print("\nDUCKDB EXECUTION PROFILE")
    print(json.dumps(profile, indent=4))

finally:
    connection.close()
