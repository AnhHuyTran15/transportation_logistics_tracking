"""Feature engineering: lead-time decomposition and segmentation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DISTANCE_BINS, DISTANCE_LABELS, LONG_HAUL_DISTANCE_KM, URBAN_DISTANCE_KM


def haversine_km(lat1, lon1, lat2, lon2) -> pd.Series:
    """Vectorized haversine distance in km."""
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return pd.Series(2 * r * np.arcsin(np.sqrt(a)))


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build analytical features for RCA and ML."""
    out = df.copy()

    # Lead time decomposition (hours/days)
    out["wait_hours"] = (
        (out["trip_start"] - out["booking_date"]).dt.total_seconds() / 3600
    ).clip(lower=0)
    out["moving_hours"] = (
        (out["trip_end"] - out["trip_start"]).dt.total_seconds() / 3600
    ).clip(lower=0)
    out["delay_hours"] = (
        (out["actual_eta"] - out["planned_eta"]).dt.total_seconds() / 3600
    )
    out["trip_days"] = out["moving_hours"] / 24
    out["is_late"] = (out["delay_hours"] > 0).astype(int)

    # Proxy unloading: residual after moving if actual_eta > trip_end
    out["unloading_hours"] = (
        (out["actual_eta"] - out["trip_end"]).dt.total_seconds() / 3600
    ).clip(lower=0)

    # Speed & efficiency (validated against distance, not assumed causation)
    out["avg_speed_kmph"] = np.where(
        out["moving_hours"] > 0,
        out["distance_km"] / (out["moving_hours"] / 1),
        np.nan,
    )
    out["km_per_day"] = np.where(
        out["trip_days"] > 0, out["distance_km"] / out["trip_days"], np.nan
    )

    # Route complexity
    out["route_id"] = (
        out["origin_location"].astype(str)
        + " → "
        + out["destination_location"].astype(str)
    )
    out["geo_distance_km"] = haversine_km(
        out["origin_lat"],
        out["origin_lon"],
        out["dest_lat"],
        out["dest_lon"],
    )
    out["route_detour_ratio"] = np.where(
        (out["geo_distance_km"] > 0) & out["distance_km"].notna(),
        out["distance_km"] / out["geo_distance_km"],
        np.nan,
    )

    # Segmentation
    out["distance_band"] = pd.cut(
        out["distance_km"],
        bins=DISTANCE_BINS,
        labels=DISTANCE_LABELS,
        include_lowest=True,
    )
    out["route_category"] = np.select(
        [
            out["distance_km"] <= URBAN_DISTANCE_KM,
            out["distance_km"] <= LONG_HAUL_DISTANCE_KM,
        ],
        ["short_haul", "mid_haul"],
        default="long_haul",
    )
    out["booking_month"] = out["booking_date"].dt.to_period("M").astype(str)
    out["booking_dow"] = out["booking_date"].dt.day_name()

    # Material grouping (top N + Other)
    top_materials = out["material_shipped"].value_counts().head(15).index
    out["material_group"] = out["material_shipped"].where(
        out["material_shipped"].isin(top_materials), "Other"
    )

    # Supplier specialization proxy: dominant distance band per supplier
    supplier_mode_band = (
        out.groupby("supplier_name")["distance_band"]
        .agg(lambda s: s.mode().iloc[0] if len(s.dropna()) and len(s.mode()) else np.nan)
    )
    out["supplier_specialization"] = out["supplier_name"].map(supplier_mode_band)

    # Customer type proxy by volume tier
    cust_vol = out["customer_name"].value_counts()
    out["customer_tier"] = out["customer_name"].map(
        lambda c: "enterprise"
        if cust_vol.get(c, 0) >= 200
        else ("mid_market" if cust_vol.get(c, 0) >= 50 else "long_tail")
    )

    # Idle time proxy: gap between min daily km target pace vs actual
    out["expected_days"] = np.where(
        (out["min_daily_km"] > 0) & out["distance_km"].notna(),
        out["distance_km"] / out["min_daily_km"],
        np.nan,
    )
    out["idle_days_proxy"] = (out["trip_days"] - out["expected_days"]).clip(lower=0)

    # GPS snapshot features
    out["gps_ping_lag_hours"] = (
        (out["gps_ping_time"] - out["trip_start"]).dt.total_seconds() / 3600
    )
    out["gps_position_drift_km"] = haversine_km(
        out["current_lat"],
        out["current_lon"],
        out["dest_lat"],
        out["dest_lon"],
    )

    return out
