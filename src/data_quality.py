"""Reusable data-quality checks used before publishing curated data."""

import pandas as pd


def validate_orders(df: pd.DataFrame) -> dict:
    checks = {
        "row_count_positive": len(df) > 0,
        "order_id_not_null": df["order_id"].notna().all(),
        "order_id_unique": df["order_id"].is_unique,
        "amount_non_negative": (df["amount"] >= 0).all(),
        "order_date_valid": df["order_date"].notna().all(),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"Data-quality checks failed: {failed}")
    return checks
