
import json
import pytest

from src.metrics import save_run_metrics


def make_publish_stats(**overrides):
    stats = {
        "batch_records": 10,
        "new_records_added": 8,
        "duplicate_records_ignored": 2,
        "rows_published": 100,
        "partition_count": 5,
        "file_count": 5,
        "total_size_bytes": 50000,
        "output_dir": "data/processed",
    }

    stats.update(overrides)
    return stats


def test_metrics_report_is_created(tmp_path):
    reports_dir = tmp_path / "reports"

    metrics = save_run_metrics(
        run_id="test-001",
        input_count=12,
        valid_count=10,
        rejected_count=2,
        publish_stats=make_publish_stats(),
        duration_seconds=2.56789,
        reports_dir=reports_dir,
    )

    report_path = reports_dir / "run_test-001.json"

    assert report_path.exists()
    assert metrics["input_records"] == 12
    assert metrics["valid_records"] == 10
    assert metrics["rejected_records"] == 2
    assert metrics["reconciliation_passed"] is True
    assert metrics["status"] == "SUCCESS"
    assert metrics["duration_seconds"] == 2.5679

    with open(report_path, encoding="utf-8") as file:
        saved_report = json.load(file)

    assert saved_report["run_id"] == "test-001"
    assert saved_report["total_published_records"] == 100


def test_input_reconciliation_failure(tmp_path):
    with pytest.raises(
        ValueError,
        match="input count does not equal valid \\+ rejected",
    ):
        save_run_metrics(
            run_id="test-002",
            input_count=12,
            valid_count=9,
            rejected_count=2,
            publish_stats=make_publish_stats(
                batch_records=9,
                new_records_added=7,
                duplicate_records_ignored=2,
            ),
            duration_seconds=1.0,
            reports_dir=tmp_path,
        )


def test_publishing_batch_count_mismatch(tmp_path):
    with pytest.raises(
        ValueError,
        match="Publishing batch count does not match valid record count",
    ):
        save_run_metrics(
            run_id="test-003",
            input_count=12,
            valid_count=10,
            rejected_count=2,
            publish_stats=make_publish_stats(
                batch_records=9,
            ),
            duration_seconds=1.0,
            reports_dir=tmp_path,
        )


def test_publishing_duplicate_reconciliation_failure(tmp_path):
    with pytest.raises(
        ValueError,
        match="new records \\+ duplicates must equal valid records",
    ):
        save_run_metrics(
            run_id="test-004",
            input_count=12,
            valid_count=10,
            rejected_count=2,
            publish_stats=make_publish_stats(
                new_records_added=7,
                duplicate_records_ignored=1,
            ),
            duration_seconds=1.0,
            reports_dir=tmp_path,
        )


def test_total_published_count_cannot_be_less_than_new_records(
    tmp_path,
):
    with pytest.raises(
        ValueError,
        match="Total published records cannot be less than new records",
    ):
        save_run_metrics(
            run_id="test-005",
            input_count=12,
            valid_count=10,
            rejected_count=2,
            publish_stats=make_publish_stats(
                new_records_added=10,
                duplicate_records_ignored=0,
                rows_published=5,
            ),
            duration_seconds=1.0,
            reports_dir=tmp_path,
        )
