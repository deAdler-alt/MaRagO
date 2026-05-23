"""Strona 4: ML Insights & Market Intelligence — mapy, heatmapy, feature importance."""

from __future__ import annotations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from app.data_loader import load_dashboard, load_candidates
from app.style import kpi_card, section_header, page_header, action_box


# ── Dane ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_insights_data():
    candidates = load_candidates()
    feature_imp_path = Path(__file__).resolve().parents[2] / "output" / "feature_importance.csv"
    fi = pd.read_csv(feature_imp_path) if feature_imp_path.exists() else pd.DataFrame()
    return candidates, fi

candidates, fi = load_insights_data()
dashboard = load_dashboard()

confirmed = (
    candidates[candidates["c_check_probability"] > 0.7].copy()
    if not candidates.empty and "c_check_probability" in candidates.columns
    else pd.DataFrame()
)

# ── Koordinaty lotnisk MRO ────────────────────────────────────────────────────
AIRPORT_META = {
    "LTBA": (40.976, 28.815, "Istanbul Atatürk", "TR"),
    "LTFM": (41.275, 28.752, "Istanbul (YAI)", "TR"),
    "LTFJ": (40.899, 29.309, "Istanbul Sabiha", "TR"),
    "LTAI": (36.899, 30.800, "Antalya", "TR"),
    "LTFE": (37.251, 27.664, "Bodrum-Milas", "TR"),
    "EGSH": (52.676, 1.283,  "Norwich",        "UK"),
    "EGPK": (55.509, -4.587, "Prestwick",       "UK"),
    "EGDX": (51.404, -3.435, "St Athan (MOD)",  "UK"),
    "EGCC": (53.354, -2.275, "Manchester",      "UK"),
    "EGGW": (51.875, -0.368, "Luton",           "UK"),
    "EGSS": (51.885,  0.235, "Stansted",        "UK"),
    "EGBB": (52.454, -1.748, "Birmingham",      "UK"),
    "EGNM": (53.866, -1.661, "Leeds Bradford",  "UK"),
    "EGHL": (51.187, -1.036, "Lasham",          "UK"),
    "EINN": (52.702, -8.924, "Shannon",         "IE"),
    "EIDW": (53.421, -6.270, "Dublin",          "IE"),
    "LFSB": (47.590,  7.530, "Basel-Mulhouse",  "CH"),
    "LSGG": (46.238,  6.109, "Geneva",          "CH"),
    "LHBP": (47.430, 19.261, "Budapest",        "HU"),
    "LKPR": (50.101, 14.260, "Praha",           "CZ"),
    "LKMT": (49.696, 18.111, "Ostrava",         "CZ"),
    "EHAM": (52.308,  4.764, "Amsterdam",       "NL"),
    "LGAV": (37.936, 23.945, "Athens",          "GR"),
    "EPWA": (52.166, 20.967, "Warszawa (LOTAMS)","PL"),
    "LZIB": (48.170, 17.213, "Bratislava",      "SK"),
    "LBSF": (42.697, 23.411, "Sofia",           "BG"),
    "LROP": (44.572, 26.102, "Bucharest",       "RO"),
    "LRBS": (44.503, 26.102, "Bucharest Baneasa","RO"),
    "EDDH": (53.630,  9.988, "Hamburg",         "DE"),
    "EDDM": (48.354, 11.786, "Munich",          "DE"),
    "EDDN": (49.499, 11.067, "Nuremberg",       "DE"),
    "EDLP": (51.614,  8.616, "Paderborn",       "DE"),
    "LFPO": (48.723,  2.359, "Paris Orly",      "FR"),
    "LFLL": (45.726,  5.088, "Lyon",            "FR"),
    "LIRA": (41.799, 12.595, "Rome Ciampino",   "IT"),
    "LPPT": (38.776, -9.135, "Lisbon",          "PT"),
    "LEMD": (40.494, -3.567, "Madrid",          "ES"),
    "EETN": (59.413, 24.833, "Tallinn",         "EE"),
    "LYBE": (44.818, 20.309, "Belgrade",        "RS"),
    "HEAZ": (30.080, 31.380, "Cairo Almaza",    "EG"),
    "GMMN": (33.368, -7.590, "Casablanca",      "MA"),
}

