CREATE DATABASE dq_observability;
\c dq_observability;

CREATE TABLE checks_results (
    run_id VARCHAR(50),
    dataset_urn VARCHAR(255),
    expectation_id VARCHAR(255),
    severity VARCHAR(20),
    status VARCHAR(20),
    observed_value TEXT,
    threshold TEXT,
    run_at TIMESTAMP
);

CREATE TABLE registry (
    dataset_urn VARCHAR(255) PRIMARY KEY,
    owner VARCHAR(100),
    freshness_sla_minutes INT,
    completeness_sla_percent DECIMAL(5,2),
    expectations JSONB
);

CREATE TABLE incidents (
    incident_id SERIAL PRIMARY KEY,
    dataset_urn VARCHAR(255),
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    root_cause TEXT,
    slack_channel VARCHAR(100),
    runbook VARCHAR(255)
);

CREATE TABLE slo_state (
    dataset_urn VARCHAR(255),
    freshness_sla_pct DECIMAL(5,2),
    completeness_sla_pct DECIMAL(5,2),
    validity_sla_pct DECIMAL(5,2),
    status VARCHAR(20),
    updated_at TIMESTAMP
);
