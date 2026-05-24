"""Generate the main logistics analytics Jupyter notebook."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "logistics_analytics_tracking.ipynb"

CELLS = []

def md(s):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": s.split("\n")})

def code(s):
    CELLS.append(
        {
            "cell_type": "code",
            "metadata": {},
            "source": s.split("\n"),
            "outputs": [],
            "execution_count": None,
        }
    )

md(
    """# Transportation & Logistics Tracking — Enterprise Analytics

**Purpose:** End-to-end analytics for logistics management — route performance, supplier efficiency, material lead times, delay root-cause analysis, and ML-based ETA/delay/risk models.

**Dataset:** `Transportation & Logistics Tracking Dataset.xlsx` (Primary Data + Data Dictionary)

**Audience:** Executives, fleet managers, operations, supply chain analysts."""
)

code(
    """import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

ROOT = Path.cwd()
if not (ROOT / 'src').exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
import plotly.io as pio
from IPython.display import display, Markdown, HTML

from src.data_loader import load_shipments, load_raw, profile_dataset
from src.cleaning import clean_shipments
from src.features import engineer_features
from src.gps import snapshot_gps_summary, preprocess_gps_trajectory
from src import analytics, root_cause, ml_models, viz

pio.renderers.default = 'notebook'
print('Project root:', ROOT)"""
)

md("## 1. Automated Dataset Intelligence")
code(
    """raw, data_dict = load_raw()
display(data_dict.head(15))
ship_raw = load_shipments()
profile = profile_dataset(ship_raw)
display(Markdown('### Column meanings & dtypes'))
display(pd.DataFrame({'column': list(profile['dtypes'].keys()), 'dtype': list(profile['dtypes'].values())}))
display(Markdown('### Missing values (%)'))
display(pd.Series(profile['missing_pct']).sort_values(ascending=False))
display(Markdown('### Shipment lifecycle & GPS behavior'))
display(pd.DataFrame([{
    'gps_mode': profile['gps_tracking_mode'],
    'median_pings_per_booking': profile['gps_pings_per_booking']['50%'],
    'booking_date_range': f"{profile['date_range']['booking_min']} → {profile['date_range']['booking_max']}",
}]).T)
display(Markdown('### Operational workflow (inferred)'))
display(Markdown('''
1. **Booking** (`booking_date`) — contract/spot shipment created  
2. **Dispatch wait** — gap until `trip_start` (loading/planning)  
3. **In-transit** — `trip_start` → `trip_end` (moving time)  
4. **GPS snapshot** — `gps_ping_time` + current coordinates (last known)  
5. **Planned vs actual arrival** — `planned_eta` vs `actual_eta` → `ontime_flag`  
6. **Unloading** — residual after `trip_end` if delivery completes later  
'''))

display(Markdown('### Potential KPIs'))
display(pd.DataFrame({'kpi': profile['potential_kpis']}))
display(Markdown('### Data quality flags'))
display(pd.DataFrame({'flag': profile['data_quality_flags']}))"""
)

md("## 2. Data Cleaning Pipeline")
code(
    """df, qlog = clean_shipments(ship_raw)
df = engineer_features(df)
print('Clean rows:', len(df))
display(qlog)
display(df.head(3))"""
)

md("## 3. Executive KPIs (Power BI Overall Dashboard)")
code(
    """kpis = analytics.executive_kpis(df)
display(HTML(viz.kpi_cards_html(kpis)))
display(kpis)"""
)

md("## 4. GPS Tracking Behavior & Preprocessing")
code(
    """display(snapshot_gps_summary(df))
# Trajectory preprocessor ready for high-frequency GPS feeds
sample_multi = ship_raw[ship_raw.duplicated('Booking ID', keep=False)]
if len(sample_multi):
    pings = sample_multi.rename(columns={
        'Booking ID':'booking_id','Data Ping time':'gps_ping_time',
        'Current Location Latitude':'current_lat','Curren Location Longitude':'current_lon'
    })
    display(preprocess_gps_trajectory(pings).head())
else:
    print('Note: Current file is snapshot GPS (~1 ping/booking). Enterprise deployment needs 30-60s pings for idle/moving decomposition.')"""
)

md("## 5. On-Time Delivery & Delay Analytics")
code(
    """display(analytics.delay_patterns(df).tail(12))
