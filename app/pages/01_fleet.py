from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import load_config
from src.scoring.priority import format_predictions_table


@st.cache_data
def load_predictions() -> pd.DataFrame:
    config = load_config()
    path = Path(config["paths"]["predictions"])
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def render() -> None:
    st.header("Fleet Priority")
    st.caption("Lista Boeing 737 w Europie posortowana według zbliżającego się okna decyzyjnego C-check")

    predictions = load_predictions()
    if predictions.empty:
        st.warning("Brak danych. Uruchom: `python scripts/run_pipeline.py`")
        return

    operators = sorted(predictions["operator"].dropna().unique())
    bands = sorted(predictions["priority_band"].dropna().unique(), key=lambda x: x)

    col1, col2, col3 = st.columns(3)
    with col1:
        operator_filter = st.multiselect("Operator", operators, default=operators)
    with col2:
        band_filter = st.multiselect("Priorytet", bands, default=bands)
    with col3:
        min_confidence = st.slider("Min. confidence", 0.0, 1.0, 0.3, 0.05)

    filtered = predictions[
        predictions["operator"].isin(operator_filter)
        & predictions["priority_band"].isin(band_filter)
        & (predictions["confidence"] >= min_confidence)
    ]

    c_only = st.checkbox("Tylko historia C-check", value=False)
    if c_only:
        filtered = filtered[filtered["last_check_type"] == "C-check"]

    low_conf = len(filtered[filtered["confidence"] < 0.5])
    if low_conf > 0:
        st.warning(
            f"⚠️ {low_conf} z {len(filtered)} samolotów ma confidence < 0.5 — "
            "prognoza opiera się na krótkich przerwach (A/B-check), nie na historii C-check. "
            "Podnieś próg Min. confidence lub zaznacz **Tylko historia C-check** dla pewniejszych wyników."
        )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Samoloty", filtered["icao24"].nunique())
    k2.metric("TERAZ", len(filtered[filtered["priority_band"] == "TERAZ"]))
    k3.metric("6 mies.", len(filtered[filtered["priority_band"] == "6 mies."]))
    k4.metric("Śr. confidence", f"{filtered['confidence'].mean():.2f}" if len(filtered) else "—")

    table = format_predictions_table(filtered)
    st.dataframe(table.drop(columns=["icao24", "urgency_score", "confidence"], errors="ignore"), use_container_width=True)

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Eksport CSV", csv, "mro_priority.csv", "text/csv")


render()
