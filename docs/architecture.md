# Architecture & Production Design

## Flow

```text
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │  Source System   │
                    └────────┬─────────┘
                             │ incremental extract
                             ▼
                    ┌──────────────────┐
                    │   Amazon S3      │
                    │   Raw / Bronze   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    AWS Glue      │
                    │ PySpark Transform│
                    └────────┬─────────┘
                             │ data quality
                             ▼
                    ┌──────────────────┐
                    │   Amazon S3      │
                    │ Curated / Silver │
                    │  Parquet + parts │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │ Analytics / Gold │
                    └──────────────────┘

              ┌───────────────────────────────┐
              │ Apache Airflow                │
              │ schedule / retries / SLA /   │
              │ dependency / alerting        │
              └──────────────┬────────────────┘
                             │
              ┌──────────────▼────────────────┐
              │ AI-assisted anomaly triage    │
              │ aggregate metrics → LLM       │
              │ investigation recommendations │
              └───────────────────────────────┘
```

## Senior-level engineering decisions

- PostgreSQL is treated as an operational source; S3 is the durable landing layer.
- Raw objects are immutable so failed transformations can be replayed without re-querying the source.
- Curated data is stored as Parquet and partitioned by business date for efficient downstream reads.
- Transformations are idempotent and include duplicate, null, type, and domain validation.
- Airflow owns orchestration rather than business transformation logic.
- Retries use bounded backoff; failed tasks are isolated so the pipeline can be rerun safely.
- SQL is parameterized and indexed around the primary extraction and analytics access paths.
- Secrets are injected through runtime environment/secret management rather than committed to Git.
- CI executes unit tests before code is merged.
- AI is advisory only: deterministic data-quality rules remain the release gate. The AI component receives aggregate metrics rather than raw customer records.

## AI use case

The pipeline calculates aggregate quality metrics such as row-count variance, null-rate changes, duplicate counts, and rejected-record counts. These metrics can be sent to an approved enterprise LLM endpoint (for example, Amazon Bedrock through a controlled runtime integration) to produce an incident summary and prioritized investigation steps.

This demonstrates practical AI augmentation without allowing an LLM to silently modify production data or bypass deterministic validation.
