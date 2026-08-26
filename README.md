# AWS End-to-End ETL Pipeline

Corporate-style batch ETL pipeline demonstrating SQL, Python, PostgreSQL, Amazon S3, AWS Glue, Apache Airflow, data quality, and CI/CD.

## Architecture

PostgreSQL → S3 (Raw) → AWS Glue (PySpark) → S3 (Curated) → PostgreSQL (Analytics)
                                      ↑
                                Airflow orchestration

GitHub Actions runs tests and validation on every pull request.

## Technologies

- Python / PySpark
- PostgreSQL / SQL
- Amazon S3
- AWS Glue
- Apache Airflow
- Docker
- GitHub Actions

## Pipeline

1. Extract source data from PostgreSQL.
2. Land immutable raw data in S3.
3. Transform and validate data with AWS Glue/PySpark.
4. Write partitioned curated data to S3.
5. Load analytics-ready data into PostgreSQL.
6. Orchestrate the workflow with Airflow.
7. Run automated Python/SQL tests through CI.

## Project Structure

```text
aws-end-to-end-etl-pipeline/
├── dags/
│   └── etl_pipeline.py
├── src/
│   ├── extract.py
│   ├── transform.py
│   └── load.py
├── glue/
│   └── transform_job.py
├── sql/
│   ├── schema.sql
│   └── analytics.sql
├── tests/
│   └── test_pipeline.py
├── config/
│   └── pipeline_config.yaml
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Key Engineering Practices

- Idempotent pipeline design
- Incremental processing
- S3 raw/curated separation
- Partitioned datasets
- Data-quality checks
- Parameterized SQL
- Environment-based configuration
- Retry and failure handling in Airflow
- Automated tests and CI

## Local Development

```bash
docker compose up -d
pip install -r requirements.txt
pytest
```

AWS credentials and infrastructure-specific values are supplied through environment variables and are never committed to the repository.
