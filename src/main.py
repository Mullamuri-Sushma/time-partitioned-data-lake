import argparse
import json
import time
import uuid

from pathlib import Path

from src.config import (
    RAW_DIR,
    PROCESSED_DIR,
    QUARANTINE_DIR,
    REPORTS_DIR,
)
from src.ingestion import ingest_sources
from src.validation import validate_events
from src.transformation import transform_events
from src.publishing import publish_parquet
from src.metrics import save_run_metrics


def run_pipeline(events_path, customers_path):
    """Execute the complete data lake pipeline."""

    start_time = time.perf_counter()
    run_id = f"run-{uuid.uuid4().hex[:12]}"

    print(f"\nStarting pipeline: {run_id}")

    # 1. Ingestion
    print("\n1. Ingesting source files...")

    events, customers = ingest_sources(
        events_path,
        customers_path,
    )

    input_count = len(events)
    print(f"   Input events: {input_count}")

    # 2. Validation
    print("\n2. Validating events...")

    valid_events, rejected_events = validate_events(
        events,
        customers,
        run_id,
    )

    valid_count = len(valid_events)
    rejected_count = len(rejected_events)

    print(f"   Valid events: {valid_count}")
    print(f"   Rejected events: {rejected_count}")

    # Save rejected records for investigation.
    if not rejected_events.empty:
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

        reject_path = (
            QUARANTINE_DIR / f"rejected_{run_id}.csv"
        )

        rejected_events.to_csv(reject_path, index=False)

        print(f"   Rejected records saved: {reject_path}")

    # 3. Transformation
    print("\n3. Transforming valid events...")

    transformed_events = transform_events(valid_events)

    print(f"   Transformed events: {len(transformed_events)}")

    # 4. Publishing
    print("\n4. Publishing Parquet dataset...")

    publish_stats = publish_parquet(
        transformed_events,
        PROCESSED_DIR,
    )

    print(f"   Batch records: {publish_stats['batch_records']}")
    print(f"   New records added: {publish_stats['new_records_added']}")
    print(
        "   Duplicate records ignored: "
        f"{publish_stats['duplicate_records_ignored']}"
    )
    print(
        "   Total records in data lake: "
        f"{publish_stats['rows_published']}"
    )
    print(f"   Published files: {publish_stats['file_count']}")
    print(f"   Date partitions: {publish_stats['partition_count']}")

    # 5. Metrics and reconciliation
    print("\n5. Saving pipeline metrics...")

    duration = time.perf_counter() - start_time

    metrics = save_run_metrics(
        run_id=run_id,
        input_count=input_count,
        valid_count=valid_count,
        rejected_count=rejected_count,
        publish_stats=publish_stats,
        duration_seconds=duration,
        reports_dir=REPORTS_DIR,
    )

    print("\nPIPELINE COMPLETED")
    print("=" * 45)
    print(json.dumps(metrics, indent=4))

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Run the time-partitioned data lake pipeline"
    )

    parser.add_argument(
        "--events",
        default=str(RAW_DIR / "order_events.csv"),
        help="Path to order events CSV",
    )

    parser.add_argument(
        "--customers",
        default=str(RAW_DIR / "customers.csv"),
        help="Path to customers CSV",
    )

    args = parser.parse_args()

    run_pipeline(
        Path(args.events),
        Path(args.customers),
    )


if __name__ == "__main__":
    main()