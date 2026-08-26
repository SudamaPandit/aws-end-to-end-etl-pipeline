"""Deterministic data-quality gates used before publishing curated data."""

from __future__ import annotations

from typing import Any

import pandas as pd

REQUIRED_COLUMNS = {"order_id", "customer_id", "order_date", "amount", "status"}


def validate_orders(df: pd.DataFrame) -> dict[str, Any]:
    """Validate the canonical order dataset and fail closed on bad data."""
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    checks = {
        "row_count_positive": len(df) > 0,
        "order_id_not_null": df["order_id"].notna().all(),
        "order_id_unique": df["order_id"].is_unique,
        "customer_id_not_null": df["customer_id"].notna().all(),
        "amount_not_null": df["amount"].notna().all(),
        "amount_non_negative": (df["amount"] >= 0).all(),
        "order_date_valid": pd.to_datetime(df["order_date"], errors="coerce").notna().all(),
        "status_not_null": df["status"].notna().all(),
    }

    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"Data-quality checks failed: {failed}")

    return checks
