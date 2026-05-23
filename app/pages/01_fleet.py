"""Strona 1: Fleet Priority — lista priorytetowa dla handlowca."""

from __future__ import annotations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.data_loader import (
    load_dashboard,
    enrich_with_generation,
    PRIORITY_ORDER,
    PRIORITY_EMOJI,
    CONFIDENCE_EMOJI,
    priority_sort_key,
)
from app.style import (
    kpi_card,
    section_header,
    page_header,
    action_box,
    PRIORITY_COLORS,
)


# ── Dane ─────────────────────────────────────────────────────────────────────
df = enrich_with_generation(load_dashboard())
if df.empty:
    st.error("Brak danych. Uruchom: `python predict.py`")
    st.stop()

# ── Filtry w sidebarze ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filtry")
    st.caption("Zawęź listę do interesujących Cię samolotów")

    search = st.text_input("Szukaj rejestracji / operatora", "")

    available_priorities = [p for p in PRIORITY_ORDER if p in df["priorytet_smart"].unique()]
    default_priorities = [p for p in available_priorities if p not in ["Nieaktywny", "Daleko"]]
    selected_priorities = st.multiselect(
        "Priorytet C-check",
        available_priorities,
        default=default_priorities,
        format_func=lambda p: f"{PRIORITY_EMOJI.get(p, '⚪')} {p}",
    )

    # ML probability threshold — zamienia multiselect confidence na dynamiczny slider
    prob_threshold = st.slider(
        "Min ML probability (c_check_prob ≥)",
        min_value=0.0, max_value=1.0, value=0.0, step=0.05,
        help="Przesuń żeby zobaczyć jak zmienia się lista przy różnych progach ML",
    )

    available_conf = [c for c in ["HIGH", "MEDIUM", "LOW"]
                      if c in df["confidence"].unique()] if "confidence" in df.columns else []
    selected_conf = st.multiselect(
        "Confidence (reguły lokalizacji)",
        available_conf,
        default=["HIGH", "MEDIUM"],
        format_func=lambda c: f"{CONFIDENCE_EMOJI.get(c, '⚪')} {c}",
    )

    # Kraj rejestracji
    if "registration_country" in df.columns:
        available_countries = sorted(df["registration_country"].dropna().unique())
        selected_countries = st.multiselect("Kraj rejestracji", available_countries)
    else:
        selected_countries = []

    operators = sorted(df["icao_operator"].dropna().unique()) if "icao_operator" in df.columns else []
    selected_ops = st.multiselect("Operator (ICAO)", operators)

    active_only = st.checkbox("Tylko aktywne samoloty", value=True)

    st.markdown("---")
    st.markdown(action_box(
        "JAK CZYTAĆ TABELĘ",
        "Wiersze czerwone = działaj <b>teraz</b>.<br>"
        "Żółte = zaplanuj kontakt w tym kwartale.<br>"
        "Niebieskie = obserwuj, kontakt za ~6 mies.<br>"
        "Kolumna <b>Za (mies.)</b> = ile miesięcy do okna C-check.",
        accent="#3b82f6",
    ), unsafe_allow_html=True)

# ── Filtrowanie ──────────────────────────────────────────────────────────────
df["typ_check"] = "C-check"   # dashboard zawiera wyłącznie C-check kandydatów
filtered = df.copy()

if active_only and "is_active" in filtered.columns:
    filtered = filtered[filtered["is_active"]]
if selected_priorities:
    filtered = filtered[filtered["priorytet_smart"].isin(selected_priorities)]
# Filtr ML probability: c_check_prob >= próg LUB brak kolumny (fallback)
if prob_threshold > 0.0 and "c_check_probability" in filtered.columns:
    filtered = filtered[filtered["c_check_probability"].fillna(0) >= prob_threshold]
if selected_conf and "confidence" in filtered.columns:
    filtered = filtered[filtered["confidence"].isin(selected_conf)]
if selected_countries and "registration_country" in filtered.columns:
    filtered = filtered[filtered["registration_country"].isin(selected_countries)]
if selected_ops:
    filtered = filtered[filtered["icao_operator"].isin(selected_ops)]
if search:
    mask = (
        filtered["registration"].str.contains(search.upper(), na=False) |
        filtered["icao_operator"].str.contains(search.upper(), na=False)
    )
    filtered = filtered[mask]

filtered = filtered.copy()
filtered["_sort_key"] = priority_sort_key(filtered["priorytet_smart"])
filtered = filtered.sort_values(["_sort_key", "mies_do_next_smart"]).drop(columns=["_sort_key"])

