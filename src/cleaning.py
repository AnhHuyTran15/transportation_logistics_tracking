"""Data cleaning pipeline for shipment tracking records."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DISTANCE_BINS, DISTANCE_LABELS, LONG_HAUL_DISTANCE_KM, URBAN_DISTANCE_KM


def clean_shipments(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean shipment-level records. Returns (clean_df, quality_log).
    Deduplicates bookings keeping latest GPS ping when multiple exist.
    """
    out = df.copy()
    date_cols = [
        "booking_date",
        "gps_ping_time",
        "planned_eta",
        "actual_eta",
        "trip_start",
        "trip_end",
    ]
    for c in date_cols:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")

    log = []

    # Deduplicate: prefer row with actual_eta, then latest ping
    before = len(out)
    out["_has_actual"] = out["actual_eta"].notna().astype(int)
    out = out.sort_values(
        ["booking_id", "_has_actual", "gps_ping_time"],
        ascending=[True, False, False],
    )
    out = out.drop_duplicates(subset=["booking_id"], keep="first")
    out = out.drop(columns=["_has_actual"])
    log.append({"step": "dedupe_bookings", "rows_removed": before - len(out)})

    # Normalize categorical flags
    out["ontime_flag"] = (
        out["ontime_flag"]
        .astype(str)
        .str.strip()
        .str.title()
        .replace({"Nan": np.nan})
    )
    out["is_ontime"] = (out["ontime_flag"] == "Yes").astype("Int64")

    # Impute vehicle type with segment mode by distance band
    out["distance_km"] = pd.to_numeric(out["distance_km"], errors="coerce")
    out["distance_band"] = pd.cut(
        out["distance_km"],
        bins=DISTANCE_BINS,
        labels=DISTANCE_LABELS,
        include_lowest=True,
    )
    mode_by_band = (
        out.dropna(subset=["vehicle_type"])
        .groupby("distance_band", observed=True)["vehicle_type"]
        .agg(lambda s: s.mode().iloc[0] if len(s.mode()) else np.nan)
    )
    missing_vt = out["vehicle_type"].isna()
    out.loc[missing_vt, "vehicle_type"] = out.loc[missing_vt, "distance_band"].map(
        mode_by_band
    )
    out["vehicle_type_imputed"] = missing_vt & out["vehicle_type"].notna()
    log.append(
        {
            "step": "impute_vehicle_type",
            "imputed_count": int(out["vehicle_type_imputed"].sum()),
        }
    )

    # Cap impossible lifecycle values (data quality, not business truth)
    trip_days = (out["trip_end"] - out["trip_start"]).dt.total_seconds() / 86400
    invalid_trip = (trip_days < 0) | (trip_days > 90)
    out.loc[invalid_trip, "trip_end"] = pd.NaT
    log.append({"step": "null_invalid_trip_end", "count": int(invalid_trip.sum())})

    delay_h = (out["actual_eta"] - out["planned_eta"]).dt.total_seconds() / 3600
    extreme_delay = delay_h.abs() > 24 * 30
    out.loc[extreme_delay, "actual_eta"] = pd.NaT
    log.append({"step": "null_extreme_delay_eta", "count": int(extreme_delay.sum())})

    wait_h = (out["trip_start"] - out["booking_date"]).dt.total_seconds() / 3600
    bad_wait = wait_h < -24
    out.loc[bad_wait, "booking_date"] = out.loc[bad_wait, "trip_start"]
    log.append({"step": "fix_booking_after_start", "count": int(bad_wait.sum())})

    quality_log = pd.DataFrame(log)
    return out, quality_log
