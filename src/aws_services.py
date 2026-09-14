"""Thin AWS integration adapters used by the Airflow DAG."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import boto3


def upload_to_s3(local_path: str, bucket: str, key: str) -> str:
    if not Path(local_path).is_file():
        raise FileNotFoundError(local_path)
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    s3.upload_file(local_path, bucket, key)
    return f"s3://{bucket}/{key}"


def start_glue_job(job_name: str, source_path: str, target_path: str) -> str:
    glue = boto3.client("glue", region_name=os.getenv("AWS_REGION"))
    response = glue.start_job_run(
        JobName=job_name,
        Arguments={"--SOURCE_PATH": source_path, "--TARGET_PATH": target_path},
    )
    return response["JobRunId"]


def wait_for_glue_job(
    job_name: str,
    run_id: str,
    poll_seconds: int = 15,
    timeout_seconds: int = 3600,
    *,
    client: Any | None = None,
) -> None:
    """Wait for Glue without allowing an Airflow worker to poll forever."""
    if poll_seconds <= 0 or timeout_seconds <= 0:
        raise ValueError("poll_seconds and timeout_seconds must be positive")

    glue = client or boto3.client("glue", region_name=os.getenv("AWS_REGION"))
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        state = glue.get_job_run(
            JobName=job_name,
            RunId=run_id,
            PredecessorsIncluded=False,
        )["JobRun"]["JobRunState"]
        if state == "SUCCEEDED":
            return
        if state in {"FAILED", "STOPPED", "TIMEOUT", "ERROR"}:
            raise RuntimeError(f"Glue job {job_name} failed with state={state}")
        time.sleep(poll_seconds)

    raise TimeoutError(
        f"Glue job {job_name} run {run_id} exceeded {timeout_seconds} seconds"
    )


def download_from_s3(bucket: str, key: str, local_path: str) -> str:
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    s3.download_file(bucket, key, local_path)
    return local_path
