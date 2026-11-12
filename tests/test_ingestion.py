import pytest

from src.ingestion import ingest_sources, read_csv_safely, EVENT_COLUMNS


def test_successful_ingestion(tmp_path):
    events_file = tmp_path / "events.csv"
    customers_file = tmp_path / "customers.csv"

    events_file.write_text(
        ",".join(EVENT_COLUMNS)
        + "\nEVT001,ORD001,CUST001,2026-01-01T10:00:00Z,"
          "order_placed,100.00,pending\n",
        encoding="utf-8",
    )

    customers_file.write_text(
        "customer_id\nCUST001\n",
        encoding="utf-8",
    )

    events, customers = ingest_sources(
        events_file,
        customers_file,
    )

    assert len(events) == 1
    assert len(customers) == 1
    assert events.iloc[0]["event_id"] == "EVT001"
    assert events.iloc[0]["source_row_number"] == 2


def test_missing_file_raises_error(tmp_path):
    missing_file = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        read_csv_safely(missing_file, EVENT_COLUMNS)


def test_empty_csv_raises_error(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        read_csv_safely(empty_file, EVENT_COLUMNS)


def test_schema_drift_raises_error(tmp_path):
    events_file = tmp_path / "events.csv"

    events_file.write_text(
        "event_id,order_id,unexpected_column\n"
        "EVT001,ORD001,value\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        read_csv_safely(events_file, EVENT_COLUMNS)
