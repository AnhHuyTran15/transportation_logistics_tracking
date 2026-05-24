"""Plotly/Matplotlib visualizations for logistics dashboards."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def kpi_cards_html(kpis: pd.Series) -> str:
    items = "".join(
        f"<div style='padding:12px;border:1px solid #ddd;border-radius:8px;margin:4px'>"
        f"<b>{k}</b><br>{v}</div>"
        for k, v in kpis.items()
    )
    return f"<div style='display:flex;flex-wrap:wrap'>{items}</div>"


def origin_bubble_map(df: pd.DataFrame):
    """Bookings and on-time rate by origin (Power BI style)."""
    agg = (
        df.groupby(["origin_location", "origin_lat", "origin_lon"])
        .agg(bookings=("booking_id", "count"), ontime_rate=("is_ontime", "mean"))
        .reset_index()
    )
    agg["ontime_rate_pct"] = agg["ontime_rate"] * 100
    return px.scatter_geo(
        agg,
        lat="origin_lat",
        lon="origin_lon",
        size="bookings",
        color="ontime_rate_pct",
        hover_name="origin_location",
        color_continuous_scale="RdYlGn",
        title="Bookings & On-time Rate by Origin",
        scope="asia",
    )


def bookings_trend(df: pd.DataFrame):
    monthly = (
        df.groupby("booking_month")["booking_id"].count().reset_index(name="bookings")
    )
    return px.area(
        monthly,
        x="booking_month",
        y="bookings",
        title="Total Bookings Trend Over Time",
    )


def supplier_combo_chart(supplier_df: pd.DataFrame, top_n: int = 12):
    top = supplier_df.head(top_n)
    fig = go.Figure()
    fig.add_bar(
        x=top["supplier_name"],
        y=top["total_bookings"],
        name="Bookings",
        marker_color="#5B2C6F",
    )
    fig.add_trace(
        go.Scatter(
            x=top["supplier_name"],
            y=top["ontime_rate_pct"],
            name="On-time %",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#3498DB"),
        )
    )
    fig.update_layout(
        title="Bookings vs On-time Rate by Supplier",
        yaxis=dict(title="Bookings"),
        yaxis2=dict(title="On-time %", overlaying="y", side="right"),
        template="plotly_white",
    )
    return fig


def conditional_table_style(df: pd.DataFrame, rate_col: str = "ontime_rate_pct"):
    """Return styled dataframe for notebook display."""
    return df.style.background_gradient(
        subset=[rate_col] if rate_col in df.columns else [],
        cmap="RdYlGn",
        vmin=0,
        vmax=100,
    )
