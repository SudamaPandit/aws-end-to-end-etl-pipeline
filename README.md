# AWS End-to-End Data Engineering Platform

A production-oriented batch ETL platform demonstrating the engineering practices expected from a Senior Data Engineer: incremental ingestion, layered data architecture, distributed PySpark processing, SQL analytics, orchestration, data-quality gates, CI/CD, and responsible AI-assisted operations.

## Architecture

```text
PostgreSQL Source
      │ incremental extraction
      ▼
Amazon S3 — Raw / Bronze
      │
      ▼
AWS Glue — PySpark
      │ validation + standardization
      ▼
Amazon S3 — Curated / Silver
      │ partitioned Parquet
      ▼
PostgreSQL — Analytics / Gold
      │
      ▼
SQL Analytics

Apache Airflow ── scheduling / dependencies / retries
      │
      └── AI anomaly triage ── aggregate metrics → Amazon Bedrock

GitHub Actions ── automated unit tests on every push/PR
```

## Why this is Senior-Level

The project focuses on engineering decisions rather than simply connecting AWS services:

- Incremental extraction using a bounded date window.
- Immutable S3 Raw storage for replayability.
- Curated Parquet partitioned by year/month.
- Distributed transformation with AWS Glue/PySpark.
- Deterministic data-quality gates for schema, nulls, duplicates, types, and business rules.
- Idempotent PostgreSQL loading using a staging table and `ON CONFLICT` upsert.
- Airflow dependency management, retries, scheduling, and failure isolation.
- Thin AWS service adapters keeping cloud integration out of business logic.
- Parameterized SQL and targeted PostgreSQL indexes.
- Automated unit testing through GitHub Actions.
- Runtime configuration and credentials kept outside source control.

## AI-Assisted ETL Operations

AI is integrated as an operational intelligence step rather than a gimmick.

After the ETL load, Airflow collects safe aggregate pipeline metrics such as curated object count and processed bytes. When `AWS_REGION` and `BEDROCK_MODEL_ID` are configured, `src/ai_data_quality.py` sends those aggregate metrics to the Amazon Bedrock Converse API and returns concise troubleshooting guidance.

The AI layer is advisory only. Deterministic data-quality checks remain authoritative, and raw customer records, credentials, and PII are never sent to the model.

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
| AI Operations | Amazon Bedrock |

## Repository Structure

```text
├── dags/                  # Airflow orchestration
├── glue/                  # AWS Glue PySpark job
├── src/
│   ├── extract.py        # PostgreSQL incremental extraction
│   ├── transform.py      # Reusable local transformation logic
│   ├── data_quality.py   # Deterministic quality gates
│   ├── aws_services.py   # S3 + Glue adapters
│   ├── load.py            # S3 Parquet → PostgreSQL upsert
│   └── ai_data_quality.py # Amazon Bedrock anomaly triage
├── sql/                  # Warehouse schema + analytics SQL
├── tests/                # Automated unit tests
├── config/               # Non-secret configuration
├── docs/                 # Architecture and design decisions
├── .github/workflows/    # CI pipeline
├── .env.example          # Safe runtime configuration template
├── .gitignore
├── requirements.txt
└── README.md
```

## End-to-End Flow

1. Airflow starts an incremental PostgreSQL extraction.
2. Python lands the source snapshot in S3 Raw.
3. Airflow starts and monitors the AWS Glue PySpark job.
4. Glue validates, standardizes, deduplicates, and writes partitioned Parquet to S3 Curated.
5. The loader downloads curated Parquet and performs an idempotent PostgreSQL upsert.
6. SQL analytics queries operate on the Gold table.
7. Airflow collects aggregate run metrics and optionally invokes Amazon Bedrock for anomaly triage.
8. GitHub Actions executes automated tests on every push to `main` and pull request.

## Configuration

Copy `.env.example` into your runtime environment and provide real values through your secret manager or environment variables. Never commit `.env` or credentials.

## Local Validation

```bash
pip install -r requirements.txt
pytest -q
```

The unit-test suite is cloud-independent. Running the full AWS workflow requires PostgreSQL, an S3 bucket, an AWS Glue job, Airflow, and appropriate IAM permissions.