# ── Nagłówek ─────────────────────────────────────────────────────────────────
st.markdown(page_header(
    "Fleet Priority",
    "Wszystkie B737 w Europie posortowane wg zbliżającego się okna C-check · Dla handlowca LOTAMS",
    "📋",
), unsafe_allow_html=True)

# ── PANEL 1: KPI tiles ────────────────────────────────────────────────────────
n_teraz = len(filtered[filtered["priorytet_smart"].isin(["TERAZ", "TERAZ (zaległe)"])])
n_szesc = len(filtered[filtered["priorytet_smart"] == "6 mies."])
n_12    = len(filtered[filtered["priorytet_smart"] == "12 mies."])
n_high  = len(filtered[filtered["confidence"] == "HIGH"]) if "confidence" in filtered.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(kpi_card(str(len(filtered)), "Samoloty (po filtrach)", f"{len(df)} w sumie",
    bg="#1e293b", accent="#3b82f6"), unsafe_allow_html=True)
c2.markdown(kpi_card(str(n_teraz), "🔴 TERAZ", "Kontaktuj natychmiast",
    bg="#7f1d1d", accent="#ef4444", text_color="#fef2f2"), unsafe_allow_html=True)
c3.markdown(kpi_card(str(n_szesc), "🟡 6 mies.", "Zaplanuj outreach",
    bg="#78350f", accent="#fbbf24", text_color="#fef3c7"), unsafe_allow_html=True)
c4.markdown(kpi_card(str(n_12), "🔵 12 mies.", "Obserwuj",
    bg="#1e3a8a", accent="#60a5fa", text_color="#eff6ff"), unsafe_allow_html=True)
c5.markdown(kpi_card(str(n_high), "🟢 HIGH conf.", "Potwierdzone w MRO",
    bg="#14532d", accent="#4ade80", text_color="#f0fdf4"), unsafe_allow_html=True)

st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

# ── PANEL 2: Tabela + mini wykres ─────────────────────────────────────────────
st.markdown(section_header(
    "LISTA PRIORYTETOWA",
    f"Pokazuje {len(filtered)} samolotów · Posortowane wg priorytetu → daty",
    accent="#ef4444",
), unsafe_allow_html=True)

col_table, col_chart = st.columns([7, 3])

with col_chart:
    # Donut dla widocznych samolotów
    visible_counts = (
        filtered["priorytet_smart"]
        .value_counts()
        .reindex(PRIORITY_ORDER, fill_value=0)
        .reset_index()
    )
    visible_counts.columns = ["Priorytet", "N"]
    visible_counts = visible_counts[visible_counts["N"] > 0]

    donut_colors = {
        "TERAZ (zaległe)": "#7f1d1d",
        "TERAZ": "#ef4444",
        "6 mies.": "#f59e0b",
        "12 mies.": "#3b82f6",
        "Daleko": "#475569",
        "Nieaktywny": "#334155",
    }

    fig_mini = go.Figure(go.Pie(
        labels=visible_counts["Priorytet"],
        values=visible_counts["N"],
        hole=0.5,
        marker_colors=[donut_colors.get(p, "#334155") for p in visible_counts["Priorytet"]],
        textinfo="value",
        textfont=dict(size=10, color="white"),
    ))
    fig_mini.update_layout(
        showlegend=True,
        legend=dict(font=dict(color="#94a3b8", size=10), x=0, y=-0.2, orientation="h"),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        margin=dict(l=0, r=0, t=10, b=10),
        height=230,
    )
    st.plotly_chart(fig_mini, use_container_width=True)

    # Confidence breakdown bar
    if "confidence" in filtered.columns:
        conf_counts = filtered["confidence"].value_counts().reset_index()
        conf_counts.columns = ["Confidence", "N"]
        conf_colors_map = {"HIGH": "#16a34a", "MEDIUM": "#d97706", "LOW": "#dc2626"}
        fig_conf = go.Figure(go.Bar(
            x=conf_counts["Confidence"],
            y=conf_counts["N"],
            marker_color=[conf_colors_map.get(c, "#64748b") for c in conf_counts["Confidence"]],
            text=conf_counts["N"],
            textposition="outside",
            textfont=dict(color="#94a3b8"),
        ))
        fig_conf.update_layout(
            xaxis=dict(color="#94a3b8"),
            yaxis=dict(color="#94a3b8", showgrid=False),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            margin=dict(l=0, r=0, t=10, b=20),
            height=180,
            title=dict(text="Confidence", font=dict(color="#94a3b8", size=11)),
        )
        st.plotly_chart(fig_conf, use_container_width=True)

