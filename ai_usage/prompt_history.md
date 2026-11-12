# AI Prompt History

## Tool
ChatGPT — used for development assistance, debugging, optimization, testing guidance and documentation.

## Categorized prompt/request summary
These are summaries, not verbatim transcripts.

| No. | Stage | Prompt/request summary |
|---:|---|---|
| 1 | Requirements | Explain the data engineering assessment and break it into implementation stages. |
| 2 | Setup | Guide creation of the Python project structure and virtual environment. |
| 3 | Technology | Select free tools for CSV, Parquet, analytics and tests. |
| 4 | Data generation | Create reproducible synthetic order events, customer references and quality scenarios. |
| 5 | Ingestion | Implement CSV ingestion with schema checks and source metadata. |
| 6 | Validation | Implement required-field, duplicate, customer, timestamp, event type, status and amount checks. |
| 7 | Quarantine | Save rejects with reasons and original source details. |
| 8 | Transformation | Normalize timestamps and derive event date. |
| 9 | Partitioning | Implement daily event-date partition paths. |
| 10 | Publishing | Implement Parquet publishing, duplicate handling and safe output replacement. |
| 11 | Idempotency | Verify repeated processing does not add duplicate event IDs. |
| 12 | Recovery | Investigate publishing failures and improve staging, backup and recovery. |
| 13 | Testing | Create and debug ingestion, validation and publishing tests. |
| 14 | Optimization | Replace slow row-by-row validation with vectorized Pandas operations. |
| 15 | Benchmarking | Measure 100K and 1M synthetic datasets. |
| 16 | Partition pruning | Use DuckDB profiling to verify date-filtered scans. |
| 17 | Documentation | Prepare README, design, data dictionary and AI disclosure. |

## Important note
These are categorized summaries, not exact copies of every prompt. Preserve the original prompts from the relevant ChatGPT conversations as well. Do not represent this summary as a complete verbatim prompt history.

## Candidate review
AI suggestions were checked through local execution, tests, benchmark comparisons, output inspection and reconciliation. The candidate remains responsible for understanding and explaining the submitted implementation.
