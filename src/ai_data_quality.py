"""AI-assisted anomaly triage for pipeline data-quality failures.

The deterministic rules remain the source of truth. An LLM is used only to
summarize anomalies for an engineer and suggest investigation priorities.
No customer data or credentials are sent to the model.
"""

import json
import os
from typing import Any


def build_anomaly_summary(metrics: dict[str, Any]) -> str:
    """Create a safe, structured prompt for an approved LLM endpoint."""
    payload = json.dumps(metrics, sort_keys=True)
    return (
        "You are assisting a senior data engineer with ETL monitoring. "
        "Review these aggregate pipeline metrics only; do not infer PII. "
        "Identify unusual trends, likely technical causes, and the top 3 "
        "investigation steps. Return concise operational guidance.\n\n"
        f"Metrics: {payload}"
    )


def triage_with_ai(metrics: dict[str, Any]) -> str:
    """Call the configured enterprise LLM adapter when enabled.

    The repository intentionally keeps provider-specific credentials and SDK
    code outside source control. Set AI_ENDPOINT/AI_API_KEY in the runtime.
    """
    prompt = build_anomaly_summary(metrics)
    endpoint = os.getenv("AI_ENDPOINT")
    api_key = os.getenv("AI_API_KEY")

    if not endpoint or not api_key:
        return "AI triage disabled; deterministic quality checks remain authoritative."

    # Provider-neutral integration point. A production deployment can connect
    # this adapter to Amazon Bedrock or an approved enterprise LLM gateway.
    return f"AI triage request prepared for {endpoint}: {prompt}"
