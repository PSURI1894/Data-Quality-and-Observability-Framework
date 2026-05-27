# Data Quality and Observability Framework (Data SRE)

A modular, enterprise-grade Data Site Reliability Engineering (Data SRE) framework that wraps analytical lakehouses and database platforms with configuration-driven validations, end-to-end lineage extraction, data SLO tracking, statistical anomaly detection, and automated on-call incident response.

This repository provides a concrete implementation of **Project 8: Data Quality and Observability Framework** from the Data Engineering Compendium.

---

## 1. System Architecture & Component Design

The framework operates on a decoupled, configuration-driven model that overlays existing batch and streaming ingestion pipelines with verification check gates, OpenLineage emitters, state trackers, and incident bots.

```mermaid
graph TD
    subgraph Data Pipeline Ingestion
        RawAPI[Raw Kafka Payment Stream] -->|1. Ingestion Task| StgTable[(stg_payments)]
        StgTable -->|2. dbt build & test| MartTable[(fact_payment_observability)]
    end

    subgraph OpenLineage & Metadata Store
        StgTable -.->|Lineage Events| Marquez[Marquez Engine]
        MartTable -.->|Lineage Events| Marquez
    end

    subgraph Data Quality Assertion Layer
        dbtRun[dbt Test Suite] -->|3. Elementary Integration| ChecksDB[(Postgres checks_results)]
        geRun[validator.py / GE Checkpoints] -->|4. GE Assertions| ChecksDB
    end

    subgraph SLO Tracker & Incident Automation
        ChecksDB -->|5. rolling 24h checks| SLOTracker[slo_tracker.py]
        SLOTracker -->|Update States| SLOStateDB[(Postgres slo_state)]
        SLOStateDB -->|6. Render Metrics| Grafana[Grafana Dashboard]
        
        SLOStateDB -->|7. SLO Breaches| IncidentBot[incident_bot.py]
        IncidentBot -->|8. Suspect blame lookup| GitRepo[(Git Logs)]
        IncidentBot -->|9. Route alerts| Slack[Slack Channels]
        IncidentBot -->|10. Trigger on-call| PagerDuty[PagerDuty API]
    end

    style Data Pipeline Ingestion fill:#1b1d2e,stroke:#3b405e,stroke-width:2px,color:#fff
    style OpenLineage & Metadata Store fill:#191d0f,stroke:#4a5e26,stroke-width:2px,color:#fff
    style Data Quality Assertion Layer fill:#220f0f,stroke:#5e2626,stroke-width:2px,color:#fff
    style SLO Tracker & Incident Automation fill:#0f2214,stroke:#265e38,stroke-width:2px,color:#fff
```

---

## 2. Pillars of the Observability Framework

### A. Configuration-Driven Check Registry (`registry.yaml`)
We treat data quality assertions as code. Upstream engineers register datasets in a centralized YAML manifest containing structural metrics, ownership information, severity routes, and specific Great Expectations rules. The parser translates these into expectation suites dynamically at runtime.

### B. Runtime Validator (`validator.py`)
Runs validation pipelines. It reads the registry, fetches expectation suites, queries Postgres/lakehouse targets, translates validations intoGreat Expectations RuntimeBatchRequests, runs checkpoints, and pushes check metrics (success rates, failed thresholds, observed counts) into a central database.

### C. Data Lineage Store (`lineage.py`)
Uses the OpenLineage specification standard to hook into Airflow operators and dbt runs. On task status updates, lineage payloads are dispatched to a local Marquez server which visualizes column-level and DAG-level dependency maps.

### D. Data SLO Tracker (`slo_tracker.py`)
A background service computing actual data service levels over sliding windows. Instead of basic alarm thresholds, the tracker processes mathematical SLO states (Healthy, Degraded, Down) and saves updates into Postgres.

### E. Alert Routing & Blame Resolution (`incident_bot.py`)
On SLO breach, the incident responder triggers, routes critical alerts to Slack, queries Git history via `git blame` to identify recent query modifications, pages on-call SREs, and attaches Marquez lineage subgraphs and playbook runbooks.

