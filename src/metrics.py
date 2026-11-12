import json
from datetime import datetime, timezone
from pathlib import Path


def save_run_metrics(
    run_id: str,
    input_count: int,
    valid_count: int,
    rejected_count: int,
    publish_stats: dict,
    duration_seconds: float,
    reports_dir: Path,
) -> dict:
    """Save metrics for one pipeline execution."""

    # Verify input reconciliation.
    if input_count != valid_count + rejected_count:
        raise ValueError(
            "Data reconciliation failed: "
            "input count does not equal valid + rejected"
        )

    # Verify that publishing received the valid batch.
    if publish_stats["batch_records"] != valid_count:
        raise ValueError(
            "Publishing batch count does not match valid record count"
        )

    new_records = publish_stats["new_records_added"]
    duplicates = publish_stats["duplicate_records_ignored"]
    total_published = publish_stats["rows_published"]

    # Verify batch-level publishing reconciliation.
    if new_records + duplicates != valid_count:
        raise ValueError(
            "Publishing reconciliation failed: "
            "new records + duplicates must equal valid records"
        )

    if total_published < new_records:
        raise ValueError(
            "Total published records cannot be less than new records"
        )

    metrics = {
        "run_id": run_id,
        "run_timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "input_records": input_count,
        "valid_records": valid_count,
        "rejected_records": rejected_count,
        "batch_records": publish_stats["batch_records"],
        "new_records_added": new_records,
        "duplicate_records_ignored": duplicates,
        "total_published_records": total_published,
        "partition_count": publish_stats["partition_count"],
        "file_count": publish_stats["file_count"],
        "total_size_bytes": publish_stats["total_size_bytes"],
        "duration_seconds": round(duration_seconds, 4),
        "reconciliation_passed": True,
        "status": "SUCCESS",
    }

    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f"run_{run_id}.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    metrics["report_path"] = str(report_path)

    return metrics