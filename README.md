# Transportation & Logistics Tracking — Analytics Platform

Enterprise-grade analytics for the **Transportation & Logistics Tracking Dataset**, including a full Jupyter analysis notebook, reusable Python pipelines, SQL schema, and architecture documentation.

## Quick Start

```bash
pip install -r requirements.txt
jupyter lab notebooks/logistics_analytics_tracking.ipynb
```

Place the Excel file in the project root (already included):

`Transportation & Logistics Tracking Dataset.xlsx`

## What’s Included

| Asset | Description |
|-------|-------------|
| [`notebooks/logistics_analytics_tracking.ipynb`](notebooks/logistics_analytics_tracking.ipynb) | Main analysis — EDA, KPIs, RCA, ML, visuals |
| [`src/`](src/) | Cleaning, features, GPS, analytics, ML modules |
| [`sql/schema.sql`](sql/schema.sql) | PostgreSQL/Timescale schema |
| [`docs/`](docs/) | Architecture, API, ERD, dashboards, deployment, phases |

## Key Findings (from automated run)

- **3,582 bookings** (Apr 2019 – Dec 2020)
- **38.5% on-time rate** (matches Power BI ~38.52%)
- **Snapshot GPS** (~1 ping/booking) — continuous tracking needed for idle/moving analytics
- **Primary delay drivers** (multivariate): wait time, route detour, distance band — not distance alone

## Regenerate Notebook

```bash
python scripts/build_notebook.py
```

## ML Models (notebook section 13)

- ETA (trip days) — Gradient Boosting
- Delay classification — LightGBM / RandomForest
- Shipment risk score (0–100)
- Route anomaly detection — IsolationForest
- Monthly volume forecast — exponential smoothing

## Publish to GitHub

The repo is initialized locally on branch `main`. One-time login, then publish:

```powershell
gh auth login
cd "c:\Users\Huypz\OneDrive\Documents\Logistics"
.\scripts\publish_github.ps1
```

Or create the repo on [github.com/new](https://github.com/new), then:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/logistics-analytics-tracking.git
git push -u origin main
```

## Documentation Index

- [Architecture](docs/ARCHITECTURE.md)
- [Database ERD](docs/DATABASE_ERD.md)
- [API Spec](docs/API_SPEC.md)
- [Dashboards](docs/DASHBOARDS.md)
- [Implementation Phases](docs/IMPLEMENTATION_PHASES.md)
- [Deployment](docs/DEPLOYMENT.md)