### F. Statistical Anomaly Detector (`anomaly_detector.py`)
Implements standard Z-scoring alongside Exponentially Weighted Moving Average (EWMA) to identify data volume drops, row-count shifts, and null-rate spikes, avoiding false-alarm triggers on seasonal weekends or holiday cycles.

---

## 3. Database Schema Models

We track SRE observability state inside a central Postgres instance. The database schema holds tables mapping check results, registries, alerts, and SLO statuses:

### `checks_results`
Stores the output of every Great Expectations check or dbt test:
* `run_id` (VARCHAR): Unique pipeline execution ID.
* `dataset_urn` (VARCHAR): Target table representation (e.g. `db.payments.raw_events`).
* `expectation_id` (VARCHAR): Expectation check name (e.g. `expect_column_values_to_not_be_null`).
* `severity` (VARCHAR): Critical, Major, or Minor.
* `status` (VARCHAR): `PASS`, `FAIL`, or `WARN`.
* `observed_value` (TEXT): The value recorded during check runs.
* `threshold` (TEXT): The registered bounds.
* `run_at` (TIMESTAMP): Event completion timestamp.

### `slo_state`
Maintains rolling service level indices:
* `dataset_urn` (VARCHAR): Target table representation.
* `freshness_sla_pct` (DECIMAL): Measured freshness SLA percentage over a 24-hour window.
* `completeness_sla_pct` (DECIMAL): Measured row completeness SLA percentage.
* `validity_sla_pct` (DECIMAL): Percentage of critical validation checks passing.
* `status` (VARCHAR): `Healthy`, `Degraded`, or `Down`.
* `updated_at` (TIMESTAMP): State recalculation timestamp.

---

## 4. Mathematical Specifications

Our Data SLO metrics are calculated over a rolling 24-hour window according to SRE metrics:

### Freshness SLA
Calculated as the percentage of expected updates that occurred within the SLA threshold:
$$\text{Freshness SLA} = \frac{\sum_{t=1}^{N} I(t_{\text{now}} - t_{\text{last\_update}} \le \text{Threshold})}{N} \ge 99.5\%$$
*Where $I()$ is the indicator function, and $N$ represents the samples per day.*

### Completeness SLA
Tracks row completeness across ingestion windows:
$$\text{Completeness SLA} = \frac{\text{Expected Rows} - \text{Missing Rows}}{\text{Expected Rows}} \ge 99.9\%$$

### Validity SLA
Proportion of critical validation checks that passed:
$$\text{Validity SLA} = \frac{\text{Passing Critical Checks}}{\text{Total Critical Checks}} \ge 99.99\%$$

---

## 5. Local Runtime & Development Guide

### Prerequisites
* Docker & Docker Compose
* Python 3.10+
* Git

### Step 1: Spin Up Infrastructure Services
Start the Postgres, Marquez, and Grafana databases in the background:
```bash
docker-compose up -d
```

Verify that all services are online:
```bash
docker-compose ps
```
* **Marquez UI**: Available at [http://localhost:5000](http://localhost:5000)
* **Grafana Portals**: Available at [http://localhost:3000](http://localhost:3000) (User: `admin` / Password: `admin`)
* **Postgres Database**: Available at `localhost:5432`

### Step 2: Configure Local Python Environment
Create a virtual environment and install validation tools:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r dbt/requirements.txt  # Installs pytest, great_expectations, requests, psycopg2
```

### Step 3: Run Validation Tests
Execute local tests to ensure the validation suite passes:
```bash
pytest tests/
```

### Step 4: Run Airflow pipeline DAGs
In your orchestrator, trigger the pipeline:
```bash
airflow dags trigger payment_ingestion_pipeline
```
This automatically runs the Flink/dbt pipelines, registers task lineage nodes in Marquez, and triggers `validator.py` checkpoint logging.

---

## 6. Operational Incident Runbooks

We provide structured runbooks inside the `runbooks/` directory for immediate mitigation of SLO breaches:

* **[Freshness SLA Breach Playbook](file:///runbooks/freshness_sla_breach.md)**: Steps for identifying upstream Airflow blockages, debugging Kafka listener lags, and contact maps for downstream consumers.
* **[Data Validation Failure Playbook](file:///runbooks/data_validation_failure.md)**: Details on tracing anomalies, executing immediate git blame resolutions, and executing rolling table partitions recovery routines.
