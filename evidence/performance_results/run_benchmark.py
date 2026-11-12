import json
import time
import uuid
from pathlib import Path

from src.ingestion import ingest_sources
from src.validation import validate_events
from src.transformation import transform_events
from src.publishing import publish_parquet
from src.file_sizing import analyze_file_sizes


BASE_DIR = Path(__file__).resolve().parents[2]

EVENTS_PATH = BASE_DIR / "data" / "benchmark_raw" / "order_events.csv"
CUSTOMERS_PATH = BASE_DIR / "data" / "benchmark_raw" / "customers.csv"

OUTPUT_DIR = BASE_DIR / "data" / "benchmark_processed"

REPORT_DIR = BASE_DIR / "evidence" / "performance_results"

REPORT_PATH = REPORT_DIR / "benchmark_100k.json"


def run_benchmark():
    """Measure performance of the pipeline using 100,000 records."""

    run_id = f"benchmark-{uuid.uuid4().hex[:8]}"

    if not EVENTS_PATH.exists() or not CUSTOMERS_PATH.exists():
        raise FileNotFoundError(
            "Benchmark source files are missing. "
            "Generate the benchmark dataset first."
        )

    existing_files = (
        list(OUTPUT_DIR.rglob("*.parquet"))
        if OUTPUT_DIR.exists()
        else []
    )

    if existing_files:
        raise FileExistsError(
            f"{OUTPUT_DIR} already contains Parquet files. "
            "Remove the benchmark output directory before "
            "running a fresh benchmark."
        )

    timings = {}

    total_start = time.perf_counter()

    # 1. Ingestion
    stage_start = time.perf_counter()

    events, customers = ingest_sources(
        EVENTS_PATH,
        CUSTOMERS_PATH,
    )

    timings["ingestion_seconds"] = round(
        time.perf_counter() - stage_start, 4
    )

    input_count = len(events)

    # 2. Validation
    stage_start = time.perf_counter()

    valid_events, rejected_events = validate_events(
        events,
        customers,
        run_id,
    )

    timings["validation_seconds"] = round(
        time.perf_counter() - stage_start, 4
    )

    # 3. Transformation
    stage_start = time.perf_counter()

    transformed_events = transform_events(valid_events)

    timings["transformation_seconds"] = round(
        time.perf_counter() - stage_start, 4
    )

    # 4. Publishing
    stage_start = time.perf_counter()

    publish_stats = publish_parquet(
        transformed_events,
        OUTPUT_DIR,
    )

    timings["publishing_seconds"] = round(
        time.perf_counter() - stage_start, 4
    )

    timings["total_pipeline_seconds"] = round(
        time.perf_counter() - total_start, 4
    )

    # 5. File-size analysis
    file_size_stats = analyze_file_sizes(OUTPUT_DIR)

    # 6. Reconciliation
    reconciliation_passed = (
        input_count == len(valid_events) + len(rejected_events)
        and publish_stats["rows_published"] == len(transformed_events)
    )

    # 7. Save benchmark report
    report = {
        "benchmark_run_id": run_id,
        "dataset": "100,000 synthetic order events",
        "input_records": input_count,
        "valid_records": len(valid_events),
        "rejected_records": len(rejected_events),
        "transformed_records": len(transformed_events),
        "new_records_added": publish_stats["new_records_added"],
        "total_published_records": publish_stats["rows_published"],
        "partition_count": publish_stats["partition_count"],
        "file_count": publish_stats["file_count"],
        "total_size_bytes": publish_stats["total_size_bytes"],
        "file_size_analysis": file_size_stats,
        "timings": timings,
        "reconciliation_passed": reconciliation_passed,
        "output_directory": str(OUTPUT_DIR),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\nBENCHMARK COMPLETED")
    print("=" * 50)
    print(json.dumps(report, indent=4))
    print(f"\nReport saved to: {REPORT_PATH}")

    if not reconciliation_passed:
        raise RuntimeError("Benchmark reconciliation failed.")

    return report


if __name__ == "__main__":
    run_benchmark()