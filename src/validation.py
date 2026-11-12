
import json
from decimal import Decimal, InvalidOperation

import pandas as pd


VALID_EVENT_TYPES = {
    "order_placed",
    "payment_completed",
    "order_shipped",
    "order_delivered",
    "order_cancelled",
}

VALID_STATUSES = {
    "pending",
    "completed",
    "shipped",
    "delivered",
    "cancelled",
}

REJECT_COLUMNS = [
    "source_file",
    "source_row_number",
    "event_id",
    "reject_reason",
    "raw_record",
]

VALID_COLUMNS = [
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

REQUIRED_COLUMNS = [
    "event_id",
    "order_id",
    "customer_id",
    "event_timestamp",
    "event_type",
    "amount",
    "status",
]


def parse_amount(value):
    """
    Parse amount using Decimal to preserve financial precision.

    Returns:
        amount, error_reason
    """

    try:
        amount = Decimal(value)

        if not amount.is_finite():
            return None, "non_finite_amount"

        if amount < 0:
            return None, "negative_amount"

        return amount, None

    except (InvalidOperation, ValueError, TypeError):
        return None, "invalid_amount"


def validate_events(
    events: pd.DataFrame,
    customers: pd.DataFrame,
    run_id: str,
):
    """
    Validate source events using vectorized Pandas operations.

    Returns:
        valid_df, rejected_df
    """

    # ------------------------------------------------
    # 1. Validate customer reference data
    # ------------------------------------------------

    customer_ids = (
        customers["customer_id"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if customer_ids.eq("").any():
        raise ValueError(
            "Customer reference contains missing customer IDs"
        )

    if customer_ids.duplicated().any():
        raise ValueError(
            "Customer reference contains duplicate customer IDs"
        )

    known_customers = set(customer_ids)

    # ------------------------------------------------
    # 2. Normalize source columns
    # ------------------------------------------------

    df = events.copy()

    for column in REQUIRED_COLUMNS:
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # ------------------------------------------------
    # 3. Required-field validation
    # ------------------------------------------------

    missing_masks = {
        column: df[column].eq("")
        for column in REQUIRED_COLUMNS
    }

    # ------------------------------------------------
    # 4. Duplicate event ID validation
    # ------------------------------------------------

    event_ids = df["event_id"]

    duplicate_mask = (
        event_ids.ne("")
        & event_ids.duplicated(keep="first")
    )

    # ------------------------------------------------
    # 5. Customer reference validation
    # ------------------------------------------------

    customer_mask = (
        df["customer_id"].ne("")
        & ~df["customer_id"].isin(known_customers)
    )

    # ------------------------------------------------
    # 6. Timestamp validation
    # ------------------------------------------------

    parsed_timestamps = pd.to_datetime(
        df["event_timestamp"],
        utc=True,
        errors="coerce",
        format="mixed",
    )

    timestamp_mask = parsed_timestamps.isna()

    # ------------------------------------------------
    # 7. Event type and status validation
    # ------------------------------------------------

    event_type_mask = (
        df["event_type"].ne("")
        & ~df["event_type"].isin(VALID_EVENT_TYPES)
    )

    status_mask = (
        df["status"].ne("")
        & ~df["status"].isin(VALID_STATUSES)
    )

    # ------------------------------------------------
    # 8. Amount validation
    # ------------------------------------------------

    amount_results = df["amount"].map(parse_amount)

    amounts = amount_results.map(lambda result: result[0])

    amount_errors = amount_results.map(
        lambda result: result[1]
    )

    amount_masks = {
        "non_finite_amount": amount_errors.eq(
            "non_finite_amount"
        ),
        "negative_amount": amount_errors.eq(
            "negative_amount"
        ),
        "invalid_amount": amount_errors.eq(
            "invalid_amount"
        ),
    }

    # ------------------------------------------------
    # 9. Combine validation masks
    # ------------------------------------------------

    all_masks = {
        **{
            f"missing_{column}": mask
            for column, mask in missing_masks.items()
        },
        "duplicate_event_id": duplicate_mask,
        "invalid_customer_reference": customer_mask,
        "invalid_timestamp": timestamp_mask,
        "invalid_event_type": event_type_mask,
        "invalid_status": status_mask,
        **amount_masks,
    }

    invalid_mask = pd.Series(
        False,
        index=df.index,
    )

    for mask in all_masks.values():
        invalid_mask |= mask

    # ------------------------------------------------
    # 10. Build rejected records
    # ------------------------------------------------

    rejected_indices = df.index[invalid_mask]

    rejected_rows = []

    for index in rejected_indices:

        row = df.loc[index]

        reasons = [
            reason
            for reason, mask in all_masks.items()
            if mask.loc[index]
        ]

        raw_record = json.dumps(
            events.loc[index].to_dict(),
            default=str,
        )

        rejected_rows.append({
            "source_file": row["source_file"],
            "source_row_number": row["source_row_number"],
            "event_id": row["event_id"],
            "reject_reason": ";".join(reasons),
            "raw_record": raw_record,
        })

    rejected_df = pd.DataFrame(
        rejected_rows,
        columns=REJECT_COLUMNS,
    )

    # ------------------------------------------------
    # 11. Build valid records
    # ------------------------------------------------

    valid_df = df.loc[~invalid_mask].copy()

    valid_df["event_timestamp"] = parsed_timestamps.loc[
        ~invalid_mask
    ]

    valid_df["amount"] = amounts.loc[
        ~invalid_mask
    ]

    valid_df["event_date"] = (
        valid_df["event_timestamp"].dt.date
    )

    valid_df["run_id"] = run_id

    valid_df = valid_df[VALID_COLUMNS].reset_index(drop=True)

    # ------------------------------------------------
    # 12. Return results
    # ------------------------------------------------

    return valid_df, rejected_df
