from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import load_config


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config = load_config()
    flights = pd.read_parquet(config["paths"]["flights"]) if Path(config["paths"]["flights"]).exists() else pd.DataFrame()
    gaps = pd.read_parquet(config["paths"]["gaps"]) if Path(config["paths"]["gaps"]).exists() else pd.DataFrame()
    predictions = (
        pd.read_parquet(config["paths"]["predictions"]) if Path(config["paths"]["predictions"]).exists() else pd.DataFrame()
    )
    return flights, gaps, predictions


def _timeline_figure(flights: pd.DataFrame, gaps: pd.DataFrame, registration: str) -> go.Figure:
    subset = flights[flights["registration"] == registration].copy()
    gap_subset = gaps[gaps["registration"] == registration].copy()
    fig = go.Figure()

    # Agreguj loty do tygodniowych bloków aktywności — zamiast 1 trace na lot
    if not subset.empty:
        subset = subset.sort_values("dep_time_utc")
        subset["week"] = subset["dep_time_utc"].dt.to_period("W").dt.start_time
        weekly = subset.groupby("week").agg(
            week_start=("dep_time_utc", "min"),
            week_end=("arr_time_utc", "max"),
            flights=("flight_id", "count"),
        ).reset_index(drop=True)
        for _, w in weekly.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[w["week_start"], w["week_end"]],
                    y=[registration, registration],
                    mode="lines",
                    line=dict(color="#2563eb", width=8),
                    hovertemplate=f"{w['flights']} lotów w tygodniu<extra></extra>",
                    showlegend=False,
                )
            )

    color_map = {
        "C-check": "#dc2626",
        "D-check": "#7c3aed",
        "B-check": "#f59e0b",
        "A-check": "#9ca3af",
        "unknown": "#d1d5db",
    }
    for _, gap in gap_subset.iterrows():
        color = color_map.get(gap["check_type"], "#9ca3af")
        fig.add_trace(
            go.Scatter(
                x=[gap["gap_start"], gap["gap_end"]],
                y=[registration, registration],
                mode="lines",
                line=dict(color=color, width=14),
                name=f"{gap['check_type']} ({gap['duration_days']}d)",
                hovertemplate=(
                    f"Przerwa: {gap['duration_days']} dni<br>"
                    f"Typ: {gap['check_type']}<br>"
                    f"Confidence: {gap['confidence']:.2f}<br>"
                    f"{gap['last_airport']} → {gap['next_airport']}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"Oś czasu — {registration}",
        xaxis_title="Data (UTC)",
        yaxis_visible=False,
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def render() -> None:
    st.header("Aircraft Detail")
    flights, gaps, predictions = load_data()
    if predictions.empty:
        st.warning("Brak danych. Uruchom pipeline.")
        return

    registrations = sorted(predictions["registration"].dropna().unique())
    # Domyślnie: pierwszy samolot z historią C-check i wysokim confidence
    c_check_preds = predictions[
        (predictions["last_check_type"] == "C-check") & (predictions["confidence"] >= 0.7)
    ].sort_values("urgency_score", ascending=False)
    default = c_check_preds["registration"].iloc[0] if not c_check_preds.empty else registrations[0]

    registration = st.selectbox("Rejestracja", registrations, index=registrations.index(default))
    pred = predictions[predictions["registration"] == registration].iloc[0]

    col_chart, col_info = st.columns([2, 1])
    with col_chart:
        if not flights.empty:
            st.plotly_chart(_timeline_figure(flights, gaps, registration), use_container_width=True)
        else:
            st.info("Brak lotów dla wybranej rejestracji.")

    with col_info:
        st.subheader("Prognoza")
        st.metric("Operator", pred.get("operator", "—"))
        st.metric("Wiek", f"{pred.get('age_years', '—')} lat")
        st.metric("Ostatni check", pred.get("last_check_type", "—"))
        st.metric("Prognoza C-check", pred.get("forecast_quarter", "—"))
        st.metric("Priorytet", pred.get("priority_label", "—"))
        if pred.get("suggested_contact_date") is not None and not pd.isna(pred["suggested_contact_date"]):
            st.metric("Sugerowany kontakt", pd.Timestamp(pred["suggested_contact_date"]).strftime("%Y-%m-%d"))

        conf = pred.get("confidence", 0)
        if conf < 0.5:
            st.warning(f"⚠️ Confidence: {conf:.2f} — brak historii C-check. Prognoza szacunkowa.")
        else:
            st.success(f"✅ Confidence: {conf:.2f}")

        st.markdown("---")
        st.markdown("**Konkurencja MRO**")
        st.caption("Lufthansa Technik · AFI KLM E&M · Turkish Technic · Iberia Maintenance")
        st.caption("Gdy samolot znika 3–6 tyg. — slot już zajęty u konkurencji.")

    if not gaps.empty:
        st.subheader("Historia przerw")
        gap_rows = gaps[gaps["registration"] == registration][
            ["gap_start", "gap_end", "duration_days", "check_type", "confidence", "last_airport", "next_airport"]
        ]
        st.dataframe(gap_rows, use_container_width=True)


render()