COUNTRY_COLORS = {
    "TR": "#ef4444", "UK": "#3b82f6", "DE": "#f59e0b", "FR": "#8b5cf6",
    "NL": "#06b6d4", "PL": "#16a34a", "CZ": "#f97316", "SK": "#ec4899",
    "HU": "#14b8a6", "BG": "#84cc16", "RO": "#a855f7", "IE": "#22c55e",
    "CH": "#64748b", "GR": "#e11d48", "IT": "#0ea5e9", "EE": "#7c3aed",
    "RS": "#d97706", "EG": "#9ca3af", "MA": "#6b7280", "PT": "#10b981",
}

# ── Nagłówek ─────────────────────────────────────────────────────────────────
st.markdown(page_header(
    "ML Insights & Market Intelligence",
    "Transparentność modelu · Mapa aktywności MRO · Sezonowość C-checków · Feature importance",
    "🧠",
), unsafe_allow_html=True)

# ── PANEL 1: KPI tiles ────────────────────────────────────────────────────────
n_confirmed = len(confirmed) if not confirmed.empty else 0
n_airports  = confirmed["ades"].nunique() if not confirmed.empty else 0
n_operators = confirmed["icao_operator"].dropna().nunique() if not confirmed.empty else 0
top_feat    = fi.iloc[0]["feature"] if not fi.empty else "—"

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card(f"{n_confirmed:,}", "Potwierdzonych C-checków", "c_check_prob > 0.7",
    bg="#14532d", accent="#4ade80", text_color="#f0fdf4"), unsafe_allow_html=True)
c2.markdown(kpi_card(str(n_airports), "Lotnisk MRO w EU",  "unikalne ades",
    bg="#1e3a8a", accent="#60a5fa", text_color="#eff6ff"), unsafe_allow_html=True)
c3.markdown(kpi_card(str(n_operators), "Operatorów", "z historią C-check",
    bg="#78350f", accent="#fbbf24", text_color="#fef3c7"), unsafe_allow_html=True)
c4.markdown(kpi_card(top_feat, "Top feature ML", "najwyższy information gain",
    bg="#1e293b", accent="#8b5cf6"), unsafe_allow_html=True)

st.markdown("<div style='margin:10px 0'></div>", unsafe_allow_html=True)

# ── PANEL 2: Mapa MRO ─────────────────────────────────────────────────────────
st.markdown(section_header(
    "MAPA AKTYWNOŚCI MRO — EUROPA",
    "Bańki = liczba potwierdzonych C-checków (prob > 0.7) · Kolor = kraj · Hover po szczegóły",
    accent="#3b82f6",
), unsafe_allow_html=True)

