
import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.publishing import publish_parquet


def make_events():
    """Create sample events for publishing tests."""

    return pd.DataFrame([
        {
            "event_id": "EVT001",
            "order_id": "ORD001",
            "customer_id": "CUST001",
            "event_timestamp": pd.Timestamp(
                "2026-01-01T10:00:00Z"
            ),
            "event_type": "order_placed",
            "amount": 100.00,
            "status": "pending",
            "event_date": pd.Timestamp(
                "2026-01-01"
            ).date(),
            "source_file": "events.csv",
            "source_row_number": 2,
            "run_id": "test-001",
        }
    ])


def read_published_events(output_dir):
    """
    Read individual Parquet files without inferring
    partition columns from Hive-style folder names.
    """

    files = list(output_dir.rglob("*.parquet"))

    if not files:
        return pd.DataFrame()

    frames = [
        pd.read_parquet(file_path)
        for file_path in files
    ]

    return pd.concat(frames, ignore_index=True)


def test_parquet_file_is_created(tmp_path):
    output_dir = tmp_path / "processed"

    stats = publish_parquet(
        make_events(),
        output_dir,
    )

    files = list(output_dir.rglob("*.parquet"))

    assert stats["rows_published"] == 1
    assert stats["file_count"] == 1
    assert stats["partition_count"] == 1
    assert len(files) == 1

    table = pq.read_table(files[0])

    assert table.num_rows == 1
    assert table.column("event_id")[0].as_py() == "EVT001"


def test_empty_dataset_publishes_safely(tmp_path):
    output_dir = tmp_path / "processed"

    empty_events = make_events().iloc[0:0]

    stats = publish_parquet(
        empty_events,
        output_dir,
    )

    files = list(output_dir.rglob("*.parquet"))

    assert stats["rows_published"] == 0
    assert stats["partition_count"] == 0
    assert stats["file_count"] == 0
    assert output_dir.exists()
    assert len(files) == 0


def test_repeated_publish_does_not_duplicate_files(tmp_path):
    output_dir = tmp_path / "processed"
    events = make_events()

    first_stats = publish_parquet(events, output_dir)
    second_stats = publish_parquet(events, output_dir)

    files = list(output_dir.rglob("*.parquet"))

    assert first_stats["file_count"] == 1
    assert second_stats["file_count"] == 1
    assert len(files) == 1

    table = pq.read_table(files[0])

    assert table.num_rows == 1
    assert table.column("event_id")[0].as_py() == "EVT001"


def test_write_failure_preserves_previous_dataset(
    tmp_path,
    monkeypatch,
):
    output_dir = tmp_path / "processed"
    events = make_events()

    publish_parquet(events, output_dir)

    original_file = next(output_dir.rglob("*.parquet"))
    original_bytes = original_file.read_bytes()

    def fail_to_parquet(self, *args, **kwargs):
        raise OSError("Simulated disk write failure")

    monkeypatch.setattr(
        pd.DataFrame,
        "to_parquet",
        fail_to_parquet,
    )

    with pytest.raises(
        OSError,
        match="Simulated disk write failure",
    ):
        publish_parquet(events, output_dir)

    remaining_files = list(output_dir.rglob("*.parquet"))

    assert len(remaining_files) == 1
    assert remaining_files[0].read_bytes() == original_bytes

    staging_dir = tmp_path / "processed.__staging__"
    assert not staging_dir.exists()


def test_interrupted_publish_restores_previous_dataset(
    tmp_path,
    monkeypatch,
):
    output_dir = tmp_path / "processed"
    staging_dir = tmp_path / "processed.__staging__"
    backup_dir = tmp_path / "processed.__backup__"

    events = make_events()

    publish_parquet(events, output_dir)

    original_file = next(output_dir.rglob("*.parquet"))
    original_bytes = original_file.read_bytes()

    output_dir.rename(backup_dir)
    staging_dir.mkdir()

    (staging_dir / "incomplete.txt").write_text(
        "Incomplete publishing",
        encoding="utf-8",
    )

    def fail_to_parquet(self, *args, **kwargs):
        raise OSError("Simulated retry failure")

    monkeypatch.setattr(
        pd.DataFrame,
        "to_parquet",
        fail_to_parquet,
    )

    with pytest.raises(
        OSError,
        match="Simulated retry failure",
    ):
        publish_parquet(events, output_dir)

    restored_files = list(output_dir.rglob("*.parquet"))

    assert len(restored_files) == 1
    assert restored_files[0].read_bytes() == original_bytes

    assert not staging_dir.exists()
    assert not backup_dir.exists()


def test_incremental_publish_preserves_previous_events(tmp_path):
    output_dir = tmp_path / "processed"

    first_batch = make_events()
    publish_parquet(first_batch, output_dir)

    second_batch = make_events().copy()
    second_batch.loc[0, "event_id"] = "EVT002"
    second_batch.loc[0, "order_id"] = "ORD002"
    second_batch.loc[0, "source_row_number"] = 3

    stats = publish_parquet(second_batch, output_dir)

    result = read_published_events(output_dir)

    assert stats["rows_published"] == 2
    assert set(result["event_id"]) == {"EVT001", "EVT002"}


def test_duplicate_event_across_batches_is_ignored(tmp_path):
    output_dir = tmp_path / "processed"

    first_batch = make_events()
    publish_parquet(first_batch, output_dir)

    duplicate_batch = make_events().copy()
    duplicate_batch.loc[0, "amount"] = 999.00

    stats = publish_parquet(duplicate_batch, output_dir)

    result = read_published_events(output_dir)

    assert stats["rows_published"] == 1
    assert len(result) == 1
    assert result.iloc[0]["amount"] == 100.00


def test_late_arriving_event_uses_event_date_partition(tmp_path):
    output_dir = tmp_path / "processed"

    first_batch = make_events()
    publish_parquet(first_batch, output_dir)

    late_event = make_events().copy()
    late_event.loc[0, "event_id"] = "EVT003"
    late_event.loc[0, "event_timestamp"] = pd.Timestamp(
        "2025-12-02T08:00:00Z"
    )
    late_event.loc[0, "event_date"] = pd.Timestamp(
        "2025-12-02"
    ).date()

    stats = publish_parquet(late_event, output_dir)

    result = read_published_events(output_dir)

    assert stats["rows_published"] == 2
    assert set(result["event_id"]) == {"EVT001", "EVT003"}

    late_partition = output_dir / "event_date=2025-12-02"

    assert late_partition.exists()
    assert len(list(late_partition.glob("*.parquet"))) == 1


def test_empty_incremental_batch_preserves_existing_data(tmp_path):
    output_dir = tmp_path / "processed"

    original_events = make_events()
    publish_parquet(original_events, output_dir)

    empty_batch = original_events.iloc[0:0]

    stats = publish_parquet(empty_batch, output_dir)

    result = read_published_events(output_dir)

    assert stats["rows_published"] == 1
    assert len(result) == 1
    assert result.iloc[0]["event_id"] == "EVT001"
