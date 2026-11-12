# Time-Partitioned Data Lake Pipeline

## Overview

A local, reproducible data lake pipeline for e-commerce order events. It ingests CSV sources, validates records, quarantines rejects, transforms valid events and publishes Snappy-compressed Parquet files partitioned by UTC event date.

## Technology

- Python 3.12
- Pandas 3.1.1
- PyArrow 26.0.1
- DuckDB 2.0.0
- Pytest 9.2.0

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Generate synthetic data

```powershell
python -m src.data_generator --rows 1000 --seed 42
```

The generator creates `order_events.csv`, `customers.csv` and `scenario_manifest.json`. For requested counts of at least 10, it adds one duplicate event, so the generated count is one greater than the requested count.

## Run the pipeline

```powershell
python -m src.main
```

Default inputs: `data/raw/order_events.csv` and `data/raw/customers.csv`.

Outputs: `data/processed/`, `data/quarantine/` and `data/reports/`.

Custom inputs:

```powershell
python -m src.main --events path/to/order_events.csv --customers path/to/customers.csv
```

## Pipeline stages

1. Generate reproducible synthetic sources.
2. Ingest CSV files and attach source metadata.
3. Validate required fields, event IDs, customer references, timestamps, event types, statuses and amounts.
4. Quarantine rejected records with reasons and raw records.
5. Normalize timestamps and derive `event_date`.
6. Publish Snappy-compressed Parquet by daily event-date partition.
7. Save metrics and reconcile record counts.

## Partitioning

The partition column is `event_date`, derived from the UTC-normalized event timestamp. Late-arriving events are placed according to event time, not arrival time. Date filters can therefore prune unrelated partitions.

## Idempotency and recovery

The publisher uses `event_id` to ignore repeated event IDs and preserve existing records. It writes to a staging directory and uses backup/restore handling.

**Limitation:** It reads the existing dataset and rewrites the combined dataset on each publish; this is logically idempotent but not append-only incremental publishing.

## Tests

Run:

```powershell
python -m pytest -q
```

The latest recorded test run completed successfully with 35 passing tests in 2.32 seconds. Run the test suite with the command above to verify the current code.

## Benchmark results

Observed local synthetic-data results:

| Metric | 100K | 1M |
|---|---:|---:|
| Input records | 100,001 | 1,000,001 |
| Valid records | 99,995 | 999,995 |
| Rejected records | 6 | 6 |
| Published records | 99,995 | 999,995 |
| Daily partitions / files | 92 / 92 | 92 / 92 |
| Parquet size | 3.91 MB | 30.06 MB |
| Total runtime | 1.33 s | 10.63 s |
| Reconciliation | Passed | Passed |

The counts include one deliberately added duplicate. Validation was optimized from approximately 69.56 seconds to 0.36 seconds on the same 100K dataset using vectorized Pandas operations. These are local results, not production throughput guarantees.

The configured file-size target is 128 MB. All benchmark files were below that target. The implementation writes one file per date partition and does not implement general-purpose compaction across accumulated batches.

For this benchmark, the total dataset is only about 30 MB, so individual daily partitions remain small. Compaction is documented as future work rather than introducing unnecessary complexity into this prototype.

## DuckDB partition pruning

On the 1M dataset, a query filtering for `2025-12-02` returned one record. DuckDB reported 1 of 92 Parquet files scanned and one row scanned.

## Evidence

Benchmark reports and DuckDB profiles are stored in `evidence/performance_results/`. Supporting documents are in `docs/` and AI usage notes in `ai_usage/`.

## Limitations

- Local prototype using synthetic data.
- Full combined-dataset rewrite on each publish.
- No general-purpose file compaction.
- No distributed processing or cloud object storage integration.
- Input schema drift is detected through strict CSV column-name and column-order checks; automatic schema evolution is not implemented.
- Performance depends on local hardware and workload.