if not confirmed.empty:
    airport_counts = confirmed["ades"].value_counts().reset_index()
    airport_counts.columns = ["ades", "n_checks"]

    map_rows = []
    for _, row in airport_counts.iterrows():
        code = row["ades"]
        if code in AIRPORT_META:
            lat, lon, name, country = AIRPORT_META[code]
            map_rows.append({
                "ades": code, "lat": lat, "lon": lon,
                "name": name, "country": country,
                "n_checks": row["n_checks"],
                "color": COUNTRY_COLORS.get(country, "#64748b"),
            })

    map_df = pd.DataFrame(map_rows)

    if not map_df.empty:
        fig_map = go.Figure()

        for country, grp in map_df.groupby("country"):
            color = COUNTRY_COLORS.get(country, "#64748b")
            fig_map.add_trace(go.Scattergeo(
                lat=grp["lat"],
                lon=grp["lon"],
                mode="markers",
                name=country,
                marker=dict(
                    size=grp["n_checks"] ** 0.55 * 4,
                    color=color,
                    opacity=0.85,
                    line=dict(color="white", width=0.5),
                    sizemode="diameter",
                ),
                text=[
                    f"<b>{r['name']} ({r['ades']})</b><br>"
                    f"C-checki: {r['n_checks']}<br>"
                    f"Kraj: {r['country']}"
                    for _, r in grp.iterrows()
                ],
                hovertemplate="%{text}<extra></extra>",
            ))

        # LOTAMS highlight
        epwa = map_df[map_df["ades"] == "EPWA"]
        if not epwa.empty:
            fig_map.add_trace(go.Scattergeo(
                lat=epwa["lat"], lon=epwa["lon"],
                mode="markers+text",
                name="LOTAMS (EPWA)",
                marker=dict(size=22, color="#fbbf24", symbol="star",
                            line=dict(color="white", width=1.5)),
                text=["⭐ LOTAMS"],
                textposition="top center",
                textfont=dict(color="#fbbf24", size=12),
                hovertemplate="<b>Warszawa Okęcie (EPWA)</b><br>LOTAMS HQ<br>C-checki: "
                              + str(epwa["n_checks"].values[0]) + "<extra></extra>",
            ))

        fig_map.update_geos(
            scope="europe",
            showland=True, landcolor="#1e293b",
            showocean=True, oceancolor="#0f172a",
            showcoastlines=True, coastlinecolor="#334155",
            showcountries=True, countrycolor="#334155",
            showframe=False,
            projection_type="natural earth",
            center=dict(lat=50, lon=15),
            lataxis_range=[30, 72],
            lonaxis_range=[-15, 45],
        )
        fig_map.update_layout(
            paper_bgcolor="#0f172a",
            font=dict(color="#94a3b8"),
            height=480,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                orientation="h", y=-0.05, x=0,
                font=dict(color="#94a3b8", size=10),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=True,
        )
        st.plotly_chart(fig_map, use_container_width=True)

        col_info, col_top = st.columns([1, 2])
        with col_info:
            st.markdown(action_box(
                "CO WIDZISZ NA MAPIE",
                "Każda bańka = lotnisko MRO gdzie wykryliśmy C-checki B737.<br>"
                "Rozmiar bańki ∝ liczba C-checków.<br>"
                "⭐ Żółta gwiazda = LOTAMS Warszawa.<br><br>"
                "<b>Turcja dominuje</b> (LTBA + LTFM + LTFJ = 666 C-checków) — "
                "Turkish Technic to największy competitor w EU dla LOTAMS.",
                accent="#3b82f6",
            ), unsafe_allow_html=True)
        with col_top:
            top_airports = map_df.sort_values("n_checks", ascending=False).head(10)[
                ["name", "ades", "country", "n_checks"]
            ].rename(columns={"name": "Lotnisko", "ades": "ICAO",
                               "country": "Kraj", "n_checks": "C-checki"})
            st.dataframe(top_airports, use_container_width=True, hide_index=True)

# ── PANEL 3: Sezonowość ────────────────────────────────────────────────────────
st.markdown(section_header(
    "SEZONOWOŚĆ C-CHECKÓW — KIEDY NAJLEPIEJ PROSPECTOWAĆ",
    "Potwierdzone C-checki (prob > 0.7) per miesiąc · Wyraźny wzorzec zimowy",
    accent="#f59e0b",
), unsafe_allow_html=True)

col_heat1, col_heat2 = st.columns([2, 3])

