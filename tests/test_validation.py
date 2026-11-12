
import pandas as pd

from src.validation import validate_events


def make_event(**overrides):
    event = {
        "event_id": "EVT001",
        "order_id": "ORD001",
        "customer_id": "CUST001",
        "event_timestamp": "2026-01-01T10:00:00Z",
        "event_type": "order_placed",
        "amount": "100.00",
        "status": "pending",
        "source_file": "events.csv",
        "source_row_number": 2,
    }

    event.update(overrides)
    return event


def make_customers():
    return pd.DataFrame({
        "customer_id": ["CUST001", "CUST002"]
    })


# ------------------------------------------------
# 1. Valid event
# ------------------------------------------------

def test_valid_event_is_accepted():
    events = pd.DataFrame([make_event()])

    valid, rejected = validate_events(
        events, make_customers(), "test-001"
    )

    assert len(valid) == 1
    assert len(rejected) == 0
    assert valid.iloc[0]["event_id"] == "EVT001"


# ------------------------------------------------
# 2. Missing customer ID
# ------------------------------------------------

def test_missing_customer_id_is_rejected():
    events = pd.DataFrame([
        make_event(customer_id="")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-002"
    )

    assert len(valid) == 0
    assert "missing_customer_id" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 3. Negative amount
# ------------------------------------------------

def test_negative_amount_is_rejected():
    events = pd.DataFrame([
        make_event(amount="-50.00")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-003"
    )

    assert len(valid) == 0
    assert "negative_amount" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 4. Invalid customer reference
# ------------------------------------------------

def test_unknown_customer_reference_is_rejected():
    events = pd.DataFrame([
        make_event(customer_id="CUST999")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-004"
    )

    assert len(valid) == 0
    assert "invalid_customer_reference" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 5. Duplicate event ID
# ------------------------------------------------

def test_duplicate_event_id_is_rejected():
    events = pd.DataFrame([
        make_event(),
        make_event(source_row_number=3),
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-005"
    )

    assert len(valid) == 1
    assert len(rejected) == 1
    assert "duplicate_event_id" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 6. Zero amount and late event
# ------------------------------------------------

def test_zero_amount_and_late_event_are_valid():
    events = pd.DataFrame([
        make_event(
            amount="0.00",
            event_timestamp="2025-12-02T00:00:00Z",
        )
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-006"
    )

    assert len(valid) == 1
    assert len(rejected) == 0
    assert float(valid.iloc[0]["amount"]) == 0.0
    assert str(valid.iloc[0]["event_date"]) == "2025-12-02"


# ------------------------------------------------
# 7. Missing event ID
# ------------------------------------------------

def test_missing_event_id_is_rejected():
    events = pd.DataFrame([
        make_event(event_id="")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-007"
    )

    assert len(valid) == 0
    assert "missing_event_id" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 8. Missing order ID
# ------------------------------------------------

def test_missing_order_id_is_rejected():
    events = pd.DataFrame([
        make_event(order_id="")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-008"
    )

    assert len(valid) == 0
    assert "missing_order_id" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 9. Malformed timestamp
# ------------------------------------------------

def test_malformed_timestamp_is_rejected():
    events = pd.DataFrame([
        make_event(event_timestamp="not-a-valid-date")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-009"
    )

    assert len(valid) == 0
    assert "invalid_timestamp" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 10. Invalid event type
# ------------------------------------------------

def test_invalid_event_type_is_rejected():
    events = pd.DataFrame([
        make_event(event_type="invalid_event")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-010"
    )

    assert len(valid) == 0
    assert "invalid_event_type" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 11. Invalid status
# ------------------------------------------------

def test_invalid_status_is_rejected():
    events = pd.DataFrame([
        make_event(status="unknown_status")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-011"
    )

    assert len(valid) == 0
    assert "invalid_status" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 12. Invalid amount text
# ------------------------------------------------

def test_invalid_amount_text_is_rejected():
    events = pd.DataFrame([
        make_event(amount="abc")
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-012"
    )

    assert len(valid) == 0
    assert "invalid_amount" in rejected.iloc[0]["reject_reason"]


# ------------------------------------------------
# 13. Null amount
# ------------------------------------------------

def test_null_amount_is_rejected():
    events = pd.DataFrame([
        make_event(amount=None)
    ])

    valid, rejected = validate_events(
        events, make_customers(), "test-013"
    )

    assert len(valid) == 0

    reasons = rejected.iloc[0]["reject_reason"]

    assert "missing_amount" in reasons
    assert "invalid_amount" in reasons
