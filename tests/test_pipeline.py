import pandas as pd
import pytest

from src.transform import transform_orders


def test_transform_orders_cleans_and_derives_fields():
    source = pd.DataFrame([
        {"order_id": 1, "customer_id": 10, "order_date": "2026-01-15", "amount": "100.50", "status": " completed "},
        {"order_id": 1, "customer_id": 10, "order_date": "2026-01-15", "amount": "100.50", "status": "completed"},
    ])
    result = transform_orders(source)
    assert len(result) == 1
    assert result.iloc[0]["status"] == "COMPLETED"
    assert result.iloc[0]["order_year"] == 2026


def test_negative_amount_is_rejected():
    source = pd.DataFrame([
        {"order_id": 1, "customer_id": 10, "order_date": "2026-01-15", "amount": -1, "status": "completed"},
    ])
    assert transform_orders(source).empty


def test_missing_columns_raise_error():
    with pytest.raises(ValueError):
        transform_orders(pd.DataFrame({"order_id": [1]}))
