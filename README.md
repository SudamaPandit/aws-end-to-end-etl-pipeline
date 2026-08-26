# AWS End-to-End Data Engineering Platform

A production-oriented batch ETL platform designed to demonstrate the engineering practices expected from a Senior Data Engineer: scalable ingestion, layered data architecture, PySpark transformations, SQL analytics, orchestration, data quality, observability, CI/CD, and responsible AI-assisted operations.

## Architecture

```text
PostgreSQL Source
      │
      │ Incremental extraction
      ▼
Amazon S3 — Raw/Bronze
      │
      │ AWS Glue / PySpark
      ▼
Data Quality + Standardization
      │
      ▼
Amazon S3 — Curated/Silver
      │
      │ Partitioned Parquet
      ▼
PostgreSQL — Analytics/Gold
      │
      ▼
SQL Analytics

Apache Airflow ── orchestration / retries / scheduling / monitoring
GitHub Actions ── CI / automated tests
AI Layer ── anomaly triage from aggregate pipeline metrics
```

## Why this is Senior-Level

The project focuses on engineering decisions rather than simply connecting AWS services:

- Layered Raw → Curated → Analytics architecture.
- Idempotent processing so reruns do not corrupt downstream data.
- Incremental extraction instead of repeatedly moving the complete source dataset.
- S3 as a durable replayable landing zone.
- Parquet + date partitioning for efficient analytical processing.
- PySpark transformations designed for distributed execution.
- PostgreSQL indexes and parameterized SQL for extraction and analytics workloads.
- Explicit data-quality gates for schema, null, duplicate, type, and business-rule validation.
- Airflow dependency management, retries, scheduling, and failure isolation.
- CI with automated unit tests before changes are merged.
- Runtime configuration and secrets separated from source code.

## AI-Assisted ETL Operations

AI is used where it provides practical engineering value rather than being added as a gimmick.

The pipeline can calculate aggregate operational metrics such as:

- Row-count variance versus historical runs
- Null-rate changes
- Duplicate/rejected record counts
- Processing duration changes
- Partition-level anomalies

These metrics can be passed to an approved enterprise LLM endpoint, such as an Amazon Bedrock integration, to generate a concise incident summary and prioritized troubleshooting steps.

The AI component is deliberately advisory. Deterministic data-quality checks remain the production gate, and raw customer data/credentials are not sent to the model. This demonstrates responsible use of AI in a real data-engineering workflow.

See [`docs/architecture.md`](docs/architecture.md) for the detailed design.

## Technology Stack

| Area | Technology |
|---|---|
| Source / Analytics DB | PostgreSQL |
| Storage | Amazon S3 |
| Distributed ETL | AWS Glue, PySpark |
| Orchestration | Apache Airflow |
| Programming | Python |
| Query / Analytics | SQL |
| Testing | Pytest |
| CI/CD | GitHub Actions |
| Containers | Docker |
| AI Operations | Enterprise LLM / Amazon Bedrock integration point |

## Repository Structure

```text
├── dags/                  # Airflow orchestration
├── glue/                  # AWS Glue PySpark jobs
├── src/
│   ├── extract.py        # PostgreSQL incremental extraction
│   ├── transform.py      # Reusable transformations
│   ├── data_quality.py   # Deterministic quality gates
│   └── ai_data_quality.py # AI-assisted anomaly triage
├── sql/
│   ├── schema.sql        # Source and analytics schema
│   └── analytics.sql     # Business analytics queries
├── tests/                 # Automated tests
├── config/                # Non-secret configuration
├── docs/                  # Architecture and design decisions
├── .github/workflows/     # CI pipeline
├── requirements.txt
└── README.md
```

## End-to-End Flow

1. Extract an incremental slice from PostgreSQL.
2. Land the source snapshot in immutable S3 Raw storage.
3. Run AWS Glue/PySpark transformations.
4. Apply deterministic data-quality rules.
5. Publish partitioned Parquet to S3 Curated storage.
6. Load the curated dataset into the PostgreSQL analytics layer.
7. Execute SQL aggregations for downstream reporting/analysis.
8. Airflow orchestrates dependencies, retries, and scheduling.
9. Aggregate pipeline metrics can be sent to the AI triage layer for operational diagnosis.
10. GitHub Actions runs automated tests on code changes.

## Local Validation

```bash
pip install -r requirements.txt
pytest -q
```

Cloud credentials, database passwords, API keys, and environment-specific values are intentionally excluded from Git and supplied at runtime through secure configuration.