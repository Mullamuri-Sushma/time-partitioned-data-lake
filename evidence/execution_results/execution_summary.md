# Pipeline Execution Summary



## Environment



- Python: 3.12

- Operating system: Windows

- Execution mode: Local



## Pipeline Verification



The pipeline was executed using reproducible synthetic e-commerce order event data.



The execution included:

- CSV ingestion

- Schema and data-quality validation

- Rejected-record quarantine

- Timestamp normalization

- Daily event-date partitioning

- Snappy-compressed Parquet publishing

- Run metrics and reconciliation



## Automated Tests



Latest reported test result: 35 tests passed in 2.32 seconds.



## Benchmark Verification



| Metric | 100K Dataset | 1M Dataset |

|---|---:|---:|

| Input records | 100,001 | 1,000,001 |

| Valid records | 99,995 | 999,995 |

| Rejected records | 6 | 6 |

| Published records | 99,995 | 999,995 |

| Partitions | 92 | 92 |

| Reconciliation | Passed | Passed |



## Partition Pruning



DuckDB profiling verified that a date-filtered query scanned 1 of 92 Parquet files on the 1M dataset.



## Evidence Location



Detailed benchmark reports, profiling outputs and benchmark scripts are available in `evidence/performance_results/`.



## Notes



These results were obtained locally using synthetic data. They are not production performance guarantees.


