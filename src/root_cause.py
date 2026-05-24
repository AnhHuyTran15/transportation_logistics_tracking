"""Root-cause diagnostics: beyond simple correlation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import roc_auc_score, mean_absolute_error

from .config import RANDOM_STATE


def _prep_model_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Modeling frame with operational controls."""
    cols = [
        "distance_km",
        "route_detour_ratio",
        "wait_hours",
        "shipment_type",
        "vehicle_type",
        "route_category",
        "distance_band",
        "material_group",
        "supplier_name",
        "customer_tier",
        "booking_dow",
        "avg_speed_kmph",
        "km_per_day",
    ]
    m = df.dropna(subset=["delay_hours"]).copy()
    m = m[cols + ["delay_hours", "is_late", "is_ontime"]]
    num = ["distance_km", "route_detour_ratio", "wait_hours", "avg_speed_kmph", "km_per_day"]
    cat = [c for c in cols if c not in num]
    for c in num:
        m[c] = pd.to_numeric(m[c], errors="coerce")
    m = m.dropna(subset=num)
    return m, num, cat


def delay_driver_model(df: pd.DataFrame) -> dict:
    """
    Multivariate delay model with controls.
    Distinguishes correlation vs operational drivers via permutation importance + SHAP-ready pipeline.
    """
    m, num, cat = _prep_model_frame(df)
    X = m[num + cat]
    y = m["delay_hours"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    pre = ColumnTransformer(
        [
            ("num", "passthrough", num),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", max_categories=25),
                cat,
            ),
        ]
    )
    reg = Pipeline(
        [
            ("pre", pre),
            (
                "model",
                GradientBoostingRegressor(
                    random_state=RANDOM_STATE, n_estimators=120, max_depth=4
                ),
            ),
        ]
    )
    reg.fit(X_train, y_train)
    pred = reg.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    perm = permutation_importance(
        reg, X_test, y_test, n_repeats=5, random_state=RANDOM_STATE, n_jobs=1
    )
    raw_names = list(num) + list(cat)
    imp = (
        pd.DataFrame(
            {
                "feature": raw_names,
                "importance_mean": perm.importances_mean[: len(raw_names)],
                "importance_std": perm.importances_std[: len(raw_names)],
            }
        )
        .sort_values("importance_mean", ascending=False)
    )
    return {
        "model_type": "gradient_boosting_delay_hours",
        "test_mae_hours": round(mae, 2),
        "top_drivers": imp,
        "interpretation_note": (
            "High importance on wait_hours/route_detour supports process bottlenecks; "
            "distance alone should not dominate if infrastructure is the root cause."
        ),
    }


def late_risk_classifier(df: pd.DataFrame) -> dict:
    """Classify late vs on-time with segmented features."""
    m, num, cat = _prep_model_frame(df)
    X = m[num + cat]
    y = m["is_late"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    pre = ColumnTransformer(
        [
            ("num", "passthrough", num),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", max_categories=25),
                cat,
            ),
        ]
    )
    clf = Pipeline(
        [
            ("pre", pre),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=8,
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    clf.fit(X_train, y_train)
    proba = clf.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    perm = permutation_importance(
        clf, X_test, y_test, n_repeats=5, random_state=RANDOM_STATE, n_jobs=1
    )
    raw_names = list(num) + list(cat)
    imp = (
        pd.DataFrame(
            {
                "feature": raw_names,
                "importance_mean": perm.importances_mean[: len(raw_names)],
            }
        )
        .sort_values("importance_mean", ascending=False)
    )
    return {"test_auc": round(auc, 3), "top_risk_drivers": imp}


def supplier_capability_gap(df: pd.DataFrame, supplier: str) -> pd.DataFrame:
    """
    Compare supplier vs peer median within same distance band + vehicle type.
    Surfaces capability limitations vs route difficulty.
    """
    peer = (
        df.groupby(["distance_band", "vehicle_type"], dropna=False)
        .agg(peer_ontime=("is_ontime", "mean"), peer_delay=("delay_hours", "mean"))
        .reset_index()
    )
    sup = df[df["supplier_name"] == supplier].copy()
    merged = sup.merge(peer, on=["distance_band", "vehicle_type"], how="left")
    merged["ontime_gap_vs_peer"] = merged["is_ontime"] - merged["peer_ontime"]
    merged["delay_gap_vs_peer_h"] = merged["delay_hours"] - merged["peer_delay"]
    return (
        merged.groupby(["distance_band", "vehicle_type"])
        .agg(
            bookings=("booking_id", "count"),
            ontime_rate=("is_ontime", "mean"),
            peer_ontime=("peer_ontime", "first"),
            ontime_gap=("ontime_gap_vs_peer", "mean"),
            avg_delay_h=("delay_hours", "mean"),
            peer_delay_h=("peer_delay", "first"),
        )
        .reset_index()
    )


def bottleneck_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify delay contribution: waiting, moving inefficiency, unloading, idle proxy.
    """
    total = df["delay_hours"].clip(lower=0).sum()
    components = pd.DataFrame(
        {
            "component": [
                "waiting_before_dispatch",
                "slow_moving_trip",
                "unloading_after_arrival",
                "idle_beyond_contract_pace",
            ],
            "hours_sum": [
                df["wait_hours"].sum(),
                (df["moving_hours"] - (df["distance_km"] / 50 * 1)).clip(lower=0).sum(),
                df["unloading_hours"].sum(),
                (df["idle_days_proxy"] * 24).sum(),
            ],
        }
    )
    components["share_of_positive_delay_pool"] = (
        components["hours_sum"] / total * 100 if total > 0 else 0
    ).round(2)
    return components
