"""AI-assisted anomaly triage using Amazon Bedrock Converse API.

AI is advisory only. Deterministic data-quality rules remain authoritative,
and only aggregate pipeline metrics are sent to the model.
"""

from __future__ import annotations

import json
import os
from typing import Any

import boto3


def build_anomaly_summary(metrics: dict[str, Any]) -> str:
    payload = json.dumps(metrics, sort_keys=True)
    return (
        "You are assisting a senior data engineer with ETL monitoring. "
        "Review these aggregate pipeline metrics only. Do not infer or request PII. "
        "Identify unusual trends, likely technical causes, and the top 3 "
        "investigation steps. Return concise operational guidance.\n\n"
        f"Metrics: {payload}"
    )


def triage_with_ai(metrics: dict[str, Any]) -> str:
    """Use Bedrock when configured; otherwise return a safe disabled state."""
    region = os.getenv("AWS_REGION")
    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not region or not model_id:
        return "AI triage disabled; deterministic quality checks remain authoritative."

    client = boto3.client("bedrock-runtime", region_name=region)
    response = client.converse(
        modelId=model_id,
        system=[{"text": "You are an ETL operations assistant. Never request or expose PII."}],
        messages=[{"role": "user", "content": [{"text": build_anomaly_summary(metrics)}]}],
        inferenceConfig={"maxTokens": 500, "temperature": 0.1},
    )
    return response["output"]["message"]["content"][0]["text"]
