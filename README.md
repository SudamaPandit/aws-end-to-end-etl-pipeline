# AWS Batch ETL Pipeline

A layered batch ETL platform: Postgres >>> S3 (raw) >>> Glue/PySpark >>> S3
(curated) >>> Postgres (analytics), orchestrated by Airflow. This is the
"classic" pipeline in my portfolio - no streaming, no ML - built to show
the fundamentals done correctly: idempotency, incremental extraction,
data-quality gates, and a layout that survives someone else maintaining it.

## Design decisions worth explaining

**Incremental, not full-reload.** Extraction pulls only the changed slice
from Postgres using a watermark column, not the whole table every run.
At real data volumes, "just reload everything nightly" stops being viable
fast, and I wanted the pattern in place even at small scale.

**Idempotent by construction.** Re-running a given day's job produces the
same curated output, not duplicates. This matters more than it sounds -
Airflow retries will re-run failed tasks, and if a job isn't idempotent,
a transient failure turns into a data-quality incident instead of a
non-event.

**Raw is immutable.** Once something lands in S3 raw, nothing downstream
mutates it. If a transformation bug ships, I can replay from raw instead
of re-extracting from the source system (which may not even have the
history anymore).

**Quality gates are explicit, not implicit.** `data_quality.py` checks
schema, nulls, duplicates, types, and a handful of business rules
*before* data is allowed into the curated layer - bad data gets rejected
and logged, not silently propagated.

## Architecture

```
Postgres (source)
      │ incremental extract (watermark-based)
      ▼
S3 - raw / immutable
      │ Glue / PySpark
      ▼
Data quality gate
      │
      ▼
S3 - curated (partitioned Parquet)
      │
      ▼
Postgres - analytics layer
      │
      ▼
SQL analytics / reporting

Airflow: scheduling, retries, dependency management, failure isolation
GitHub Actions: CI on every change
```
<img width="1672" height="941" alt="AWS End-to-End ETL Pipeline" src="https://github.com/user-attachments/assets/4029e455-8f3f-4474-bdde-c8f6862644f9" />

## Repository structure

```
dags/                      Airflow DAG
glue/                      the PySpark job as Glue runs it
src/
  extract.py               incremental Postgres extraction
  transform.py             reusable transform logic
  data_quality.py          the quality gate
  ai_data_quality.py       optional AI-assisted anomaly triage (see below)
sql/schema.sql, analytics.sql
tests/                     unit tests, no live infra required
config/                    non-secret runtime config
docs/architecture.md       longer-form design notes
```

## Running the tests

```bash
pip install -r requirements.txt
pytest -q
```

No database, no AWS credentials, no live Airflow needed - the extraction
and transform logic is tested against fixtures, and anything that talks
to real infrastructure is behind an interface I can substitute in tests.

## The AI-assisted piece, and why it's scoped the way it is

`ai_data_quality.py` can take *aggregate* run metrics - row-count
variance vs. history, null-rate shifts, duplicate counts, runtime
deltas - and ask an LLM (Bedrock in the reference design) to draft a
plain-English incident summary and a starting list of things to check.
It never sees raw records. It's not in the critical path: the actual
pass/fail decision is made by the deterministic checks in
`data_quality.py`, before this ever runs. I built it this way on purpose
- I've seen "AI does data quality" pitched as if the model itself is the
gate, and I think that's the wrong place to put non-determinism.

## What running this actually cost me

I didn't run this as a permanently-live pipeline - there's no reason to
keep Glue or a Redshift-class warehouse running 24/7 for a project with
no real traffic. In practice:

- Postgres, Airflow, and the extract/transform logic were developed and
  exercised locally via Docker Compose - this is where 90% of the
  iteration happened.
- The actual AWS Glue job was run a small number of times against S3
  (which has a generous free tier) to validate it against real Glue
  semantics and capture logs for this README - on the order of a few
  hundred rupees total, not a recurring cost.
- The "analytics" layer uses Postgres rather than Redshift; the pattern
  (layered warehouse, SQL analytics on curated data) is the same, and I'd
  rather be upfront that I subbed in Postgres than claim a Redshift
  cluster I wasn't running.

## What I'd change for a real production version

- Extraction currently assumes a single watermark column; CDC
  (Debezium/DMS) would be the real answer once update/delete tracking
  matters, not just inserts.
- No dead-letter/quarantine path for rejected records yet - they're
  logged and dropped. At real scale I'd want them recoverable.
- Terraform provisions the AWS resources but there's no remote state
  backend configured - fine for a solo project, not fine for a team.
