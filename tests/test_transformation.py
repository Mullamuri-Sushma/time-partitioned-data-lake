
import pandas as pd

from src.transformation import transform_events


def make_event(event_id, timestamp):
    return {
        "event_id": event_id,
        "order_id": f"ORD-{event_id}",
        "customer_id": "CUST001",
        "event_timestamp": timestamp,
        "event_type": "order_placed",
        "amount": 100.00,
        "status": "pending",
        "event_date": None,
        "source_file": "events.csv",
        "source_row_number": 2,
        "run_id": "test-001",
    }


def test_out_of_order_events_are_sorted():
    events = pd.DataFrame([
        make_event("EVT003", "2026-01-03T10:00:00Z"),
        make_event("EVT001", "2026-01-01T10:00:00Z"),
        make_event("EVT002", "2026-01-02T10:00:00Z"),
    ])

    transformed = transform_events(events)

    assert list(transformed["event_id"]) == [
        "EVT001",
        "EVT002",
        "EVT003",
    ]


def test_partition_date_is_derived_from_timestamp():
    events = pd.DataFrame([
        make_event("EVT001", "2026-01-01T23:30:00Z"),
    ])

    transformed = transform_events(events)

    assert str(transformed.iloc[0]["event_date"]) == "2026-01-01"


def test_empty_batch_preserves_expected_schema():
    events = pd.DataFrame()

    transformed = transform_events(events)

    assert transformed.empty
    assert len(transformed.columns) == 11
    assert "event_date" in transformed.columns
    assert "run_id" in transformed.columns
