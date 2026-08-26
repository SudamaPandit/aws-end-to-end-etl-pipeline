from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def extract():
    from src.extract import extract_orders
    extract_orders("/opt/airflow/data/raw/orders.csv")


def transform():
    import pandas as pd
    from src.transform import transform_orders
    df = pd.read_csv("/opt/airflow/data/raw/orders.csv")
    transform_orders(df).to_parquet("/opt/airflow/data/curated/orders.parquet", index=False)


def load():
    # Production deployment replaces this local load with S3/Glue output
    # and a parameterized PostgreSQL COPY/upsert operation.
    from pathlib import Path
    if not Path("/opt/airflow/data/curated/orders.parquet").exists():
        raise FileNotFoundError("Curated dataset was not produced")

with DAG(
    dag_id="aws_end_to_end_etl",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["etl", "aws", "portfolio"],
) as dag:
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    extract_task >> transform_task >> load_task