if not confirmed.empty:
    confirmed_ts = confirmed.copy()
    confirmed_ts["month"] = pd.to_datetime(confirmed_ts["last_seen"]).dt.month
    confirmed_ts["year"] = pd.to_datetime(confirmed_ts["last_seen"]).dt.year

    with col_heat1:
        # Heatmap rok × miesiąc
        pivot_ym = (
            confirmed_ts[confirmed_ts["year"] < 2026]
            .groupby(["year", "month"]).size()
            .unstack(fill_value=0)
        )
        month_names = ["Sty","Lut","Mar","Kwi","Maj","Cze","Lip","Sie","Wrz","Paź","Lis","Gru"]
        col_labels = [month_names[c-1] for c in pivot_ym.columns]

        fig_heat = go.Figure(go.Heatmap(
            z=pivot_ym.values,
            x=col_labels,
            y=pivot_ym.index.astype(str),
            colorscale=[
                [0.0, "#1e293b"], [0.3, "#1e3a8a"],
                [0.6, "#f59e0b"], [1.0, "#ef4444"],
            ],
            text=pivot_ym.values,
            texttemplate="%{text}",
            textfont=dict(size=11, color="white"),
            hovertemplate="<b>%{y} %{x}</b><br>C-checki: %{z}<extra></extra>",
            showscale=True,
            colorbar=dict(
                tickfont=dict(color="#94a3b8"),
                outlinecolor="#334155",
            ),
        ))
        fig_heat.update_layout(
            title=dict(text="C-checki per rok × miesiąc",
                       font=dict(color="#94a3b8", size=12)),
            paper_bgcolor="#1e293b",
            plot_bgcolor="#1e293b",
            font=dict(color="#94a3b8"),
            xaxis=dict(color="#94a3b8", tickangle=-30),
            yaxis=dict(color="#94a3b8"),
            height=250,
            margin=dict(l=50, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown(action_box(
            "INSIGHT: NAJLEPSZA PORA NA PROSPECTING",
            "C-checki B737 skupiają się w <b>październiku–marcu</b> (szczyt zimowy).<br>"
            "Okno decyzyjne = 12 mies. przed → "
            "<b>prospectuj od października do marca poprzedniego roku</b>.<br>"
            "Sezon letni (maj–sierpień) = minimum → wtedy samoloty latają, nie serwisują.",
            accent="#f59e0b",
        ), unsafe_allow_html=True)

    with col_heat2:
        # Operator × miesiąc heatmap
        op_month = (
            confirmed_ts[confirmed_ts["icao_operator"].notna()]
            .groupby(["icao_operator", "month"]).size()
            .unstack(fill_value=0)
        )
        top_op_names = confirmed_ts["icao_operator"].value_counts().head(12).index
        op_heat_data = op_month.loc[op_month.index.isin(top_op_names)]
        col_labels_op = [month_names[c-1] for c in op_heat_data.columns]

        fig_op = go.Figure(go.Heatmap(
            z=op_heat_data.values,
            x=col_labels_op,
            y=op_heat_data.index.tolist(),
            colorscale=[
                [0.0, "#1e293b"], [0.3, "#1e3a8a"],
                [0.6, "#f59e0b"], [1.0, "#ef4444"],
            ],
            text=op_heat_data.values,
            texttemplate="%{text}",
            textfont=dict(size=10, color="white"),
            hovertemplate="<b>%{y} — %{x}</b><br>C-checki: %{z}<extra></extra>",
            showscale=False,
        ))
        fig_op.update_layout(
            title=dict(text="Top 12 operatorów × miesiąc (sezonowość flot)",
                       font=dict(color="#94a3b8", size=12)),
            paper_bgcolor="#1e293b",
            plot_bgcolor="#1e293b",
            font=dict(color="#94a3b8"),
            xaxis=dict(color="#94a3b8", tickangle=-30),
            yaxis=dict(color="#94a3b8", autorange="reversed"),
            height=380,
            margin=dict(l=60, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_op, use_container_width=True)

# ── PANEL 4: ML Feature Importance ───────────────────────────────────────────
st.markdown(section_header(
    "DLACZEGO MODEL MÓWI 'C-CHECK' — FEATURE IMPORTANCE",
    "LightGBM information gain · Im dłuższy słupek, tym ważniejszy sygnał",
    accent="#8b5cf6",
), unsafe_allow_html=True)

col_fi, col_fi_txt = st.columns([3, 2])

with col_fi:
    if not fi.empty:
        fi_plot = fi.sort_values("importance_gain", ascending=True).tail(16)
        # Czytelne nazwy
        FEAT_LABELS = {
            "gap_days":                              "Długość przerwy (dni)",
            "ades_country":                          "Kraj lotniska MRO",
            "flights_per_day_pre_gap":               "Loty/dzień przed przerwą",
            "avg_flight_duration_pre_gap_hours":     "Śr. długość lotu (h)",
            "same_country_after":                    "Ten sam kraj po przerwie",
            "distinct_airports_pre_gap":             "Liczba lotnisk przed przerwą",
            "operator_fleet_size":                   "Wielkość floty operatora",
            "registration_country":                  "Kraj rejestracji",
            "interval_to_previous_days":             "Interwał do poprzedniego C-check",
            "gap_at_operator_typical_mro":           "Przerwa w typowym MRO operatora",
            "gap_start_month":                       "Miesiąc początku przerwy",
            "destination_country_matches_registration": "Kraj = kraj rejestracji",
            "gap_start_dow":                         "Dzień tygodnia początku przerwy",
            "num_previous_c_checks":                 "Liczba poprzednich C-checków",
            "mean_interval_prev_c_checks":           "Śr. interwał historyczny",
            "same_operator_after":                   "Ten sam operator po przerwie",
            "typecode":                              "Typ samolotu (B737 variant)",
            "aircraft_age_years":                    "Wiek samolotu / wariantu (lata)",
            "flights_per_day_trend":                 "Trend aktywności (14d/60d przed przerwą)",
            "days_to_first_flight_after":            "Dni do kolejnego lotu po powrocie",
            "at_operator_main_base":                 "Przerwa w bazie własnej operatora",
        }
        fi_plot["label"] = fi_plot["feature"].map(FEAT_LABELS).fillna(fi_plot["feature"])
        fi_plot["gain_pct"] = fi_plot["importance_gain"] / fi_plot["importance_gain"].sum() * 100

        bar_colors = ["#ef4444" if i >= len(fi_plot) - 3
                      else "#3b82f6" if i >= len(fi_plot) - 6
                      else "#475569"
                      for i in range(len(fi_plot))]

        fig_fi = go.Figure(go.Bar(
            x=fi_plot["gain_pct"],
            y=fi_plot["label"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"{v:.1f}%" for v in fi_plot["gain_pct"]],
            textposition="outside",
            textfont=dict(color="#94a3b8", size=11),
            hovertemplate="<b>%{y}</b><br>Gain: %{x:.1f}%<extra></extra>",
        ))
        fig_fi.update_layout(
            xaxis=dict(title="% Information Gain", color="#94a3b8",
                       gridcolor="#334155", range=[0, fi_plot["gain_pct"].max() * 1.2]),
            yaxis=dict(color="#94a3b8"),
            paper_bgcolor="#1e293b",
            plot_bgcolor="#1e293b",
            font=dict(color="#cbd5e1"),
            height=420,
            margin=dict(l=20, r=80, t=10, b=40),
        )
        st.plotly_chart(fig_fi, use_container_width=True)

with col_fi_txt:
    st.markdown(action_box(
        "🔴 TOP SYGNAŁY C-CHECK",
        "<b>1. Długość przerwy</b> — C-check trwa 21–55 dni, A-check 1–3. "
        "To najbardziej dyskryminujący sygnał (31% gain).<br><br>"
        "<b>2. Kraj lotniska MRO</b> — Turcja, Czechy, Polska, Wielka Brytania "
        "to państwa ze specjalistycznym MRO B737. "
        "Przerwa w TR/PL/CZ/UK to silny sygnał (28%).",
        accent="#ef4444",
    ), unsafe_allow_html=True)

    st.markdown(action_box(
        "🔵 KONTEKST OPERACYJNY",
        "<b>3. Intensywność przed przerwą</b> — charter (TUI, SunExpress) "
        "ma wysoki wskaźnik lotów/dzień, potem pełna przerwa = storage zimowy. "
        "Niski wskaźnik + przerwa = C-check (9%).<br><br>"
        "<b>4. Długość lotu</b> — C-check operator lata długo między przerwami, "
        "storage jest z krótkim zasięgiem.",
        accent="#3b82f6",
    ), unsafe_allow_html=True)

    st.markdown(action_box(
        "⚡ DLACZEGO TO DZIAŁA",
        "Model AUC 0.975 na danych których nigdy nie widział "
        "(holdout 2025-07 → 2026-04).<br>"
        "Precision@200 = 0.950 — 190 na 200 top predykcji to faktyczne C-checki.<br><br>"
        "Pseudo-labelling z reguł domeny → ML uczy się wzorców których reguły nie widzą "
        "(np. storage zimowy vs C-check w Turcji).",
        accent="#8b5cf6",
    ), unsafe_allow_html=True)

# ── PANEL 5: Probability distribution ────────────────────────────────────────
st.markdown(section_header(
    "ROZKŁAD PRAWDOPODOBIEŃSTWA C-CHECK",
    "Histogram predykcji modelu dla wszystkich 3 651 kandydatów",
    accent="#4ade80",
), unsafe_allow_html=True)

col_hist, col_hist_txt = st.columns([3, 2])

with col_hist:
    if not candidates.empty and "c_check_probability" in candidates.columns:
        probs = candidates["c_check_probability"].dropna()

        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=probs[probs < 0.7],
            nbinsx=30,
            name="prob < 0.7 (nie-C-check)",
            marker_color="#475569",
            opacity=0.8,
        ))
        fig_hist.add_trace(go.Histogram(
            x=probs[probs >= 0.7],
            nbinsx=15,
            name="prob ≥ 0.7 (potwierdzony C-check)",
            marker_color="#ef4444",
            opacity=0.9,
        ))
        fig_hist.add_vline(
            x=0.7, line_dash="dash", line_color="#fbbf24", line_width=2,
            annotation_text="Próg 0.7",
            annotation_font=dict(color="#fbbf24"),
        )
        fig_hist.update_layout(
            barmode="overlay",
            xaxis=dict(title="c_check_probability", color="#94a3b8",
                       gridcolor="#334155", range=[0, 1]),
            yaxis=dict(title="Liczba kandydatów", color="#94a3b8", gridcolor="#334155"),
            paper_bgcolor="#1e293b",
            plot_bgcolor="#1e293b",
            font=dict(color="#cbd5e1"),
            legend=dict(font=dict(color="#94a3b8"), bgcolor="rgba(0,0,0,0)"),
            height=280,
            margin=dict(l=20, r=20, t=10, b=40),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with col_hist_txt:
    if not candidates.empty and "c_check_probability" in candidates.columns:
        n_high_prob = (candidates["c_check_probability"] >= 0.7).sum()
        n_low_prob  = (candidates["c_check_probability"] < 0.3).sum()
        n_mid_prob  = len(candidates) - n_high_prob - n_low_prob
        avg_prob    = candidates["c_check_probability"].mean()

        st.markdown(action_box(
            "INTERPRETACJA HISTOGRAMU",
            f"<b>{n_high_prob}</b> kandydatów potwierdzonych (prob ≥ 0.7) → C-checki pewne lub prawie pewne<br>"
            f"<b>{n_mid_prob}</b> w strefie szarej (0.3–0.7) → ambiguous, obserwuj<br>"
            f"<b>{n_low_prob}</b> odrzuconych (prob < 0.3) → storage, AOG, parking<br><br>"
            f"Śr. prob dla wszystkich: <b>{avg_prob:.3f}</b>",
            accent="#4ade80",
        ), unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    '<p style="color:#475569;font-size:0.75rem;text-align:center;">'
    'LightGBM binary classifier · AUC 0.975 · Time-based holdout 2025-07 → 2026-04 · '
    'EUROCONTROL OPDI 7M+ lotów · Dane: sygnał ADS-B, nie dokumentacja MRO</p>',
    unsafe_allow_html=True,
)
