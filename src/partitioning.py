
from pathlib import Path

import pandas as pd


def split_by_date(
    events: pd.DataFrame,
) -> dict:
    """
    Split transformed events into daily groups.
    The partition date comes from the event timestamp.
    """

    if events.empty:
        return {}

    if "event_date" not in events.columns:
        raise ValueError("Missing event_date column")

    partitions = {}

    for event_date, group in events.groupby("event_date", sort=True):
        partitions[event_date] = group.copy()

    return partitions


def get_partition_path(
    base_dir: Path,
    event_date,
) -> Path:
    """
    Build a Hive-style daily partition directory.
    """

    partition_date = pd.Timestamp(event_date).strftime("%Y-%m-%d")

    return Path(base_dir) / f"event_date={partition_date}"
