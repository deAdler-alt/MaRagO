from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import load_config


@st.cache_data
def load_predictions() -> pd.DataFrame:
    config = load_config()
    path = Path(config["paths"]["predictions"])
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _sales_note(row: pd.Series) -> str:
    last = row.get("last_check_date")
    last_str = pd.Timestamp(last).strftime("%b %Y") if last is not None and not pd.isna(last) else "brak danych"
    return (
        f"Temat: Okno C-check — {row['registration']} ({row['operator']})\n\n"
        f"Szacowany C-check: {row['forecast_quarter']}\n"
        f"Ostatnia przerwa serwisowa: {last_str} ({row.get('last_check_type', 'unknown')}, "
        f"{row.get('last_gap_days', '—')} dni)\n"
        f"Utilization: {row.get('flights_per_month', '—')} lotów/mies.\n"
        f"Sugerowany pierwszy kontakt: "
        f"{pd.Timestamp(row['suggested_contact_date']).strftime('%Y-%m-%d') if row.get('suggested_contact_date') is not None and not pd.isna(row.get('suggested_contact_date')) else 'ASAP'}\n\n"
        f"LOTAMS — specjalista Boeing 737, dostępny slot, EASA quality, Środkowa Europa."
    )


def _weekly_digest(alerts: pd.DataFrame) -> str:
    lines = [
        "# MRO Weekly Digest — LOTAMS",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Samoloty w oknie decyzyjnym: **{len(alerts)}**",
        "",
    ]
    for _, row in alerts.iterrows():
        lines.append(
            f"- **{row['registration']}** ({row['operator']}) — {row['priority_label']}, "
            f"prognoza {row['forecast_quarter']}, confidence {row['confidence']:.2f}"
        )
    lines.append("")
    lines.append("_Klasyfikacja na podstawie przerw ADS-B/OPDI — sygnał pośredni._")
    return "\n".join(lines)


def render() -> None:
    st.header("Commercial Alerts")
    st.caption("Samoloty wchodzące w okno decyzyjne 6–12 miesięcy przed prawdopodobnym C-check")

    predictions = load_predictions()
    if predictions.empty:
        st.warning("Brak danych. Uruchom pipeline.")
        return

    alerts = predictions[predictions["priority_band"].isin(["TERAZ", "6 mies.", "12 mies."])].copy()
    alerts = alerts.sort_values("urgency_score", ascending=False)

    col_a, col_b = st.columns(2)
    with col_a:
        band_filter = st.multiselect(
            "Pasmo priorytetu",
            ["TERAZ", "6 mies.", "12 mies."],
            default=["TERAZ", "6 mies."],
        )
    with col_b:
        min_conf = st.slider("Min. confidence", 0.0, 1.0, 0.3, 0.05)

    alerts = alerts[alerts["priority_band"].isin(band_filter) & (alerts["confidence"] >= min_conf)]

    low_conf_count = len(predictions[
        predictions["priority_band"].isin(band_filter) & (predictions["confidence"] < 0.5)
    ])
    if low_conf_count > 0:
        st.warning(
            f"⚠️ {low_conf_count} alertów ukrytych / poniżej progu confidence < 0.5 — "
            "prognoza dla tych samolotów jest szacunkowa (brak historii C-check w danych)."
        )

    k1, k2, k3 = st.columns(3)
    k1.metric("Aktywne alerty", len(alerts))
    k2.metric("🔴 TERAZ", len(alerts[alerts["priority_band"] == "TERAZ"]))
    k3.metric("🟡 6 mies.", len(alerts[alerts["priority_band"] == "6 mies."]))

    st.markdown("---")
    MAX_EXPANDERS = 50
    if len(alerts) > MAX_EXPANDERS:
        st.info(f"Pokazuję top {MAX_EXPANDERS} z {len(alerts)} alertów (posortowane wg priorytetu). Pobierz CSV po pełną listę.")
    for _, row in alerts.head(MAX_EXPANDERS).iterrows():
        with st.expander(f"{row.get('priority_label', '')} {row['registration']} — {row.get('operator', '?')} | conf: {row['confidence']:.2f}"):
            st.code(_sales_note(row), language=None)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        digest = _weekly_digest(alerts)
        st.download_button(
            "Pobierz tygodniowy digest (Markdown)",
            digest.encode("utf-8"),
            "mro_weekly_digest.md",
            "text/markdown",
        )
    with col_dl2:
        csv = alerts[["registration", "operator", "forecast_quarter", "priority_label", "confidence", "suggested_contact_date"]].to_csv(index=False)
        st.download_button(
            "Pobierz pełną listę alertów (CSV)",
            csv.encode("utf-8"),
            "mro_alerts.csv",
            "text/csv",
        )

    st.markdown("---")
    st.caption(
        "Disclaimer: Prognoza oparta na przerwach w aktywności lotniczej (EUROCONTROL OPDI). "
        "Nie zastępuje dokumentacji serwisowej ani rozmowy z operatorem."
    )


render()
