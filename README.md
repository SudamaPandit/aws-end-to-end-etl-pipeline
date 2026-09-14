# AWS Batch ETL Pipeline

A compact batch pipeline for moving order data from PostgreSQL through S3 and
AWS Glue into a PostgreSQL analytics table. Airflow wires the runtime steps;
the pure pandas transformation and quality rules are unit-tested without cloud
credentials.

## Implemented data flow

1. `src/extract.py` reads a bounded `START_DATE` / `END_DATE` slice from
   PostgreSQL and writes a raw CSV.
2. The Airflow DAG uploads that file to S3 and starts
   `glue/transform_job.py`.
3. Glue casts and cleans fields, removes invalid/duplicate order IDs, and writes
   partitioned Parquet to the curated prefix.
4. `src/load.py` downloads curated Parquet and upserts it into
   `fact_orders`.
5. Optional Bedrock triage receives aggregate S3 object metrics only.

The date window is caller-managed incremental extraction, not CDC and not a
persisted watermark. The reusable pandas quality gate in
`src/data_quality.py` is tested and available for local/pre-publish
validation; the Glue job currently applies equivalent core rules directly.

## Repository map

- `dags/`: Airflow orchestration
- `glue/`: AWS Glue/PySpark transformation
- `src/`: extraction, transformation, quality, load, and AWS adapters
- `sql/`: PostgreSQL schema and analysis queries
- `config/`: non-secret example configuration
- `tests/`: offline unit tests
- `docs/architecture.md`: design notes and production follow-ups

## Run tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Runtime credentials come from environment variables; see `.env.example`.
No credentials or infrastructure state are stored in this repository.

## Current boundaries

- No CDC or durable watermark state
- No quarantine store for rejected Glue rows
- No infrastructure-as-code or Docker environment is included
- The full Airflow/AWS/PostgreSQL path requires external services and is not
  exercised by CI
- Bedrock triage is advisory and disabled unless explicitly configured
