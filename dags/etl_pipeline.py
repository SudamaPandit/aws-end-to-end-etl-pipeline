from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.operators.python import PythonOperator


def extract_to_s3():
    from src.extract import extract_orders
    from src.aws_services import upload_to_s3

    local_path = extract_orders("/tmp/orders.csv")
    upload_to_s3(
        local_path,
        os.environ["S3_BUCKET"],
        f"{os.environ.get('S3_RAW_PREFIX', 'raw/orders')}/orders.csv",
    )


def run_glue():
    from src.aws_services import start_glue_job, wait_for_glue_job

    bucket = os.environ["S3_BUCKET"]
    source = f"s3://{bucket}/{os.environ.get('S3_RAW_PREFIX', 'raw/orders')}/orders.csv"
    target = f"s3://{bucket}/{os.environ.get('S3_CURATED_PREFIX', 'curated/orders')}/"
    job_name = os.environ["GLUE_JOB_NAME"]
    run_id = start_glue_job(job_name, source, target)
    wait_for_glue_job(job_name, run_id)


def load_analytics():
    # The production loader reads the curated S3 dataset and upserts it into
    # PostgreSQL. The implementation is intentionally isolated from DAG code.
    from src.load import load_curated_orders
    load_curated_orders()


with DAG(
    dag_id="aws_end_to_end_etl",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["etl", "aws", "portfolio"],
) as dag:
    extract_task = PythonOperator(task_id="extract_to_s3", python_callable=extract_to_s3)
    glue_task = PythonOperator(task_id="transform_with_glue", python_callable=run_glue)
    load_task = PythonOperator(task_id="load_postgres", python_callable=load_analytics)

    extract_task >> glue_task >> load_task