fig = viz.bookings_trend(df)
fig.show()
fig2 = viz.origin_bubble_map(df)
fig2.show()"""
)

md("## 6. Route Performance & Inefficiency")
code(
    """routes = analytics.route_kpis(df, min_bookings=10)
display(routes.head(20).style.background_gradient(subset=['ontime_rate_pct'], cmap='RdYlGn'))
# High delay + high volume routes = priority fixes
priority = routes[(routes['avg_delay_hours']>48) & (routes['total_bookings']>=20)].head(15)
display(Markdown('### Priority routes (high delay + volume)'))
display(priority)"""
)

md("## 7. Supplier Performance — Segmented (Not Overall Average)")
code(
    """sup_overall, sup_segment = analytics.supplier_performance_segmented(df)
display(sup_overall.head(15))
fig = viz.supplier_combo_chart(sup_overall)
fig.show()
# Example RCA for a large supplier
example_sup = sup_overall.iloc[0]['supplier_name']
display(Markdown(f'### Capability gap vs peers: **{example_sup}**'))
display(root_cause.supplier_capability_gap(df, example_sup))"""
)

md("## 8. Customer Shipment Visibility")
code(
    """customers = analytics.segment_performance(df, 'customer_name', min_bookings=20)
display(customers.head(15).style.background_gradient(subset=['ontime_rate_pct'], cmap='RdYlGn'))"""
)

md("## 9. Material / Goods Type vs Delivery Time")
code(
    """mat = analytics.material_lead_time(df)
display(mat.head(20))
import plotly.express as px
px.scatter(mat, x='median_trip_days', y='ontime_rate', size='bookings', hover_name='material_group',
           title='Material: Lead Time vs On-time Rate').show()"""
)

md("## 10. Lead Time Decomposition (Wait / Moving / Unloading / Idle)")
code(
    """display(root_cause.bottleneck_diagnostics(df))
lead = df[['booking_id','wait_hours','moving_hours','unloading_hours','idle_days_proxy','delay_hours']].describe()
display(lead)"""
)

md("## 11. Root-Cause Analysis (Multivariate — Not Correlation Only)")
code(
    """delay_model = root_cause.delay_driver_model(df)
display(Markdown(f"Delay model MAE: **{delay_model['test_mae_hours']} hours**"))
display(delay_model['top_drivers'])
late_model = root_cause.late_risk_classifier(df)
display(Markdown(f"Late-risk classifier AUC: **{late_model['test_auc']}**"))
display(late_model['top_risk_drivers'])
display(Markdown(delay_model['interpretation_note']))"""
)

md("## 12. Fleet, Driver & Vehicle Segmentation")
code(
    """display(analytics.fleet_utilization_proxy(df).head(12))
display(analytics.driver_scorecard(df).head(12))
# Vehicle type × distance band
seg_vt = analytics.segment_performance(df, ['vehicle_type','distance_band'], min_bookings=5)
display(seg_vt.head(20))"""
)

md("## 13. Machine Learning Models")
code(
    """eta = ml_models.train_eta_model(df)
delay_clf = ml_models.train_delay_classifier(df)
df['risk_score'] = ml_models.shipment_risk_score(df, delay_clf)
anomalies = ml_models.route_anomaly_detection(df)
forecast = ml_models.forecast_monthly_volume(df)

display(Markdown(f"**ETA (trip days) MAE:** {eta['test_mae_days']} "))
display(Markdown(f"**Delay classifier AUC:** {delay_clf['test_auc']}"))
display(df[['booking_id','supplier_name','route_id','risk_score','is_late']].sort_values('risk_score', ascending=False).head(15))
display(Markdown('### Route anomalies'))
display(anomalies[anomalies['is_anomaly']].head(10))
display(Markdown('### Volume forecast (next 3 months)'))
display(forecast)"""
)

md("## 14. Management Recommendations — Logistics Transformation Roadmap")
code(
    """from src.recommendations import generate_management_recommendations, recommendations_markdown_table

mgmt_recs = generate_management_recommendations(df, delay_model=delay_model)
display(mgmt_recs)  # structured initiative register
display(Markdown(recommendations_markdown_table(mgmt_recs)))"""
)

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
    },
    "cells": CELLS,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("Wrote", OUT)
