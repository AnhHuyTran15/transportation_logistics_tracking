# Implementation Phases

## Phase 1 — Foundation (Weeks 1–4)
- Ingest historical Excel/CSV into `fact_shipment` (see `sql/schema.sql`)
- Deploy cleaning + feature pipelines (`src/`)
- Jupyter/Power BI parity dashboards (executive KPIs, route & supplier tables)
- Data quality rules (negative trip days, extreme delays)

**Exit criteria:** KPIs match notebook within 1% tolerance; documented column dictionary.

## Phase 2 — Real-Time Tracking (Weeks 5–10)
- Kafka + ingestion API for GPS pings
- TimescaleDB hypertable for `fact_gps_ping`
- Redis last-position cache + WebSocket live map
- Geofence & delay rule engine (stream processing)

**Exit criteria:** p95 ingest-to-map latency < 5s; idle detection on test fleet.

## Phase 3 — Analytics Platform (Weeks 11–16)
- dbt marts: `mv_supplier_segment_kpi`, route/customer scorecards
- Superset/Power BI semantic models
- Scheduled Airflow DAGs

**Exit criteria:** Segmented supplier views used in ops reviews.

## Phase 4 — ML Production (Weeks 17–22)
- Train/register ETA & delay models (MLflow)
- Batch + online scoring → `fact_prediction`
- Route anomaly batch job

**Exit criteria:** Delay model AUC ≥ 0.85 on holdout; ETA MAE within SLA by distance band.

## Phase 5 — Enterprise Hardening (Weeks 23+)
- Multi-tenant auth, audit logs
- DR, autoscaling K8s, cost monitoring
- Customer/supplier portal (read-only visibility)

## Recommended Stack Summary

| Concern | Choice |
|---------|--------|
| Frontend | React, Mapbox, Recharts |
| Backend | FastAPI, Celery workers |
| Database | PostgreSQL + TimescaleDB |
| Stream | Kafka, Flink |
| ML | LightGBM, MLflow, optional Feast |
| Cloud | AWS (EKS, MSK, RDS) or Azure (AKS, Event Hubs, PostgreSQL) |
| IaC | Terraform |
