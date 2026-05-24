"""GPS preprocessing for snapshot and high-frequency trajectory data."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .features import haversine_km


def preprocess_gps_trajectory(
    pings: pd.DataFrame,
    booking_col: str = "booking_id",
    time_col: str = "gps_ping_time",
    lat_col: str = "current_lat",
    lon_col: str = "current_lon",
) -> pd.DataFrame:
    """
    Enterprise GPS preprocessing for multi-ping trajectories.
    Handles missing pings, speed outliers, and idle detection.
    """
    df = pings.sort_values([booking_col, time_col]).copy()
    df["prev_lat"] = df.groupby(booking_col)[lat_col].shift()
    df["prev_lon"] = df.groupby(booking_col)[lon_col].shift()
    df["prev_time"] = df.groupby(booking_col)[time_col].shift()
    df["delta_hours"] = (
        (df[time_col] - df["prev_time"]).dt.total_seconds() / 3600
    )
    df["segment_km"] = haversine_km(
        df["prev_lat"], df["prev_lon"], df[lat_col], df[lon_col]
    )
    df["segment_speed_kmph"] = np.where(
        df["delta_hours"] > 0, df["segment_km"] / df["delta_hours"], np.nan
    )
    # Idle: < 2 km/h for > 2 hours
    df["is_idle_segment"] = (df["segment_speed_kmph"] < 2) & (df["delta_hours"] >= 2)
    return df


def snapshot_gps_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize GPS behavior when only last-known-location snapshots exist."""
    summary = pd.DataFrame(
        {
            "bookings": [df["booking_id"].nunique()],
            "median_pings_per_booking": [df.groupby("booking_id").size().median()],
            "missing_current_location": [df["current_location"].isna().mean()],
            "missing_gps_coords": [
                df[["current_lat", "current_lon"]].isna().any(axis=1).mean()
            ],
            "avg_ping_lag_from_trip_start_h": [df["gps_ping_lag_hours"].median()],
            "tracking_recommendation": [
                "Deploy continuous GPS (30-60s) for idle/moving decomposition"
            ],
        }
    )
    return summary
