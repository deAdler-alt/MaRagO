"""Strona główna: Executive Overview — 4 panele BI."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.data_loader import (
    load_dashboard,
    load_candidates,
    enrich_with_generation,
    PRIORITY_ORDER,
    PRIORITY_EMOJI,
    CONFIDENCE_EMOJI,
)
from app.style import (
    GLOBAL_CSS,
    kpi_card,
    section_header,
    action_box,
    page_header,
    PRIORITY_COLORS,
)

st.set_page_config(
    page_title="MRO Intelligence | LOTAMS",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def _render_overview():
    # ── Dane ─────────────────────────────────────────────────────────────────────
    dashboard = enrich_with_generation(load_dashboard())
    candidates = load_candidates()

    if dashboard.empty:
        st.error("Brak danych. Uruchom: `python pipeline.py && python features.py && python train_classifier.py && python predict.py`")
        st.stop()

    active = dashboard[dashboard["is_active"]] if "is_active" in dashboard.columns else dashboard
    teraz_zaleg = active[active["priorytet_smart"] == "TERAZ (zaległe)"]
    teraz = active[active["priorytet_smart"] == "TERAZ"]
    szesc = active[active["priorytet_smart"] == "6 mies."]
    dwanascie = active[active["priorytet_smart"] == "12 mies."]
    high_conf = active[active["confidence"] == "HIGH"] if "confidence" in active.columns else active
    med_conf = active[active["confidence"] == "MEDIUM"] if "confidence" in active.columns else pd.DataFrame()
    high_or_med_teraz = active[
        active["priorytet_smart"].isin(["TERAZ (zaległe)", "TERAZ", "6 mies."]) &
        active["confidence"].isin(["HIGH", "MEDIUM"])
    ] if "confidence" in active.columns else pd.DataFrame()

    # ── Nagłówek ─────────────────────────────────────────────────────────────────
    st.markdown(page_header(
        "MRO Intelligence Platform",
        "Boeing 737 · Europa · Wczesne wykrywanie okien C-check · EUROCONTROL OPDI 2023-2026",
        "✈️",
    ), unsafe_allow_html=True)

    # ── PANEL 1: KPI tiles ────────────────────────────────────────────────────────
    st.markdown(section_header(
        "STAN FLOTY — PRZEGLĄD",
        "Wszystkie aktywne B737 w Europie według priorytetu C-check",
        accent="#3b82f6",
    ), unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.markdown(kpi_card(
        str(len(dashboard)),
        "B737 w Europie",
        f"{len(active)} aktywnych",
        bg="#1e293b", accent="#3b82f6", text_color="#f1f5f9",
    ), unsafe_allow_html=True)

    c2.markdown(kpi_card(
        str(len(teraz_zaleg) + len(teraz)),
        "KONTAKT TERAZ",
        "Okno decyzyjne — działaj natychmiast",
        bg="#7f1d1d", accent="#ef4444", text_color="#fef2f2",
    ), unsafe_allow_html=True)

    c3.markdown(kpi_card(
        str(len(szesc)),
        "Kontakt w 6 mies.",
        "Wchodzą w okno — zaplanuj outreach",
        bg="#78350f", accent="#fbbf24", text_color="#fef3c7",
    ), unsafe_allow_html=True)

    c4.markdown(kpi_card(
        str(len(high_or_med_teraz)),
        "HIGH/MEDIUM priorytet",
        "Potwierdzone C-checki w oknie",
        bg="#14532d", accent="#4ade80", text_color="#f0fdf4",
    ), unsafe_allow_html=True)

    c5.markdown(kpi_card(
        f"{len(candidates):,}",
        "Kandydatów C-check",
        f"AUC 0.975 · P@200=0.950",
        bg="#1e293b", accent="#8b5cf6", text_color="#f1f5f9",
    ), unsafe_allow_html=True)

    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    # ── PANEL 2: Rozkład priorytetów + Jak działa ──────────────────────────────
    st.markdown(section_header(
        "ROZKŁAD PRIORYTETÓW & METODOLOGIA",
        "Donut: podział floty · Prawo: jak interpretować wskaźniki",
        accent="#8b5cf6",
    ), unsafe_allow_html=True)

    col_donut, col_method = st.columns([2, 3])

    with col_donut:
        priority_counts = (
            active["priorytet_smart"]
            .value_counts()
            .reindex(PRIORITY_ORDER, fill_value=0)
            .reset_index()
        )
        priority_counts.columns = ["Priorytet", "Samoloty"]

        donut_colors = {
            "TERAZ (zaległe)": "#7f1d1d",
            "TERAZ":           "#ef4444",
            "6 mies.":         "#f59e0b",
            "12 mies.":        "#3b82f6",
            "Daleko":          "#475569",
            "Nieaktywny":      "#334155",
        }

        fig_donut = go.Figure(go.Pie(
            labels=priority_counts["Priorytet"],
            values=priority_counts["Samoloty"],
            hole=0.58,
            marker_colors=[donut_colors.get(p, "#334155") for p in priority_counts["Priorytet"]],
            textinfo="percent+value",
            textfont=dict(size=11, color="white"),
            hovertemplate="<b>%{label}</b><br>%{value} samolotów (%{percent})<extra></extra>",
        ))

        total_active = len(active)
        fig_donut.add_annotation(
            text=f"<b>{total_active}</b><br><span style='font-size:10px'>aktywnych</span>",
            x=0.5, y=0.5,
            font=dict(size=20, color="#f1f5f9"),
            showarrow=False,
        )
        fig_donut.update_layout(
            showlegend=True,
            legend=dict(
                orientation="v", x=1.0, y=0.5,
                font=dict(color="#94a3b8", size=11),
            ),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_method:
        st.markdown(action_box(
            "🚨 TERAZ (zaległe) — NATYCHMIASTOWE DZIAŁANIE",
            f"<b>{len(teraz_zaleg)} samolotów</b> — prognozowany C-check już minął. "
            "Okno MRO przegapione lub nie wykryte. Zadzwoń dziś.",
            accent="#ef4444",
        ), unsafe_allow_html=True)

        st.markdown(action_box(
            "🔴 TERAZ — OSTATNIE OKNO DECYZYJNE (0–6 MIES.)",
            f"<b>{len(teraz)} samolotów</b> — C-check za mniej niż 6 miesięcy. "
            "Kontrakt MRO podpisuje się 12 mies. przed — jesteś spóźniony. Wyślij ofertę <em>teraz</em>.",
            accent="#f87171",
        ), unsafe_allow_html=True)

        st.markdown(action_box(
            "🟡 6 MIES. — ZAPLANUJ OUTREACH (6–12 MIES.)",
            f"<b>{len(szesc)} samolotów</b> — idealne okno prospectingowe. "
            "Wyślij wstępne zapytanie, potwierdź slot, zbuduj relację przed przetargiem.",
            accent="#fbbf24",
        ), unsafe_allow_html=True)

        st.markdown(action_box(
            "🔵 12 MIES. — OBSERWUJ (12–18 MIES.)",
            f"<b>{len(dwanascie)} samolotów</b> — monitoruj. "
            "Sygnały o operator changach, sprzedaży samolotu lub wcześniejszym C-checku.",
            accent="#60a5fa",
        ), unsafe_allow_html=True)

    # ── PANEL 3: Top 10 priorytetów ───────────────────────────────────────────────
    st.markdown(section_header(
        "TOP 10 SAMOLOTÓW — KONTAKT TERAZ",
        "Posortowane wg daty prognozy · Tylko HIGH/MEDIUM confidence · Aktywne",
        accent="#ef4444",
    ), unsafe_allow_html=True)

    top10 = (
        active[
            active["priorytet_smart"].isin(["TERAZ (zaległe)", "TERAZ", "6 mies."]) &
            active["confidence"].isin(["HIGH", "MEDIUM"])
        ]
        .sort_values("mies_do_next_smart")
        .head(10)
    )

    if top10.empty:
        st.info("Brak samolotów z HIGH/MEDIUM w oknie decyzyjnym.")
    else:
        COLS_MAP = {
            "priorytet_smart":    "Priorytet",
            "registration":       "Rejestracja",
            "icao_operator":      "Operator",
            "confidence":         "Conf.",
            "ostatni_c_check":    "Ostatni C-check",
            "predicted_next_smart": "Prognoza",
            "mies_do_next_smart": "Za (mies.)",
            "interval_source":    "Źródło int.",
            "mro_facility":       "MRO",
        }
        exist = {k: v for k, v in COLS_MAP.items() if k in top10.columns}
        show = top10[list(exist.keys())].rename(columns=exist).copy()

        if "Priorytet" in show.columns:
            show["Priorytet"] = show["Priorytet"].map(
                lambda p: f"{PRIORITY_EMOJI.get(p, '⚪')} {p}"
            )
        if "Conf." in show.columns:
            show["Conf."] = show["Conf."].map(
                lambda c: f"{CONFIDENCE_EMOJI.get(c, '⚪')} {c}"
            )
        for dcol in ["Ostatni C-check", "Prognoza"]:
            if dcol in show.columns:
                show[dcol] = pd.to_datetime(show[dcol], errors="coerce").dt.strftime("%b %Y")
        if "Za (mies.)" in show.columns:
            show["Za (mies.)"] = show["Za (mies.)"].round(1)

        def _style_row(row):
            p = str(row.get("Priorytet", ""))
            if "zaległe" in p:
                return ["background-color:#7f1d1d; color:#fef2f2"] * len(row)
            if "TERAZ" in p:
                return ["background-color:#991b1b; color:#fef2f2"] * len(row)
            if "6 mies" in p:
                return ["background-color:#78350f; color:#fef3c7"] * len(row)
            return [""] * len(row)

        styled = show.style.apply(_style_row, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True, height=400)
        st.markdown(
            '<p style="color:#64748b;font-size:0.82rem;margin-top:4px;">'
            '📋 Pełna lista z filtrami → <b>Fleet Priority</b> &nbsp;·&nbsp; '
            '📣 Alerty sprzedażowe → <b>Commercial Alerts</b> &nbsp;·&nbsp; '
            '🧠 Mapa MRO + ML → <b>ML Insights</b></p>',
            unsafe_allow_html=True,
        )

    # ── PANEL 4: Operator breakdown ───────────────────────────────────────────────
    st.markdown(section_header(
        "TOP OPERATORZY W OKNIE DECYZYJNYM",
        "Ile samolotów per operator wchodzi w TERAZ + 6 mies.",
        accent="#fbbf24",
    ), unsafe_allow_html=True)

    col_bar, col_conf = st.columns([3, 2])

    with col_bar:
        urgent = active[
            active["priorytet_smart"].isin(["TERAZ (zaległe)", "TERAZ", "6 mies."]) &
            active["icao_operator"].notna()
        ]
        if not urgent.empty:
            op_counts = (
                urgent.groupby("icao_operator")
                .agg(
                    Samoloty=("registration", "count"),
                    HIGH=("confidence", lambda x: (x == "HIGH").sum()),
                    MEDIUM=("confidence", lambda x: (x == "MEDIUM").sum()),
                )
                .reset_index()
                .rename(columns={"icao_operator": "Operator"})
                .sort_values("Samoloty", ascending=True)
                .tail(15)
            )
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                y=op_counts["Operator"],
                x=op_counts["HIGH"],
                name="HIGH",
                orientation="h",
                marker_color="#16a34a",
                text=op_counts["HIGH"],
                textposition="inside",
            ))
            fig_bar.add_trace(go.Bar(
                y=op_counts["Operator"],
                x=op_counts["MEDIUM"],
                name="MEDIUM",
                orientation="h",
                marker_color="#d97706",
                text=op_counts["MEDIUM"],
                textposition="inside",
            ))
            fig_bar.update_layout(
                barmode="stack",
                xaxis=dict(title="Samoloty w oknie C-check", color="#94a3b8",
                           gridcolor="#334155", zerolinecolor="#334155"),
                yaxis=dict(title="", color="#94a3b8"),
                paper_bgcolor="#1e293b",
                plot_bgcolor="#1e293b",
                font=dict(color="#cbd5e1", size=11),
                legend=dict(orientation="h", y=-0.15, font=dict(color="#94a3b8")),
                height=350,
                margin=dict(l=20, r=20, t=10, b=40),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_conf:
        st.markdown(action_box(
            "JAK CZYTAĆ CONFIDENCE",
            """
            <b>🟢 HIGH</b> — gap w dedykowanym MRO (EPWA Warszawa, LBSF Sofia, LKMT Katowice...).
            Niemal pewny C-check.<br><br>
            <b>🟡 MEDIUM</b> — hub lotniczy z możliwościami MRO (EHAM, LTBA, EDDH...).
            Prawdopodobny C-check, możliwy heavy maintenance innego typu.<br><br>
            <b>🔴 LOW</b> — przerwa poza wykazem MRO. ML ocenił jako możliwy C-check
            na podstawie 48 cech (długość, aktywność, operator, historię).
            """,
            accent="#3b82f6",
        ), unsafe_allow_html=True)

        st.markdown(action_box(
            "ŹRÓDŁA INTERWAŁÓW",
            """
            <b>per_aircraft</b> — min. 2 wykryte C-checki tego samolotu (≥180d między nimi).<br>
            <b>operator</b> — średnia per_aircraft u tego samego operatora.<br>
            <b>global_mean</b> — średnia ze wszystkich znanych interwałów (≥20 samolotów).<br>
            <b>fallback</b> — 730 dni (24 mies.) gdy brak historii.
            """,
            accent="#8b5cf6",
        ), unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#475569;font-size:0.75rem;text-align:center;">'
        'Dane: EUROCONTROL OPDI · 7M+ lotów B737 EU · 2023-01 → 2026-04 · '
        'LightGBM AUC 0.975 · Klasyfikacja ADS-B = sygnał pośredni, nie dokumentacja MRO'
        '</p>',
        unsafe_allow_html=True,
    )


pg = st.navigation(
    {
        "": [
            st.Page(_render_overview, title="Executive Overview", icon="🏠", default=True),
        ],
        "Analiza floty": [
            st.Page("pages/01_fleet.py",    title="Fleet Priority",    icon="✈️"),
            st.Page("pages/02_aircraft.py", title="Aircraft Deep Dive", icon="🔍"),
            st.Page("pages/03_alerts.py",   title="Commercial Alerts", icon="🚨"),
            st.Page("pages/04_insights.py", title="ML Insights",       icon="🧠"),
        ],
    },
    position="sidebar",
)
pg.run()
