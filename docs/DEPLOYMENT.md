# Deployment Plan

## Local / Analytics (Current)
```bash
cd Logistics
pip install -r requirements.txt
jupyter lab notebooks/logistics_analytics_tracking.ipynb
```

## Staging (Kubernetes)
1. Build API image: `docker build -t logistics-api ./api`
2. Apply manifests: `kubectl apply -f infra/k8s/`
3. Run migrations: `flyway migrate` or `psql -f sql/schema.sql`
4. Configure secrets: DB URL, Kafka brokers, Redis, MLflow URI

## Environment Variables
| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection |
| `KAFKA_BOOTSTRAP` | Stream ingest |
| `REDIS_URL` | Live position cache |
| `MLFLOW_TRACKING_URI` | Model registry |
| `S3_BUCKET` | Raw GPS archive |

## CI/CD
- **Lint/Test:** GitHub Actions on PR (`pytest`, `ruff`)
- **Notebook smoke:** `papermill` execute KPI cells
- **Deploy:** ArgoCD to staging → manual promote to prod

## Monitoring
- Ingest lag alert: Kafka consumer offset > 60s
- API SLO: 99% < 300ms for `/position`
- Model drift: weekly PSI on `distance_km`, `wait_hours`

## Disaster Recovery
- RDS multi-AZ; cross-region read replica
- Kafka retention 7d; S3 raw GPS 365d
- RPO 15 min / RTO 4 hr for API tier
