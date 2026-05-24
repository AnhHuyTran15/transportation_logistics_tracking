"""Load and profile transportation & logistics tracking data."""
from __future__ import annotations

import pandas as pd

from .config import COLUMN_MAP, DATA_FILE, DICT_SHEET, PRIMARY_SHEET


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load primary shipment/GPS snapshot data and data dictionary."""
    primary = pd.read_excel(DATA_FILE, sheet_name=PRIMARY_SHEET)
    dictionary = pd.read_excel(DATA_FILE, sheet_name=DICT_SHEET)
    return primary, dictionary


def load_shipments() -> pd.DataFrame:
    """Load primary data with canonical column names."""
    df, _ = load_raw()
    df = df.rename(columns=COLUMN_MAP)
    return df


def profile_dataset(df: pd.DataFrame) -> dict:
    """Automated dataset intelligence report."""
    date_cols = [
        "booking_date",
        "gps_ping_time",
        "planned_eta",
        "actual_eta",
        "trip_start",
        "trip_end",
    ]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    pings_per_booking = df.groupby("booking_id").size()
    lifecycle = {
        "booking_to_trip_start_h": (
            (df["trip_start"] - df["booking_date"]).dt.total_seconds() / 3600
        ),
        "trip_duration_days": (
            (df["trip_end"] - df["trip_start"]).dt.total_seconds() / 86400
        ),
        "planned_vs_actual_delay_h": (
            (df["actual_eta"] - df["planned_eta"]).dt.total_seconds() / 3600
        ),
    }

    report = {
        "row_count": len(df),
        "unique_bookings": df["booking_id"].nunique(),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_pct": (df.isnull().mean() * 100).round(2).to_dict(),
        "gps_pings_per_booking": pings_per_booking.describe().to_dict(),
        "gps_tracking_mode": (
            "snapshot"
            if pings_per_booking.median() <= 1.5
            else "multi_ping_trajectory"
        ),
        "date_range": {
            "booking_min": str(df["booking_date"].min()),
            "booking_max": str(df["booking_date"].max()),
        },
        "ontime_distribution": df["ontime_flag"].value_counts(dropna=False).to_dict(),
        "shipment_types": df["shipment_type"].value_counts().to_dict(),
        "entity_counts": {
            "suppliers": int(df["supplier_name"].nunique()),
            "customers": int(df["customer_name"].nunique()),
            "drivers": int(df["driver_name"].nunique()),
            "vehicles": int(df["vehicle_registration"].nunique()),
            "materials": int(df["material_shipped"].nunique()),
            "routes": int(
                df.groupby(["origin_location", "destination_location"]).ngroups
            ),
        },
        "lifecycle_stats": {
            k: v.describe().to_dict() for k, v in lifecycle.items()
        },
        "potential_kpis": [
            "total_bookings",
            "ontime_bookings",
            "ontime_rate",
            "avg_trip_days",
            "avg_distance_km",
            "avg_delay_hours",
            "avg_wait_hours",
            "fleet_utilization_proxy",
            "supplier_ontime_rate_segmented",
            "route_ontime_rate",
            "material_lead_time",
            "idle_time_ratio",
        ],
        "data_quality_flags": _quality_flags(df, lifecycle),
    }
    return report


def _quality_flags(df: pd.DataFrame, lifecycle: dict) -> list[str]:
    flags = []
    if lifecycle["trip_duration_days"].min() < 0:
        flags.append("negative_trip_duration")
    if (lifecycle["planned_vs_actual_delay_h"].abs() > 24 * 365).any():
        flags.append("extreme_delay_outliers")
    if df["vehicle_type"].isna().mean() > 0.15:
        flags.append("high_vehicle_type_missing")
    if df["distance_km"].isna().mean() > 0.05:
        flags.append("missing_distance")
    if df.groupby("booking_id").size().max() <= 3:
        flags.append(
            "low_frequency_gps: enterprise real-time engine required for trajectory analytics"
        )
    wait = lifecycle["booking_to_trip_start_h"]
    if (wait < -24).sum() > 0:
        flags.append("booking_after_trip_start_anomalies")
    return flags
