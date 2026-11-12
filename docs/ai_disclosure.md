# AI Usage Disclosure

## Overview
AI tools, including ChatGPT, were used as development assistance to interpret requirements, plan the pipeline, draft and improve code, troubleshoot errors, optimize performance, design tests and prepare documentation.

## Areas of assistance
| Area | Assistance |
|---|---|
| Requirements and architecture | Breaking the assessment into stages and planning a local data lake |
| Data generation | Designing reproducible synthetic records and data-quality scenarios |
| Ingestion and validation | CSV ingestion, schema checks, data-quality checks and quarantine |
| Transformation and partitioning | Timestamp normalization and daily event-date partitions |
| Publishing | Parquet publishing, duplicate handling, staging and recovery |
| Testing | Test-case design and debugging |
| Performance | Vectorized Pandas validation optimization |
| Analytics | DuckDB query and partition-pruning profile |
| Documentation | README, design decisions and data dictionary |

## Candidate review and validation
The implementation was run locally. Validation activities included generating datasets, running the pipeline, checking counts, repeating a run to inspect duplicate handling, running automated tests, executing 100K and 1M benchmarks, comparing validation timings, inspecting DuckDB profiling output and checking reconciliation.

Last reported results: 19 tests passed; 99,995 valid records published in the 100K benchmark; 999,995 in the 1M benchmark; reconciliation passed; DuckDB scanned 1 of 92 files for the tested date query. Re-run tests before submission and update results if they change.

## Responsibility
AI suggestions and code were treated as assistance, not automatically accepted as correct. The candidate is responsible for understanding and explaining the submitted implementation, decisions, results and limitations.

## Limitations
AI assistance was used in drafting and improving parts of the implementation and documentation. The project has not been deployed to a production cloud environment. Benchmarks use synthetic data locally. The publisher rewrites the combined dataset rather than using append-only incremental publishing.
