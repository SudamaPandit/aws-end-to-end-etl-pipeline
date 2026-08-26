import pandas as pd
import pytest

from src.ai_data_quality import build_anomaly_summary, triage_with_ai
from src.data_quality import validate_orders
from src.transform import transform_orders


def valid_orders():
    return pd.DataFrame([
        {"order_id": 1, "customer_id": 10, "order_date": "2026-01-15", "amount": "100.50", "status": " completed "},
        {"order_id": 2, "customer_id": 11, "order_date": "2026-02-20", "amount": "25.00", "status": "shipped"},
    ])


def test_transform_orders_cleans_and_derives_fields():
    source = pd.concat([valid_orders(), valid_orders().iloc[[0]]], ignore_index=True)
    result = transform_orders(source)
    assert len(result) == 2
    assert result.iloc[0]["status"] == "COMPLETED"
    assert result.iloc[0]["order_year"] == 2026
    assert result.iloc[0]["order_month"] == 1


def test_transform_orders_removes_invalid_amounts_and_dates():
    source = pd.DataFrame([
        {"order_id": 1, "customer_id": 10, "order_date": "bad-date", "amount": 10, "status": "ok"},
        {"order_id": 2, "customer_id": 10, "order_date": "2026-01-01", "amount": -1, "status": "ok"},
    ])
    assert transform_orders(source).empty


def test_missing_columns_raise_error():
    with pytest.raises(ValueError, match="Missing columns"):
        transform_orders(pd.DataFrame({"order_id": [1]}))


def test_data_quality_accepts_valid_dataset():
    result = validate_orders(transform_orders(valid_orders()))
    assert result["row_count_positive"] is True
    assert all(result.values())


def test_data_quality_rejects_duplicate_order_ids():
    bad = pd.concat([valid_orders(), valid_orders().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="order_id_unique"):
        validate_orders(bad)


def test_data_quality_rejects_missing_required_column():
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_orders(pd.DataFrame({"order_id": [1]}))


def test_ai_prompt_contains_only_supplied_metrics():
    prompt = build_anomaly_summary({"row_count": 100, "duplicate_rate": 0.02})
    assert "row_count" in prompt
    assert "duplicate_rate" in prompt
    assert "100" in prompt


def test_ai_triage_is_safe_when_not_configured(monkeypatch):
    monkeypatch.delenv("AI_ENDPOINT", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    result = triage_with_ai({"row_count": 100})
    assert "disabled" in result
