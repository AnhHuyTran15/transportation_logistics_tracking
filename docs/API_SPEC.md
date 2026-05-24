# Logistics Tracking API (REST)

Base URL: `https://api.logistics.example.com/v1`

## Authentication
`Authorization: Bearer <JWT>`

## Endpoints

### Shipments
| Method | Path | Description |
|--------|------|-------------|
| GET | `/shipments` | List shipments (filters: customer, supplier, status, date) |
| GET | `/shipments/{booking_id}` | Shipment detail + lifecycle timestamps |
| POST | `/shipments` | Create booking (TMS integration) |
| PATCH | `/shipments/{booking_id}` | Update planned ETA, status |

### GPS
| Method | Path | Description |
|--------|------|-------------|
| POST | `/shipments/{booking_id}/pings` | Ingest single GPS ping |
| POST | `/pings/bulk` | Bulk ingest (max 1000/request) |
| GET | `/shipments/{booking_id}/track` | Ping history + polyline |
| GET | `/shipments/{booking_id}/position` | Latest position (Redis-backed) |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/kpis` | Executive KPIs (scoped by date/filters) |
| GET | `/analytics/routes` | Route scorecard |
| GET | `/analytics/suppliers` | Segmented supplier performance |
| GET | `/analytics/suppliers/{id}/capability-gap` | Peer-adjusted gap analysis |

### ML
| Method | Path | Description |
|--------|------|-------------|
| GET | `/predictions/{booking_id}/eta` | Predicted arrival |
| GET | `/predictions/{booking_id}/risk` | Late delivery probability & risk score |
| POST | `/predictions/batch-score` | Batch scoring for active fleet |

### Alerts
| Method | Path | Description |
|--------|------|-------------|
| GET | `/alerts` | Active delay/geofence/idle alerts |
| POST | `/alerts/rules` | Configure thresholds |

## Example: Ingest GPS Ping

```json
POST /v1/shipments/BK-10293/pings
{
  "ping_ts": "2026-05-24T14:32:11Z",
  "latitude": 19.0760,
  "longitude": 72.8777,
  "speed_kmph": 42.5,
  "heading_deg": 180,
  "gps_provider": "Consent Track"
}
```

## Example: ETA Prediction Response

```json
{
  "booking_id": "BK-10293",
  "planned_eta": "2026-05-25T08:00:00Z",
  "predicted_eta": "2026-05-25T11:42:00Z",
  "late_probability": 0.78,
  "risk_score": 78.2,
  "model_version": "delay_lgbm_v3"
}
```
