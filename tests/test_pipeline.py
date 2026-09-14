import pandas as pd
import pytest

from src.ai_data_quality import build_anomaly_summary, triage_with_ai
from src.aws_services import wait_for_glue_job
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


def test_transform_orders_removes_invalid_amounts_and_dates():
    source = pd.DataFrame([
        {"order_id": 1, "customer_id": 10, "order_date": "bad-date", "amount": 10, "status": "ok"},
        {"order_id": 2, "customer_id": 10, "order_date": "2026-01-01", "amount": -1, "status": "ok"},
    ])
    assert transform_orders(source).empty


def test_missing_columns_raise_error():
    with pytest.raises(ValueError, match="Missing columns"):
        transform_orders(pd.DataFrame({"order_id": [1]}))


@pytest.mark.parametrize("column,value,check", [
    ("status", " ", "status_not_blank"),
    ("amount", "not-a-number", "amount_not_null"),
])
def test_data_quality_rejects_invalid_values(column, value, check):
    bad = transform_orders(valid_orders())
    bad.loc[0, column] = value
    with pytest.raises(ValueError, match=check):
        validate_orders(bad)


def test_data_quality_accepts_valid_dataset():
    result = validate_orders(transform_orders(valid_orders()))
    assert all(result.values())


def test_data_quality_rejects_duplicate_order_ids():
    bad = pd.concat([valid_orders(), valid_orders().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="order_id_unique"):
        validate_orders(bad)


def test_ai_prompt_contains_only_supplied_metrics():
    prompt = build_anomaly_summary({"row_count": 100, "duplicate_rate": 0.02})
    assert "row_count" in prompt and "duplicate_rate" in prompt


def test_ai_triage_is_safe_when_not_configured(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)
    assert "disabled" in triage_with_ai({"row_count": 100})


class FakeGlue:
    def __init__(self, states):
        self.states = iter(states)

    def get_job_run(self, **_):
        return {"JobRun": {"JobRunState": next(self.states)}}


def test_glue_waiter_handles_success(monkeypatch):
    monkeypatch.setattr("src.aws_services.time.sleep", lambda _: None)
    wait_for_glue_job("job", "run", poll_seconds=1, client=FakeGlue(["RUNNING", "SUCCEEDED"]))


def test_glue_waiter_fails_on_terminal_state():
    with pytest.raises(RuntimeError, match="FAILED"):
        wait_for_glue_job("job", "run", client=FakeGlue(["FAILED"]))
