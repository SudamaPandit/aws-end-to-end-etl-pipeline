"""Deterministic data-quality gates for the canonical orders dataset."""

from __future__ import annotations

from typing import Any

import pandas as pd

REQUIRED_COLUMNS = {"order_id", "customer_id", "order_date", "amount", "status"}


def validate_orders(df: pd.DataFrame) -> dict[str, Any]:
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    amount = pd.to_numeric(df["amount"], errors="coerce")
    order_date = pd.to_datetime(df["order_date"], errors="coerce")
    status = df["status"].astype("string").str.strip()
    checks = {
        "row_count_positive": len(df) > 0,
        "order_id_not_null": df["order_id"].notna().all(),
        "order_id_unique": df["order_id"].is_unique,
        "customer_id_not_null": df["customer_id"].notna().all(),
        "amount_not_null": amount.notna().all(),
        "amount_non_negative": (amount >= 0).all(),
        "order_date_valid": order_date.notna().all(),
        "status_not_blank": status.notna().all() and status.ne("").all(),
    }
    failed = [name for name, passed in checks.items() if not bool(passed)]
    if failed:
        raise ValueError(f"Data-quality checks failed: {failed}")
    return checks
