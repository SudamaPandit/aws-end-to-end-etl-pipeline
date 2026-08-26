# Architecture & Production Design

## End-to-end flow

```text
                         ┌──────────────────────┐
                         │     PostgreSQL       │
                         │     Source System    │
                         └──────────┬───────────┘
                                    │ incremental extract
                                    ▼
                         ┌──────────────────────┐
                         │      Amazon S3       │
                         │     Raw / Bronze     │
                         └──────────┬───────────┘
                                    │
                         Airflow starts Glue job
                                    ▼
                         ┌──────────────────────┐
                         │      AWS Glue        │
                         │      PySpark         │
                         │ validation + cleanup │
                         └──────────┬───────────┘
                                    │ partitioned Parquet
                                    ▼
                         ┌──────────────────────┐
                         │      Amazon S3       │
                         │   Curated / Silver   │
                         └──────────┬───────────┘
                                    │
                         idempotent staging/upsert
                                    ▼
                         ┌──────────────────────┐
                         │     PostgreSQL       │
                         │    Analytics / Gold  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                              SQL analytics

   ┌─────────────────────────────────────────────────────────────┐
   │ Apache Airflow                                              │
   │ schedule → extract → Glue → load → AI triage               │
   │ retries / dependency management / operational monitoring    │
   └─────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                         ┌──────────────────────┐
                         │   Amazon Bedrock     │
                         │ AI anomaly triage    │
                         │ aggregate metrics →  │
                         │ investigation advice │
                         └──────────────────────┘
```

## Senior-level engineering decisions

- PostgreSQL is treated as the operational source; S3 provides a durable replayable landing layer.
- Extraction is bounded by a configurable date window so the pipeline does not repeatedly move the complete source dataset.
- Raw objects are retained independently from transformation output, allowing replay without re-querying the source.
- Glue writes Parquet partitioned by `order_year` and `order_month` for efficient analytical reads.
- Data-quality rules are deterministic and fail closed before curated data is considered usable.
- PostgreSQL loading uses a staging table followed by `ON CONFLICT` upserts, making reruns idempotent.
- Airflow owns orchestration, dependencies, retries, and scheduling; transformation logic stays in Python/Glue modules.
- AWS integration is isolated in thin adapters so business logic can be unit tested without cloud credentials.
- Secrets are injected at runtime and `.env` is excluded from Git.
- GitHub Actions validates the Python test suite on every push/PR.
- AI is advisory only. It receives aggregate operational metrics and cannot bypass deterministic data-quality gates.

## AI operational use case

After a successful ETL load, Airflow collects aggregate metrics from the curated S3 prefix, including object count and processed bytes. When configured, `src/ai_data_quality.py` sends those metrics through the Amazon Bedrock Converse API.

The model is instructed to identify unusual trends, likely technical causes, and the top investigation steps. No customer rows, database credentials, or PII are passed to the model.

This keeps AI in a realistic engineering role: reducing time-to-diagnosis while preserving deterministic controls over production data.

## Failure and recovery strategy

1. PostgreSQL extraction fails → Airflow retries the task without starting downstream stages.
2. S3 upload fails → the DAG stops before Glue is triggered.
3. Glue fails → the curated dataset is not treated as a successful pipeline output.
4. PostgreSQL upsert fails → the staging table can be rebuilt and the task rerun safely.
5. AI/Bedrock is unavailable → the ETL data path remains successful because AI is advisory, not a release gate.
