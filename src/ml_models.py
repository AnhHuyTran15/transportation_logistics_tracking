"""ML pipelines: ETA, delay, risk, anomaly."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    mean_absolute_error,
    roc_auc_score,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier

from .config import ML_TEST_SIZE, RANDOM_STATE

try:
    import lightgbm as lgb

    _HAS_LGB = True
except ImportError:
    _HAS_LGB = False


def _feature_lists(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    num = [
        "distance_km",
        "geo_distance_km",
        "route_detour_ratio",
        "wait_hours",
        "avg_speed_kmph",
        "km_per_day",
    ]
    cat = [
        "shipment_type",
        "vehicle_type",
        "route_category",
        "distance_band",
        "material_group",
        "supplier_name",
        "customer_tier",
        "origin_location",
        "destination_location",
    ]
    return num, cat


def build_preprocessor(num: list[str], cat: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("num", "passthrough", num),
            ("cat", OneHotEncoder(handle_unknown="ignore", max_categories=30), cat),
        ]
    )


def train_eta_model(df: pd.DataFrame) -> dict:
    """Predict trip duration (days) as ETA proxy."""
    num, cat = _feature_lists(df)
    m = df.dropna(subset=["trip_days"] + num).copy()
    X = m[num + cat]
    y = m["trip_days"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=ML_TEST_SIZE, random_state=RANDOM_STATE
    )
    reg = Pipeline(
        [
            ("pre", build_preprocessor(num, cat)),
            (
                "model",
                GradientBoostingRegressor(
                    n_estimators=150, max_depth=5, random_state=RANDOM_STATE
                ),
            ),
        ]
    )
    reg.fit(X_train, y_train)
    pred = reg.predict(X_test)
    return {
        "target": "trip_days",
        "test_mae_days": round(mean_absolute_error(y_test, pred), 3),
        "model": reg,
        "features": num + cat,
    }


def train_delay_classifier(df: pd.DataFrame) -> dict:
    num, cat = _feature_lists(df)
    m = df.dropna(subset=num + ["is_late"]).copy()
    X = m[num + cat]
    y = m["is_late"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=ML_TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    if _HAS_LGB:
        from lightgbm import LGBMClassifier

        est = LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            random_state=RANDOM_STATE,
            class_weight="balanced",
            verbose=-1,
        )
    else:
        est = RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            random_state=RANDOM_STATE,
            class_weight="balanced",
        )
    clf = Pipeline([("pre", build_preprocessor(num, cat)), ("model", est)])
    clf.fit(X_train, y_train)
    proba = clf.predict_proba(X_test)[:, 1]
    return {
        "target": "is_late",
        "test_auc": round(roc_auc_score(y_test, proba), 3),
        "report": classification_report(y_test, (proba >= 0.5).astype(int)),
        "model": clf,
    }


def shipment_risk_score(df: pd.DataFrame, model_bundle: dict) -> pd.Series:
    """0-100 risk score from late probability."""
    num, cat = _feature_lists(df)
    m = df.dropna(subset=num).copy()
    proba = model_bundle["model"].predict_proba(m[num + cat])[:, 1]
    scores = pd.Series(index=df.index, dtype=float)
    scores.loc[m.index] = (proba * 100).round(1)
    return scores


def route_anomaly_detection(df: pd.DataFrame) -> pd.DataFrame:
    """IsolationForest on route KPI vectors."""
    route = (
        df.groupby("route_id")
        .agg(
            bookings=("booking_id", "count"),
            ontime_rate=("is_ontime", "mean"),
            avg_delay=("delay_hours", "mean"),
            avg_trip_days=("trip_days", "mean"),
            avg_detour=("route_detour_ratio", "mean"),
        )
        .reset_index()
    )
    route = route[route["bookings"] >= 5]
    feats = route[
        ["ontime_rate", "avg_delay", "avg_trip_days", "avg_detour", "bookings"]
    ].fillna(0)
    iso = IsolationForest(contamination=0.08, random_state=RANDOM_STATE)
    route["anomaly_score"] = iso.fit_predict(feats)
    route["is_anomaly"] = route["anomaly_score"] == -1
    return route.sort_values("avg_delay", ascending=False)


def forecast_monthly_volume(df: pd.DataFrame, periods: int = 3) -> pd.DataFrame:
    """Simple exponential smoothing forecast for booking volume."""
    monthly = (
        df.groupby("booking_month")["booking_id"]
        .count()
        .reset_index(name="bookings")
    )
    monthly["booking_month"] = pd.PeriodIndex(monthly["booking_month"], freq="M")
    monthly = monthly.sort_values("booking_month")
    y = monthly["bookings"].astype(float)
    if len(y) < 4:
        return monthly
    alpha = 0.35
    level = y.iloc[0]
    forecasts = []
    for val in y:
        level = alpha * val + (1 - alpha) * level
    last_period = monthly["booking_month"].iloc[-1]
    rows = []
    for i in range(1, periods + 1):
        p = last_period + i
        rows.append({"booking_month": str(p), "forecast_bookings": round(level)})
    return pd.DataFrame(rows)
