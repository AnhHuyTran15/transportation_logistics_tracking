"""KPI and segmented performance analytics."""
from __future__ import annotations

import pandas as pd


def executive_kpis(df: pd.DataFrame) -> pd.Series:
    """Top-level KPIs aligned with Power BI executive dashboard."""
    valid = df.dropna(subset=["booking_id"])
    return pd.Series(
        {
            "total_bookings": valid["booking_id"].nunique(),
            "ontime_bookings": int(valid["is_ontime"].sum()),
            "ontime_rate_pct": round(valid["is_ontime"].mean() * 100, 2),
            "avg_trip_days": round(valid["trip_days"].mean(), 2),
            "avg_distance_km": round(valid["distance_km"].mean(), 2),
            "avg_delay_hours": round(valid["delay_hours"].mean(), 2),
            "avg_wait_hours": round(valid["wait_hours"].mean(), 2),
        }
    )


def segment_performance(
    df: pd.DataFrame,
    group_col: str,
    min_bookings: int = 10,
) -> pd.DataFrame:
    """Segmented KPI table (supplier, route, material, etc.)."""
    g = (
        df.groupby(group_col, dropna=False)
        .agg(
            total_bookings=("booking_id", "count"),
            ontime_bookings=("is_ontime", "sum"),
            ontime_rate=("is_ontime", "mean"),
            avg_trip_days=("trip_days", "mean"),
            avg_delay_hours=("delay_hours", "mean"),
            avg_distance_km=("distance_km", "mean"),
            avg_wait_hours=("wait_hours", "mean"),
            avg_speed_kmph=("avg_speed_kmph", "mean"),
            avg_idle_days=("idle_days_proxy", "mean"),
        )
        .reset_index()
    )
    g["ontime_rate_pct"] = (g["ontime_rate"] * 100).round(2)
    g = g[g["total_bookings"] >= min_bookings].sort_values(
        "total_bookings", ascending=False
    )
    return g


def supplier_performance_segmented(df: pd.DataFrame, min_n: int = 15) -> pd.DataFrame:
    """
    Supplier scorecard by distance band and vehicle type — avoids overall-average bias.
    """
    keys = ["supplier_name", "distance_band", "vehicle_type"]
    seg = segment_performance(df, group_col=keys[0], min_bookings=min_n)
    detailed = (
        df.groupby(keys, dropna=False, observed=True)
        .agg(
            bookings=("booking_id", "count"),
            ontime_rate=("is_ontime", "mean"),
            avg_delay_h=("delay_hours", "mean"),
            avg_trip_days=("trip_days", "mean"),
        )
        .reset_index()
    )
    detailed = detailed[detailed["bookings"] >= 5]
    detailed["ontime_rate_pct"] = (detailed["ontime_rate"] * 100).round(2)
    overall = seg.rename(columns={"total_bookings": "bookings_overall"})
    return overall, detailed


def route_kpis(df: pd.DataFrame, min_bookings: int = 5) -> pd.DataFrame:
    """Origin-destination route performance."""
    return segment_performance(df, "route_id", min_bookings=min_bookings)


def material_lead_time(df: pd.DataFrame) -> pd.DataFrame:
    """Material vs delivery time with volume context."""
    return (
        df.groupby("material_group")
        .agg(
            bookings=("booking_id", "count"),
            median_trip_days=("trip_days", "median"),
            p90_trip_days=("trip_days", lambda s: s.quantile(0.9)),
            ontime_rate=("is_ontime", "mean"),
            avg_delay_h=("delay_hours", "mean"),
        )
        .reset_index()
        .sort_values("bookings", ascending=False)
    )


def delay_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly delay pattern for operations."""
    monthly = (
        df.groupby("booking_month")
        .agg(
            bookings=("booking_id", "count"),
            late_rate=("is_late", "mean"),
            avg_delay_h=("delay_hours", "mean"),
            avg_wait_h=("wait_hours", "mean"),
            avg_idle_days=("idle_days_proxy", "mean"),
        )
        .reset_index()
    )
    monthly["late_rate_pct"] = (monthly["late_rate"] * 100).round(2)
    return monthly


def fleet_utilization_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """Vehicle utilization proxy from km/day vs contractual min daily km."""
    return (
        df.groupby("vehicle_type")
        .agg(
            trips=("booking_id", "count"),
            avg_km_per_day=("km_per_day", "mean"),
            median_trip_days=("trip_days", "median"),
            ontime_rate=("is_ontime", "mean"),
        )
        .reset_index()
        .sort_values("trips", ascending=False)
    )


def driver_scorecard(df: pd.DataFrame, min_trips: int = 10) -> pd.DataFrame:
    return segment_performance(df, "driver_name", min_bookings=min_trips)
