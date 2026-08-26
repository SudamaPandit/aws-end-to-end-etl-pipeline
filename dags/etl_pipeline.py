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
    from src.load import load_curated_orders
    return load_curated_orders()


def ai_triage():
    import boto3
    from src.ai_data_quality import triage_with_ai

    bucket = os.environ["S3_BUCKET"]
    prefix = os.environ.get("S3_CURATED_PREFIX", "curated/orders")
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])
    parquet = [obj for obj in objects if obj["Key"].endswith(".parquet")]
    metrics = {
        "curated_object_count": len(parquet),
        "curated_bytes": sum(obj["Size"] for obj in parquet),
    }
    print(triage_with_ai(metrics))


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
    ai_task = PythonOperator(task_id="ai_anomaly_triage", python_callable=ai_triage)

    extract_task >> glue_task >> load_task >> ai_task
