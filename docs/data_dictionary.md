# Data Dictionary

## Order events source: `order_events.csv`
Grain: one row per order event. Primary key: `event_id`.

| Column | Format | Meaning | Validation |
|---|---|---|---|
| `event_id` | String | Unique event identifier | Required; duplicates rejected |
| `order_id` | String | Related order identifier | Required; may repeat |
| `customer_id` | String | Related customer | Required; must exist in customer reference data |
| `event_timestamp` | Timestamp string | Time event occurred | Required; must parse |
| `event_type` | String | Order lifecycle event | Required; allowed value |
| `amount` | Decimal-compatible string | Monetary amount | Required; numeric, finite, non-negative |
| `status` | String | Event status | Required; allowed value |

Allowed event types: `order_placed`, `payment_completed`, `order_shipped`, `order_delivered`, `order_cancelled`.

Allowed statuses: `pending`, `completed`, `shipped`, `delivered`, `cancelled`.

Zero amount is valid. Negative, malformed and non-finite amounts are rejected.

## Customer reference: `customers.csv`
Grain: one row per customer. Primary key: `customer_id`.

| Column | Format | Meaning | Validation |
|---|---|---|---|
| `customer_id` | String | Unique customer identifier | Required; must not be empty or duplicated |

An event referencing a customer absent from this dataset is rejected.

## Processed Parquet dataset
Format: Snappy-compressed Parquet. Partition column: `event_date`.

| Column | Expected type / meaning |
|---|---|
| `event_id` | String; unique event identifier |
| `order_id` | String; related order |
| `customer_id` | String; related customer |
| `event_timestamp` | UTC timestamp |
| `event_type` | String; validated event type |
| `amount` | Decimal-compatible value; validated non-negative amount |
| `status` | String; validated status |
| `event_date` | Date derived from UTC event timestamp |
| `source_file` | String; source file name |
| `source_row_number` | Original CSV row number, including header offset |
| `run_id` | Pipeline execution identifier |

Example: `2025-12-02T10:30:00+00:00` becomes `event_date=2025-12-02/`. Late events use event time, not ingestion time.

## Rejected records
CSV files under `data/quarantine/` contain:

| Column | Meaning |
|---|---|
| `source_file` | Source file name |
| `source_row_number` | Original row number |
| `event_id` | Event ID if available |
| `reject_reason` | One or more validation failures |
| `raw_record` | Original record serialized as JSON |

## Run metrics
Reports under `data/reports/` include:

| Metric | Meaning |
|---|---|
| `input_records` | Input event count |
| `valid_records` | Records passing validation |
| `rejected_records` | Records failing validation |
| `batch_records` | Valid records sent to publisher |
| `new_records_added` | Previously unseen event IDs |
| `duplicate_records_ignored` | Incoming duplicate records ignored |
| `total_published_records` | Total records in published dataset |
| `partition_count` | Number of date partitions |
| `file_count` | Number of Parquet files |
| `total_size_bytes` | Total Parquet size |
| `duration_seconds` | Pipeline duration |
| `reconciliation` | Count reconciliation result |
| `status` | Overall run status |

Reconciliation rules:
```text
input_records = valid_records + rejected_records
batch_records = valid_records
new_records_added + duplicate_records_ignored = valid_records
```
