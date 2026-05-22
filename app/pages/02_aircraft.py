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

    for _, row in subset.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["dep_time_utc"], row["arr_time_utc"]],
                y=[registration, registration],
                mode="lines",
                line=dict(color="#2563eb", width=8),
                hovertemplate=f"{row['dep_airport']} → {row['arr_airport']}<extra></extra>",
                showlegend=False,
            )
        )

    for _, gap in gap_subset.iterrows():
        color = "#dc2626" if gap["check_type"] == "C-check" else "#9ca3af"
        fig.add_trace(
            go.Scatter(
                x=[gap["gap_start"], gap["gap_end"]],
                y=[registration, registration],
                mode="lines",
                line=dict(color=color, width=12),
                name=f"{gap['check_type']} ({gap['duration_days']}d)",
                hovertemplate=(
                    f"Przerwa: {gap['duration_days']} dni<br>"
                    f"Typ: {gap['check_type']}<br>"
                    f"{gap['last_airport']} → {gap['next_airport']}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"Oś czasu lotów — {registration}",
        xaxis_title="Data (UTC)",
        yaxis_visible=False,
        height=280,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", y=-0.2),
    )
    return fig


def render() -> None:
    st.header("Aircraft Detail")
    flights, gaps, predictions = load_data()
    if predictions.empty:
        st.warning("Brak danych. Uruchom pipeline.")
        return

    registrations = sorted(predictions["registration"].dropna().unique())
    demo_pins = [r for r in ["EI-FRK", "SP-LVB", "OE-LNT", "G-JZHF"] if r in registrations]
    default = demo_pins[0] if demo_pins else registrations[0]

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
