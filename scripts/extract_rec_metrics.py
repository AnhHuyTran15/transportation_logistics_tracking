import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.data_loader import load_shipments
from src.cleaning import clean_shipments
from src.features import engineer_features
from src import analytics, root_cause

df = engineer_features(clean_shipments(load_shipments())[0])
k = analytics.executive_kpis(df)
routes = analytics.route_kpis(df, min_bookings=20)
sup_overall, _ = analytics.supplier_performance_segmented(df, min_n=40)
customers = analytics.segment_performance(df, "customer_name", min_bookings=30)
materials = analytics.material_lead_time(df)
monthly = analytics.delay_patterns(df)

bad_routes = routes.nsmallest(5, "ontime_rate_pct")
worst_sup = sup_overall.nsmallest(5, "ontime_rate_pct")
lt = customers[customers["customer_name"].str.contains("Larsen", case=False, na=False)]
auto = materials[materials["material_group"] == "Auto Parts"]

out = {
    "kpis": k.to_dict(),
    "bad_routes": bad_routes[
        ["route_id", "total_bookings", "ontime_rate_pct", "avg_delay_hours"]
    ].to_dict("records"),
    "worst_suppliers": worst_sup[
        ["supplier_name", "total_bookings", "ontime_rate_pct", "avg_delay_hours"]
    ].to_dict("records"),
    "larsen_toubro": lt.iloc[0].to_dict() if len(lt) else {},
    "auto_parts": auto.iloc[0].to_dict() if len(auto) else {},
    "peak_month": monthly.loc[monthly["late_rate_pct"].idxmax()].to_dict(),
    "detour_high_ot": float(df[df["route_detour_ratio"] > 1.5]["is_ontime"].mean() * 100),
    "detour_low_ot": float(df[df["route_detour_ratio"] <= 1.2]["is_ontime"].mean() * 100),
    "long_haul_ot": float(df[df["route_category"] == "long_haul"]["is_ontime"].mean() * 100),
    "short_haul_ot": float(df[df["route_category"] == "short_haul"]["is_ontime"].mean() * 100),
    "market_ot": float(df[df["shipment_type"] == "Market"]["is_ontime"].mean() * 100),
    "regular_ot": float(df[df["shipment_type"] == "Regular"]["is_ontime"].mean() * 100),
}
for key, val in out.items():
    print(f"---{key}---")
    print(val)
