
import shutil
import time
from pathlib import Path

import pandas as pd

from src.partitioning import split_by_date, get_partition_path


def rename_with_retry(
    source: Path,
    destination: Path,
    attempts: int = 5,
    delay_seconds: float = 1.0,
) -> None:
    """
    Retry directory renaming when Windows temporarily
    locks files or directories.
    """

    for attempt in range(attempts):
        try:
            source.rename(destination)
            return

        except PermissionError:
            if attempt == attempts - 1:
                raise

            time.sleep(delay_seconds)


def recover_interrupted_publish(
    output_dir: Path,
    staging_dir: Path,
    backup_dir: Path,
) -> None:
    """Recover the previous valid dataset after interruption."""

    if backup_dir.exists():
        if output_dir.exists():
            shutil.rmtree(backup_dir)
        else:
            rename_with_retry(backup_dir, output_dir)

    if staging_dir.exists():
        shutil.rmtree(staging_dir)


def read_existing_dataset(output_dir: Path) -> pd.DataFrame:
    """Read previously published Parquet records."""

    if not output_dir.exists():
        return pd.DataFrame()

    parquet_files = list(output_dir.rglob("*.parquet"))

    if not parquet_files:
        return pd.DataFrame()

    frames = [
        pd.read_parquet(file_path)
        for file_path in parquet_files
    ]

    return pd.concat(frames, ignore_index=True)


def calculate_publish_stats(
    output_dir: Path,
    rows_published: int,
    partition_count: int,
    batch_records: int = 0,
    new_records_added: int = 0,
    duplicate_records_ignored: int = 0,
) -> dict:
    """Calculate statistics for the published dataset."""

    parquet_files = list(output_dir.rglob("*.parquet"))

    total_bytes = sum(
        file_path.stat().st_size
        for file_path in parquet_files
    )

    return {
        "batch_records": batch_records,
        "new_records_added": new_records_added,
        "duplicate_records_ignored": duplicate_records_ignored,
        "rows_published": rows_published,
        "partition_count": partition_count,
        "file_count": len(parquet_files),
        "total_size_bytes": total_bytes,
        "output_dir": str(output_dir),
    }


def publish_parquet(
    events: pd.DataFrame,
    output_dir: Path,
) -> dict:
    """
    Incrementally publish events into date-partitioned Parquet.

    Existing events are retained.
    Duplicate event IDs are ignored.
    Staging and backup directories protect existing data.
    """

    output_dir = Path(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    staging_dir = output_dir.parent / (
        f"{output_dir.name}.__staging__"
    )

    backup_dir = output_dir.parent / (
        f"{output_dir.name}.__backup__"
    )

    # Recover from an interrupted previous publishing operation.
    recover_interrupted_publish(
        output_dir,
        staging_dir,
        backup_dir,
    )

    existing_events = read_existing_dataset(output_dir)

    batch_records = len(events)

    # Case 1: Empty input with existing records.
    # Never erase previously published data.
    if events.empty and not existing_events.empty:

        partition_count = len(
            list(output_dir.glob("event_date=*"))
        )

        return calculate_publish_stats(
            output_dir=output_dir,
            rows_published=len(existing_events),
            partition_count=partition_count,
        )

    # Case 2: Both input and existing dataset are empty.
    if events.empty and existing_events.empty:

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return calculate_publish_stats(
            output_dir=output_dir,
            rows_published=0,
            partition_count=0,
        )

    # Identify existing event IDs.
    if existing_events.empty:
        existing_ids = set()
    else:
        existing_ids = set(
            existing_events["event_id"].astype(str)
        )

    # Remove duplicates inside the incoming batch.
    incoming_unique = events.drop_duplicates(
        subset=["event_id"],
        keep="first",
    )

    # Identify genuinely new events.
    new_events = incoming_unique[
        ~incoming_unique["event_id"]
        .astype(str)
        .isin(existing_ids)
    ]

    new_records_added = len(new_events)

    duplicate_records_ignored = (
        batch_records - new_records_added
    )

    # Combine old and incoming records.
    if existing_events.empty:
        combined_events = events.copy()
    else:
        combined_events = pd.concat(
            [existing_events, events],
            ignore_index=True,
        )

    # Keep only one record per event ID.
    combined_events = combined_events.drop_duplicates(
        subset=["event_id"],
        keep="first",
    ).reset_index(drop=True)

    # Create a fresh staging directory.
    staging_dir.mkdir(parents=True)

    partitions = split_by_date(combined_events)

    try:

        # Write each event-date partition.
        for event_date, group in partitions.items():

            partition_dir = get_partition_path(
                staging_dir,
                event_date,
            )

            partition_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            file_path = (
                partition_dir / "part-00000.parquet"
            )

            group.to_parquet(
                file_path,
                engine="pyarrow",
                compression="snappy",
                index=False,
            )

        # Move the previous dataset to backup.
        if output_dir.exists():

            rename_with_retry(
                output_dir,
                backup_dir,
            )

        try:

            # Move the completed staging dataset into place.
            rename_with_retry(
                staging_dir,
                output_dir,
            )

        except Exception:

            # Restore the previous dataset if publishing fails.
            if backup_dir.exists() and not output_dir.exists():

                rename_with_retry(
                    backup_dir,
                    output_dir,
                )

            raise

        # Remove backup only after successful publishing.
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

    except Exception:

        # Clean incomplete staging data.
        if staging_dir.exists():
            shutil.rmtree(staging_dir)

        raise

    # Return final publishing statistics.
    return calculate_publish_stats(
        output_dir=output_dir,
        rows_published=len(combined_events),
        partition_count=len(partitions),
        batch_records=batch_records,
        new_records_added=new_records_added,
        duplicate_records_ignored=duplicate_records_ignored,
    )
