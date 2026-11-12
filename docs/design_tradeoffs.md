# Design Decisions and Trade-offs

## Architecture
The pipeline is a modular sequence: synthetic CSV sources → ingestion → validation → valid/rejected split → transformation → date partitioning → Parquet publishing → metrics and reconciliation. Each stage is separated into a Python module.

## Data model
The `order_events` grain is one row per order event. `event_id` identifies an event; `order_id` can repeat because an order can have multiple lifecycle events. `customers.csv` supplies customer reference IDs.

## Technology choices
| Technology | Reason |
|---|---|
| Python | Pipeline implementation and orchestration |
| Pandas | CSV processing, vectorized validation and transformation |
| PyArrow | Parquet support |
| Parquet | Columnar analytical storage |
| DuckDB | Query Parquet and inspect partition pruning |
| Pytest | Automated tests |

These tools support local execution without paid cloud infrastructure.

## Partitioning
The output is partitioned by `event_date`, derived from `event_timestamp` after UTC normalization. Daily partitions support date filtering. Late-arriving events use event time rather than arrival time.

On the 1M benchmark, DuckDB scanned 1 of 92 files for the tested date filter, demonstrating partition pruning for that query.

## Validation and quarantine
Checks include required fields, duplicate event IDs, customer references, parseable timestamps, allowed event types and statuses, and finite non-negative amounts. Zero is valid. Rejected rows are saved with source file, source row, event ID, rejection reasons and raw record.

## Performance optimization
The initial row-by-row validation took about 69.56 seconds on the 100K dataset. Vectorized Pandas checks reduced this to about 0.36 seconds on the same dataset.

## Format and file sizing
Parquet with Snappy compression was selected for columnar analytical storage. The configured target file size is 128 MB.

| Metric | 100K | 1M |
|---|---:|---:|
| Files | 92 | 92 |
| Average file size | 0.0425 MB | 0.3268 MB |
| Largest file | 0.0459 MB | 0.3391 MB |
| Files above 128 MB | 0 | 0 |

The current implementation writes one file per date partition. General-purpose compaction across independently accumulated batches is not implemented. Daily partitioning was retained to support date-based pruning.

## Idempotency and recovery
The publisher uses `event_id` to identify existing records. Repeated IDs are ignored and existing records are preserved. On the reported repeated run, 0 new records were added, 995 duplicates were ignored, and 995 records remained published.

Publishing writes to staging, moves existing output to backup, and replaces the output. Recovery logic handles interrupted publishing. Tests cover simulated write failure and interrupted publishing.

**Trade-off:** the publisher rewrites the complete combined dataset on each publish. It supports logical idempotency but is not a true append-only incremental writer; write cost increases with existing dataset size.

## Metrics and reconciliation
Metrics include input, valid and rejected counts; batch, new and duplicate counts; total published records; partition and file counts; output size; duration; reconciliation and status.

Checks:
```text
input_records = valid_records + rejected_records
batch_records = valid_records
new_records_added + duplicate_records_ignored = valid_records
```

## Benchmark observations
| Metric | 100K | 1M |
|---|---:|---:|
| Input | 100,001 | 1,000,001 |
| Valid | 99,995 | 999,995 |
| Rejected | 6 | 6 |
| Published | 99,995 | 999,995 |
| Runtime | 1.33 s | 10.63 s |
| Output size | 3.91 MB | 30.06 MB |
| Partitions | 92 | 92 |

These are local synthetic-data measurements, not guaranteed production throughput.

## Limitations and future work
This is a local prototype. It does not implement append-only incremental publishing, general-purpose compaction, distributed processing or cloud object storage. Future improvements could add these capabilities, monitoring and schema-version management.
