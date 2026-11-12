
import pandas as pd


TRANSFORMED_COLUMNS = [
    "event_id",
    "order_id",
    "customer_id",
    "event_timestamp",
    "event_type",
    "amount",
    "status",
    "event_date",
    "source_file",
    "source_row_number",
    "run_id",
]


def transform_events(valid_events: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare validated event records for Parquet publishing.
    """

    # Handle empty batches without losing the expected schema.
    if valid_events.empty:
        return pd.DataFrame(columns=TRANSFORMED_COLUMNS)

    transformed = valid_events.copy()

    # Standardize timestamps to UTC.
    transformed["event_timestamp"] = pd.to_datetime(
        transformed["event_timestamp"],
        utc=True
    )

    # Derive the partition date from the event timestamp.
    transformed["event_date"] = (
        transformed["event_timestamp"].dt.date
    )

    # Keep a consistent column order.
    transformed = transformed[TRANSFORMED_COLUMNS]

    # Sort records for predictable output.
    transformed = transformed.sort_values(
        by=["event_date", "event_timestamp", "event_id"]
    ).reset_index(drop=True)

    return transformed
