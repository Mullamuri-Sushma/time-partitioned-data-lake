
import argparse
import csv
import json
import random

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import RAW_DIR, RANDOM_SEED


# Source event schema
FIELDS = [
    "event_id",
    "order_id",
    "customer_id",
    "event_timestamp",
    "event_type",
    "amount",
    "status",
]


def generate_dataset(
    record_count=1000,
    seed=RANDOM_SEED,
    output_dir=RAW_DIR,
):
    """
    Generate reproducible synthetic order events
    and customer reference data.

    Args:
        record_count: Number of normal event records.
        seed: Random seed for reproducibility.
        output_dir: Directory to save generated files.

    Returns:
        Dictionary containing generation statistics.
    """

    if record_count < 0:
        raise ValueError("record_count cannot be negative")

    rng = random.Random(seed)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------
    # 1. Generate customer reference data
    # ------------------------------------------------

    customers = [
        f"CUST{i:05d}"
        for i in range(1, 501)
    ]

    customer_file = output_dir / "customers.csv"

    with customer_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["customer_id"],
        )

        writer.writeheader()

        for customer_id in customers:
            writer.writerow({
                "customer_id": customer_id
            })

    # ------------------------------------------------
    # 2. Define allowed business values
    # ------------------------------------------------

    event_types = [
        "order_placed",
        "payment_completed",
        "order_shipped",
        "order_delivered",
        "order_cancelled",
    ]

    statuses = [
        "pending",
        "completed",
        "shipped",
        "delivered",
        "cancelled",
    ]

    base_time = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    rows = []

    # ------------------------------------------------
    # 3. Generate normal event records
    # ------------------------------------------------

    for i in range(record_count):

        event_time = base_time + timedelta(
            minutes=rng.randint(
                0,
                60 * 24 * 90,
            )
        )

        row = {
            "event_id": f"EVT{i + 1:08d}",

            "order_id": f"ORD{(i // 3) + 1:07d}",

            "customer_id": rng.choice(customers),

            "event_timestamp": event_time.isoformat(),

            "event_type": rng.choice(event_types),

            "amount": f"{rng.uniform(10, 10000):.2f}",

            "status": rng.choice(statuses),
        }

        rows.append(row)

    # ------------------------------------------------
    # 4. Introduce deliberate data-quality scenarios
    # ------------------------------------------------

    anomaly_manifest = []

    if record_count >= 10:

        # Scenario 1: Duplicate event
        rows.append(rows[0].copy())

        anomaly_manifest.append({
            "scenario": "duplicate_event",
            "event_id": rows[0]["event_id"],
            "expected_issue": "duplicate primary key",
        })

        # Scenario 2: Missing required customer ID
        rows[1]["customer_id"] = ""

        anomaly_manifest.append({
            "scenario": "missing_customer",
            "event_id": rows[1]["event_id"],
            "expected_issue": "missing required field",
        })

        # Scenario 3: Negative transaction amount
        rows[2]["amount"] = "-100.00"

        anomaly_manifest.append({
            "scenario": "negative_amount",
            "event_id": rows[2]["event_id"],
            "expected_issue": "negative transaction amount",
        })

        # Scenario 4: Invalid customer reference
        rows[3]["customer_id"] = "CUST99999"

        anomaly_manifest.append({
            "scenario": "invalid_customer_reference",
            "event_id": rows[3]["event_id"],
            "expected_issue": "unknown customer reference",
        })

        # Scenario 5: Malformed timestamp
        rows[4]["event_timestamp"] = (
            "not-a-valid-timestamp"
        )

        anomaly_manifest.append({
            "scenario": "malformed_timestamp",
            "event_id": rows[4]["event_id"],
            "expected_issue": "invalid timestamp",
        })

        # Scenario 6: Unexpected event type
        rows[5]["event_type"] = "unknown_event"

        anomaly_manifest.append({
            "scenario": "unexpected_event_type",
            "event_id": rows[5]["event_id"],
            "expected_issue": "invalid event type",
        })

        # Scenario 7: Zero amount boundary value
        rows[6]["amount"] = "0.00"

        anomaly_manifest.append({
            "scenario": "zero_amount_boundary",
            "event_id": rows[6]["event_id"],
            "expected_issue": "valid boundary value",
        })

        # Scenario 8: Late-arriving event
        rows[7]["event_timestamp"] = (
            base_time - timedelta(days=30)
        ).isoformat()

        anomaly_manifest.append({
            "scenario": "late_arriving_event",
            "event_id": rows[7]["event_id"],
            "expected_issue": "older event date partition",
        })

        # Scenario 9: Out-of-order event arrival
        rows[8]["event_timestamp"] = (
            base_time + timedelta(days=60)
        ).isoformat()

        anomaly_manifest.append({
            "scenario": "out_of_order_event",
            "event_id": rows[8]["event_id"],
            "expected_issue": "event arrival order differs from event time",
        })

    # ------------------------------------------------
    # 5. Save source event data
    # ------------------------------------------------

    output_file = output_dir / "order_events.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)

    # ------------------------------------------------
    # 6. Save separate anomaly manifest
    # ------------------------------------------------

    manifest_file = (
        output_dir / "scenario_manifest.json"
    )

    with manifest_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            anomaly_manifest,
            file,
            indent=4,
        )

    # ------------------------------------------------
    # 7. Return generation statistics
    # ------------------------------------------------

    result = {
        "requested_records": record_count,

        "generated_records": len(rows),

        "customer_records": len(customers),

        "anomaly_scenarios": len(anomaly_manifest),

        "random_seed": seed,

        "events_file": str(output_file),

        "customer_file": str(customer_file),

        "manifest_file": str(manifest_file),
    }

    print(json.dumps(result, indent=4))

    return result


# ----------------------------------------------------
# 8. Command-line execution
# ----------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate synthetic order event data"
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=1000,
        help="Number of normal event records",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )

    args = parser.parse_args()

    generate_dataset(
        record_count=args.rows,
        seed=args.seed,
    )
