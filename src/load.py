"""Load curated S3 Parquet data into PostgreSQL with an idempotent upsert."""

from __future__ import annotations

import os
from pathlib import Path

import boto3
import pandas as pd
from sqlalchemy import create_engine, text


def load_curated_orders() -> int:
    bucket = os.environ["S3_BUCKET"]
    prefix = os.environ.get("S3_CURATED_PREFIX", "curated/orders")
    database_url = os.environ["TARGET_DATABASE_URL"]
    local_dir = Path("/tmp/curated-orders")
    local_dir.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])
    parquet_objects = [obj for obj in objects if obj["Key"].endswith(".parquet")]
    if not parquet_objects:
        raise FileNotFoundError(f"No curated Parquet objects found under s3://{bucket}/{prefix}")

    frames = []
    for obj in parquet_objects:
        path = local_dir / Path(obj["Key"]).name
        s3.download_file(bucket, obj["Key"], str(path))
        frames.append(pd.read_parquet(path))

    df = pd.concat(frames, ignore_index=True)
    engine = create_engine(database_url)
    staging = "stg_fact_orders"

    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {staging}"))

    df[["order_id", "customer_id", "order_date", "amount", "status", "order_year", "order_month"]].to_sql(
        staging, engine, if_exists="replace", index=False, method="multi"
    )

    upsert_sql = text(f"""
        INSERT INTO fact_orders
            (order_id, customer_id, order_date, amount, status, order_year, order_month)
        SELECT order_id, customer_id, order_date, amount, status, order_year, order_month
        FROM {staging}
        ON CONFLICT (order_id) DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            order_date = EXCLUDED.order_date,
            amount = EXCLUDED.amount,
            status = EXCLUDED.status,
            order_year = EXCLUDED.order_year,
            order_month = EXCLUDED.order_month,
            loaded_at = CURRENT_TIMESTAMP
    """)
    with engine.begin() as conn:
        conn.execute(upsert_sql)
        conn.execute(text(f"DROP TABLE IF EXISTS {staging}"))

    return len(df)