with col_table:
    DISPLAY_COLS = {
        "priorytet_smart":      "Priorytet",
        "registration":         "Rejestracja",
        "icao_operator":        "Operator",
        "registration_country": "Kraj",
        "generacja":            "Generacja",
        "wiek_est":             "Wiek (est.)",
        "typ_check":            "Typ check",
        "confidence":           "Conf.",
        "c_check_probability":  "ML prob.",
        "ostatni_c_check":      "Ostatni C-check",
        "czas_dni":             "Czas trwania (dni)",
        "predicted_next_smart": "Prognoza",
        "mies_do_next_smart":   "Za (mies.)",
        "mro_facility":         "MRO",
    }
    exist = {k: v for k, v in DISPLAY_COLS.items() if k in filtered.columns}
    show = filtered[list(exist.keys())].rename(columns=exist).copy()

    if "Priorytet" in show.columns:
        show["Priorytet"] = show["Priorytet"].map(lambda p: f"{PRIORITY_EMOJI.get(p, '⚪')} {p}")
    if "Conf." in show.columns:
        show["Conf."] = show["Conf."].map(lambda c: f"{CONFIDENCE_EMOJI.get(c, '⚪')} {c}")
    if "Ostatni C-check" in show.columns:
        show["Ostatni C-check"] = pd.to_datetime(show["Ostatni C-check"], errors="coerce").dt.strftime("%b %Y")
    if "Prognoza" in show.columns:
        show["Prognoza"] = pd.to_datetime(show["Prognoza"], errors="coerce").dt.strftime("%b %Y")
    if "Za (mies.)" in show.columns:
        show["Za (mies.)"] = show["Za (mies.)"].round(1)
    if "ML prob." in show.columns:
        show["ML prob."] = show["ML prob."].round(3)
    if "Czas trwania (dni)" in show.columns:
        show["Czas trwania (dni)"] = show["Czas trwania (dni)"].round(0).astype("Int64")

    def _row_style(row):
        p = str(row.get("Priorytet", ""))
        if "zaległe" in p:
            return ["background-color:#7f1d1d; color:#fef2f2"] * len(row)
        if "TERAZ" in p:
            return ["background-color:#991b1b; color:#fef2f2"] * len(row)
        if "6 mies" in p:
            return ["background-color:#78350f; color:#fef3c7"] * len(row)
        if "12 mies" in p:
            return ["background-color:#1e3a8a; color:#eff6ff"] * len(row)
        return ["background-color:#111827; color:#9ca3af"] * len(row)

    styled = show.style.apply(_row_style, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True, height=580)

# ── Eksport ──────────────────────────────────────────────────────────────────
col_dl1, col_dl2, spacer = st.columns([2, 2, 8])
with col_dl1:
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Eksport CSV (pełny)",
        csv, "mro_fleet_priority.csv", "text/csv",
    )
with col_dl2:
    csv_simple = show.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📋 Eksport CSV (widok)",
        csv_simple, "mro_fleet_view.csv", "text/csv",
    )

# ── Legenda ───────────────────────────────────────────────────────────────────
with st.expander("ℹ️ Legenda priorytetów i confidence"):
    c_leg1, c_leg2 = st.columns(2)
    with c_leg1:
        st.markdown("""
**Priorytety:**

| Symbol | Znaczenie | Działanie |
|---|---|---|
| 🚨 TERAZ (zaległe) | Termin C-check minął | Zadzwoń dziś |
| 🔴 TERAZ | C-check za 0–6 mies. | Wyślij ofertę teraz |
| 🟡 6 mies. | C-check za 6–12 mies. | Zaplanuj outreach |
| 🔵 12 mies. | C-check za 12–18 mies. | Obserwuj, buduj relację |
| ⚪ Daleko | > 18 mies. | Baza do przyszłości |
| ⬛ Nieaktywny | Nie latał >6 mies. | Wyleased/sprzedany |
""")
    with c_leg2:
        st.markdown("""
**Confidence (pewność wykrycia C-check):**

| Symbol | Znaczenie |
|---|---|
| 🟢 HIGH | Przerwa w dedykowanym MRO — niemal pewny C-check |
| 🟡 MEDIUM | Hub z MRO — prawdopodobny C-check |
| 🔴 LOW | ML ocenił jako C-check mimo nieznane miejsce |

**Źródło interwału:** `per_aircraft` > `operator` > `global_mean` > `fallback 730d`
""")
