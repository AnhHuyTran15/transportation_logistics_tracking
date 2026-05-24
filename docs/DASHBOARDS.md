# Dashboard Specifications

Aligned with Power BI examples (Overall Dashboard + Route Analysis).

## Executive Dashboard
- **KPIs:** Total bookings, on-time bookings, on-time %, avg trip days, avg distance
- **Map:** Origin bubble map (size=volume, color=on-time %)
- **Trend:** Monthly booking area chart
- **Table:** Dynamic dimension slicer (customer, supplier, driver, vehicle, material, shipment type)
- **Audience:** C-suite, weekly business review

## Fleet Manager Dashboard
- Vehicle type × distance band utilization
- km/day vs contractual min daily km
- Idle proxy & GPS ping lag
- Driver scorecard (min 10 trips)
- **Audience:** Fleet ops, daily standup

## Operations Dashboard
- Route KPI table (From → To)
- Delay pattern by month
- Bottleneck decomposition (wait / moving / unloading / idle)
- Active alerts (delay, geofence) — requires real-time Phase 2
- **Audience:** Control tower

## Supply Chain Analyst Dashboard
- Material lead time vs on-time scatter
- Supplier combo chart (volume + on-time line)
- Segmented supplier heatmap (distance band × vehicle)
- ML risk score queue
- **Audience:** Network planning, carrier RFPs

## Tooling
| Role | Primary tool |
|------|----------------|
| Executives | Power BI / Superset |
| Analysts | Jupyter + SQL marts |
| Real-time ops | Custom React + Mapbox |
