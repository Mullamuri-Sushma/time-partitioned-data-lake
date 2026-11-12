
import pandas as pd

from pathlib import Path


EVENT_COLUMNS = [
    "event_id",
    "order_id",
    "customer_id",
    "event_timestamp",
    "event_type",
    "amount",
    "status",
]

CUSTOMER_COLUMNS = [
    "customer_id",
]


def read_csv_safely(file_path: Path, expected_columns: list):
    """
    Read CSV as strings to preserve raw source values.
    Reject unexpected schemas and malformed CSV files.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {file_path}"
        )

    try:
        df = pd.read_csv(
            file_path,
            dtype=str,
            keep_default_na=False,
            on_bad_lines="error",
        )
    except pd.errors.EmptyDataError as exc:
        raise ValueError(
            f"CSV file is empty or has no header: {file_path}"
        ) from exc

    if list(df.columns) != expected_columns:
        raise ValueError(
            f"Unexpected schema in {file_path.name}. "
            f"Expected {expected_columns}, "
            f"received {list(df.columns)}"
        )

    return df


def ingest_sources(events_path: Path, customers_path: Path):
    """
    Read event and customer source datasets.
    """

    events = read_csv_safely(
        events_path,
        EVENT_COLUMNS,
    )

    customers = read_csv_safely(
        customers_path,
        CUSTOMER_COLUMNS,
    )

    events["source_file"] = Path(events_path).name

    # CSV line 1 is the header; first data record is line 2.
    events["source_row_number"] = range(
        2, len(events) + 2
    )

    return events, customers
