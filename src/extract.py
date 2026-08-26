import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine


def extract_orders(output_path: str) -> str:
    """Extract source orders from PostgreSQL into a raw CSV landing file."""
    database_url = os.environ["SOURCE_DATABASE_URL"]
    query = """
        SELECT order_id, customer_id, order_date, amount, status
        FROM source_orders
        WHERE order_date >= %(start_date)s
          AND order_date < %(end_date)s
        ORDER BY order_id
    """
    params = {
        "start_date": os.environ.get("START_DATE", "2026-01-01"),
        "end_date": os.environ.get("END_DATE", "2027-01-01"),
    }
    engine = create_engine(database_url)
    df = pd.read_sql(query, engine, params=params)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path
