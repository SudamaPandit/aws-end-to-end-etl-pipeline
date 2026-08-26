import pandas as pd


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Clean orders and produce analytics-ready columns."""
    required = {"order_id", "customer_id", "order_date", "amount", "status"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    result = df.copy()
    result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce", format="mixed")
    result["amount"] = pd.to_numeric(result["amount"], errors="coerce")
    result["status"] = result["status"].str.strip().str.upper()
    result = result.dropna(subset=["order_id", "customer_id", "order_date", "amount"])
    result = result[result["amount"] >= 0]
    result["order_year"] = result["order_date"].dt.year
    result["order_month"] = result["order_date"].dt.month
    return result.drop_duplicates(subset=["order_id"])
