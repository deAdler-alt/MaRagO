"""Strona 2: Aircraft Deep Dive — historia i prognoza per samolot."""

from __future__ import annotations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.data_loader import (
    load_dashboard,
    load_candidates,
    PRIORITY_EMOJI,
    CONFIDENCE_EMOJI,
    PRIORITY_BG,
    months_label,
)
from app.style import (
    GLOBAL_CSS,
    kpi_card,
    section_header,
    page_header,
    action_box,
    PRIORITY_COLORS,
)

st.set_page_config(page_title="Aircraft Detail | MRO Intelligence", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Dane ─────────────────────────────────────────────────────────────────────
dashboard = load_dashboard()
candidates = load_candidates()

if dashboard.empty:
    st.error("Brak danych. Uruchom pipeline.")
    st.stop()

# ── Sidebar: wybór samolotu ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Wybierz samolot")
    st.caption("Domyślnie: samoloty z najwyższym priorytetem C-check")

    search_reg = st.text_input("Szukaj po rejestracji", "").upper().strip()

    priority_default = dashboard[
        dashboard["priorytet_smart"].isin(["TERAZ (zaległe)", "TERAZ", "6 mies."]) &
        dashboard["confidence"].isin(["HIGH", "MEDIUM"])
    ].sort_values("mies_do_next_smart")

    registrations_all = sorted(dashboard["registration"].dropna().unique())
    if search_reg:
        registrations_filtered = [r for r in registrations_all if search_reg in r]
    else:
        priority_regs = priority_default["registration"].tolist()
        other_regs = [r for r in registrations_all if r not in priority_regs]
        registrations_filtered = priority_regs + other_regs

    if not registrations_filtered:
        registrations_filtered = registrations_all

    registration = st.selectbox("Rejestracja", registrations_filtered, index=0)

    st.markdown("---")
    prob_threshold = st.slider(
        "ML probability threshold",
        min_value=0.0, max_value=1.0, value=0.3, step=0.05,
        help="Pokaż przerwy z c_check_probability ≥ progu · Zmień żeby zobaczyć jak klasyfikacja się zmienia",
    )
    st.caption("prob < 0.3 → 🟡 storage/AOG | prob ≥ 0.3 → C-check candidate")
    st.markdown("---")
    st.markdown(action_box(
        "CO WIDZISZ NA WYKRESIE",
        "Każdy prostokąt = wykryta przerwa w lotach tego samolotu.<br>"
        "<b style='color:#4ade80'>Zielony</b> = HIGH (potw. MRO hub)<br>"
        "<b style='color:#fcd34d'>Żółty</b> = MEDIUM (możliwy MRO)<br>"
        "<b style='color:#94a3b8'>Szary</b> = LOW (ML candidate)<br>"
        "Czerwona linia = prognoza next C-check.",
        accent="#3b82f6",
    ), unsafe_allow_html=True)

# ── Dane per samolot ──────────────────────────────────────────────────────────
aircraft_row = dashboard[dashboard["registration"] == registration]
aircraft_cands = (
    candidates[candidates["registration"] == registration].sort_values("last_seen")
    if not candidates.empty else pd.DataFrame()
)

if aircraft_row.empty:
    st.warning(f"Brak danych dla {registration}")
    st.stop()

row = aircraft_row.iloc[0]
priority = row.get("priorytet_smart", "Daleko")
confidence = row.get("confidence", "LOW")
p_colors = PRIORITY_COLORS.get(priority, {"bg": "#1e293b", "accent": "#64748b", "text": "#e2e8f0"})

# ── Nagłówek samolotu ─────────────────────────────────────────────────────────
is_active_flag = row.get("is_active", False)
active_badge = (
    '<span style="background:#15803d;color:#dcfce7;padding:2px 8px;border-radius:4px;'
    'font-size:0.7rem;font-weight:700;">AKTYWNY</span>'
    if is_active_flag else
    '<span style="background:#374151;color:#9ca3af;padding:2px 8px;border-radius:4px;'
    'font-size:0.7rem;font-weight:700;">NIEAKTYWNY</span>'
)

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, {p_colors['bg']} 0%, #1e293b 100%);
    border-radius: 10px; padding: 20px 24px; margin-bottom: 16px;
    border: 1px solid {p_colors['accent']}40;
    border-left: 5px solid {p_colors['accent']};
">
    <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
        <span style="font-size:2rem;">{PRIORITY_EMOJI.get(priority, '⚪')}</span>
        <h2 style="margin:0; color:{p_colors['text']}; font-size:1.8rem; font-weight:900;">
            {registration}
        </h2>
        <span style="color:{p_colors['accent']};font-size:1rem;font-weight:600;">
            {CONFIDENCE_EMOJI.get(confidence, '⚪')} {confidence}
        </span>
        {active_badge}
        <span style="color:#64748b;font-size:0.9rem;">
            {row.get('icao_operator', '—')} &nbsp;·&nbsp; {row.get('typecode', '—')}
        </span>
    </div>
    <div style="color:{p_colors['accent']};font-size:0.95rem;font-weight:700;margin-top:8px;">
        {priority}
    </div>
</div>
""", unsafe_allow_html=True)

# ── PANEL 1: KPI metryki ──────────────────────────────────────────────────────
last_check = row.get("ostatni_c_check")
last_str = pd.Timestamp(last_check).strftime("%b %Y") if pd.notna(last_check) else "—"

pred_next = row.get("predicted_next_smart")
pred_q = "—"
pred_str = "—"
if pd.notna(pred_next):
    dt = pd.Timestamp(pred_next)
    pred_q = f"Q{(dt.month-1)//3+1} {dt.year}"
    pred_str = dt.strftime("%b %Y")

mies = row.get("mies_do_next_smart")
interval = row.get("interval_days_used")
interval_src = row.get("interval_source", "—")
n_cands = len(aircraft_cands) if not aircraft_cands.empty else 0
n_confirmed = (
    int((aircraft_cands["c_check_probability"] > 0.7).sum())
    if not aircraft_cands.empty and "c_check_probability" in aircraft_cands.columns
    else 0
)

# Łączne godziny lotu (proxy) z features w predictions.csv
fh_est = "—"
if not aircraft_cands.empty and "avg_flight_duration_pre_gap_hours" in aircraft_cands.columns:
    avg_dur = aircraft_cands["avg_flight_duration_pre_gap_hours"].mean()
    fpd = aircraft_cands["flights_per_day_pre_gap"].mean() if "flights_per_day_pre_gap" in aircraft_cands.columns else 6.0
    # proxy: avg_duration * flights/day * ~500 dni aktywnych między sprawdzonymi C-check'ami
    active_days_est = max(n_cands * 500, 365)
    fh_proxy = int(avg_dur * fpd * active_days_est)
    fh_est = f"~{fh_proxy:,} FH"

m1, m2, m3, m4, m5, m6 = st.columns(6)

m1.markdown(kpi_card(last_str, "Ostatni C-check", row.get("mro_facility", ""),
    bg="#1e293b", accent="#4ade80"), unsafe_allow_html=True)
m2.markdown(kpi_card(pred_q, "Prognoza next C-check", pred_str,
    bg=p_colors["bg"], accent=p_colors["accent"], text_color=p_colors["text"]), unsafe_allow_html=True)
m3.markdown(kpi_card(months_label(mies), "Za / temu", "od dziś",
    bg="#1e293b", accent="#f59e0b"), unsafe_allow_html=True)
m4.markdown(kpi_card(
    f"{interval:.0f} dni" if pd.notna(interval) else "—",
    "Interwał C-check", interval_src,
    bg="#1e293b", accent="#8b5cf6"), unsafe_allow_html=True)
m5.markdown(kpi_card(f"{n_confirmed} / {n_cands}", "Potw. / Kandydaci",
    "c_check_prob > 0.7", bg="#1e293b", accent="#3b82f6"), unsafe_allow_html=True)
m6.markdown(kpi_card(fh_est, "Godziny lotu (est.)", "proxy z aktywności",
    bg="#1e293b", accent="#64748b"), unsafe_allow_html=True)

st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

# ── PANEL 2: Gantt timeline ────────────────────────────────────────────────────
st.markdown(section_header(
    "HISTORIA AKTYWNOŚCI & PRZERWY SERWISOWE — TIMELINE",
    "Zielone = okresy lotów · Kolorowe = wykryte przerwy serwisowe · Czerwona linia = prognoza",
    accent="#8b5cf6",
), unsafe_allow_html=True)

ORIGIN = pd.Timestamp("2023-01-01")
NOW_TS = pd.Timestamp("2026-05-23")
# Kolor per kandydat zależy od ML probability (nie tylko reguły confidence):
# prob >= 0.7 → zielony (HIGH) lub pomarańczowy (MEDIUM) — potw. C-check
# prob 0.3–0.7 → szary (LOW) — ambiguous
# prob < 0.3  → żółty — storage/AOG
CONF_COLORS = {"HIGH": "#16a34a", "MEDIUM": "#d97706", "LOW": "#64748b"}
STORAGE_COLOR = "#f59e0b"   # żółty = storage/AOG

def _bar_color(cand: "pd.Series") -> str:
    prob = cand.get("c_check_probability")
    if pd.notna(prob) and float(prob) < 0.3:
        return STORAGE_COLOR
    return CONF_COLORS.get(cand.get("confidence", "LOW"), "#64748b")

# Wszystkie gapy — do wyznaczenia aktywnych okresów (zielone paski)
all_cands_sorted = (
    aircraft_cands.sort_values("last_seen").copy()
    if not aircraft_cands.empty else pd.DataFrame()
)

# Gapy do wyświetlenia: filtruj wg ML probability threshold ze slidera
plot_cands = (
    aircraft_cands[
        aircraft_cands["c_check_probability"].fillna(0) >= prob_threshold
    ] if not aircraft_cands.empty and "c_check_probability" in aircraft_cands.columns
    else aircraft_cands
) if not aircraft_cands.empty else pd.DataFrame()

fig = go.Figure()

# ── Zielone paski aktywności ─────────────────────────────────────────────────
# Wnioskujemy okresy aktywne jako przerwy MIĘDZY gapami.
# Nie ładujemy 7M lotów — wystarczą nam daty graniczne gapów.
active_legend_added = False
if not all_cands_sorted.empty:
    # Zbierz wszystkie okna (gap_start, gap_end) używając WSZYSTKICH gapów
    gap_windows = []
    for _, cand in all_cands_sorted.iterrows():
        gs = pd.Timestamp(cand["last_seen"])
        ge_raw = cand.get("next_first_seen")
        ge = (
            pd.Timestamp(ge_raw) if pd.notna(ge_raw)
            else gs + pd.Timedelta(days=int(cand["gap_days"]))
        )
        gap_windows.append((gs, ge))

    # Pełne timeline: ORIGIN → max(gap_end, NOW_TS)
    timeline_end = max(max(ge for _, ge in gap_windows), NOW_TS)

    # Aktywne okresy = między gapami (i przed pierwszym i po ostatnim)
    boundaries = sorted(set([ORIGIN] + [t for w in gap_windows for t in w] + [timeline_end]))
    in_gap = set()
    for gs, ge in gap_windows:
        in_gap.add((gs, ge))

    prev = boundaries[0]
    for curr in boundaries[1:]:
        # sprawdź czy przedział (prev, curr) jest wewnątrz jakiegoś gapu
        mid = prev + (curr - prev) / 2
        is_in_gap = any(gs <= mid <= ge for gs, ge in gap_windows)
        if not is_in_gap and (curr - prev).days >= 2:
            w = (curr - prev).total_seconds() / 86400
            o = (prev - ORIGIN).total_seconds() / 86400
            fig.add_trace(go.Bar(
                x=[w], y=[0],
                orientation="h", base=[o],
                width=0.35,
                marker_color="#16a34a",
                marker_line_color="#16a34a",
                opacity=0.55,
                showlegend=not active_legend_added,
                name="✈️ Aktywne loty",
                hovertemplate=(
                    f"Aktywność: {prev.strftime('%b %Y')} → {curr.strftime('%b %Y')}<br>"
                    f"Okres: {(curr-prev).days} dni<extra></extra>"
                ),
            ))
            active_legend_added = True
        prev = curr

# ── Legenda: storage/AOG + C-check warianty ──────────────────────────────────
fig.add_trace(go.Bar(
    x=[0], y=[0], orientation="h", width=0,
    marker_color=STORAGE_COLOR,
    name="🟡 storage/AOG (prob < 0.3)",
    showlegend=True,
))
for conf, color in CONF_COLORS.items():
    fig.add_trace(go.Bar(
        x=[0], y=[0], orientation="h", width=0,
        marker_color=color,
        name=f"{CONFIDENCE_EMOJI.get(conf, '')} {conf} (C-check)",
        showlegend=True,
    ))

if not plot_cands.empty:
    for _, cand in plot_cands.iterrows():
        conf = cand.get("confidence", "LOW")
        bar_color = _bar_color(cand)
        is_storage = bar_color == STORAGE_COLOR
        gs = pd.Timestamp(cand["last_seen"])
        ge_raw = cand.get("next_first_seen")
        ge = (
            pd.Timestamp(ge_raw) if pd.notna(ge_raw)
            else gs + pd.Timedelta(days=int(cand["gap_days"]))
        )
        prob = cand.get("c_check_probability")
        prob_str = f"<br>ML prob: {prob:.3f}" if pd.notna(prob) else ""
        w = (ge - gs).total_seconds() / 86400
        o = (gs - ORIGIN).total_seconds() / 86400

        fig.add_trace(go.Bar(
            x=[w], y=[0],
            orientation="h", base=[o],
            width=0.65,
            marker_color=bar_color,
            marker_line_color=bar_color,
            opacity=0.92,
            showlegend=False,
            hovertemplate=(
                f"<b>{cand.get('ades', '—')}</b> ({cand.get('mro_facility', '—')})<br>"
                f"Typ: {'🟡 storage/AOG' if is_storage else '🔵 C-check candidate'}<br>"
                f"Przerwa: {gs.strftime('%d %b %Y')} → {ge.strftime('%d %b %Y')}<br>"
                f"Długość: {cand['gap_days']:.0f} dni · conf: {conf}"
                f"{prob_str}<extra></extra>"
            ),
        ))
elif aircraft_cands.empty:
    st.info("Brak historii kandydatów C-check dla tego samolotu w bazie danych.")

# ── Linie: dziś + prognoza ────────────────────────────────────────────────────
now_offset = (NOW_TS - ORIGIN).total_seconds() / 86400
fig.add_vline(
    x=now_offset, line_dash="dot", line_color="#64748b", line_width=2,
    annotation_text="Dziś", annotation_font=dict(color="#94a3b8"),
    annotation_position="top left",
)
if pd.notna(pred_next):
    pred_ts = pd.Timestamp(pred_next)
    pred_offset = (pred_ts - ORIGIN).total_seconds() / 86400
    fig.add_vline(
        x=pred_offset, line_dash="dash", line_color="#ef4444", line_width=2,
        annotation_text=f"Prognoza: {pred_str}",
        annotation_font=dict(color="#ef4444"),
        annotation_position="top right",
    )

# ── Oś X: daty ───────────────────────────────────────────────────────────────
ticks_vals, ticks_text = [], []
d = ORIGIN
while d <= pd.Timestamp("2027-06-01"):
    ticks_vals.append((d - ORIGIN).total_seconds() / 86400)
    ticks_text.append(d.strftime("%b %Y"))
    d += pd.DateOffset(months=4)

fig.update_layout(
    barmode="overlay",
    xaxis=dict(
        tickmode="array", tickvals=ticks_vals, ticktext=ticks_text,
        color="#94a3b8", gridcolor="#334155", zerolinecolor="#334155",
        tickangle=-30,
    ),
    yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
    paper_bgcolor="#1e293b",
    plot_bgcolor="#1e293b",
    font=dict(color="#cbd5e1"),
    height=220,
    margin=dict(l=20, r=20, t=10, b=60),
    legend=dict(
        orientation="h", y=-0.55, x=0,
        font=dict(color="#94a3b8", size=11),
        bgcolor="rgba(0,0,0,0)",
    ),
)
st.plotly_chart(fig, use_container_width=True)

# ── PANEL 3: Tabela historii + kontekst ───────────────────────────────────────
col_hist, col_ctx = st.columns([3, 2])

with col_hist:
    st.markdown(section_header(
        "SZCZEGÓŁOWA HISTORIA PRZERW",
        "Wszystkie wykryte przerwy w aktywności ADS-B dla tego samolotu",
        accent="#4ade80",
    ), unsafe_allow_html=True)

    if not aircraft_cands.empty:
        hist_cols = {
            "last_seen": "Ostatni lot",
            "gap_days": "Dni przerwy",
            "ades": "Lotnisko",
            "mro_facility": "Facility",
            "confidence": "Conf.",
            "c_check_probability": "ML Prob.",
            "next_first_seen": "Powrót",
        }
        hc = {k: v for k, v in hist_cols.items() if k in aircraft_cands.columns}
        hist = aircraft_cands[list(hc.keys())].rename(columns=hc).copy()

        for tc in ["Ostatni lot", "Powrót"]:
            if tc in hist.columns:
                hist[tc] = pd.to_datetime(hist[tc], errors="coerce").dt.strftime("%Y-%m-%d")
        if "Dni przerwy" in hist.columns:
            hist["Dni przerwy"] = hist["Dni przerwy"].round(0).astype("Int64")
        if "ML Prob." in hist.columns:
            hist["ML Prob."] = hist["ML Prob."].round(3)
        if "Conf." in hist.columns:
            hist["Conf."] = hist["Conf."].map(lambda c: f"{CONFIDENCE_EMOJI.get(c, '⚪')} {c}")

        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.info("Brak historii dla tego samolotu.")

with col_ctx:
    st.markdown(section_header(
        "KONTEKST SPRZEDAŻOWY",
        "Co wiesz o tym samolocie zanim zadzwonisz",
        accent="#fbbf24",
    ), unsafe_allow_html=True)

    # Podsumowanie per samolot
    if not aircraft_cands.empty and "c_check_probability" in aircraft_cands.columns:
        best_prob = aircraft_cands["c_check_probability"].max()
        n_high_conf = (aircraft_cands["confidence"] == "HIGH").sum()
        avg_gap = aircraft_cands["gap_days"].mean()
        operators_seen = (
            aircraft_cands["icao_operator"].nunique()
            if "icao_operator" in aircraft_cands.columns else "—"
        )

        st.markdown(action_box(
            "ANALIZA HISTORYCZNA",
            f"Wykrytych przerw: <b>{len(aircraft_cands)}</b><br>"
            f"HIGH confidence: <b>{n_high_conf}</b><br>"
            f"Najwyższe ML prob: <b>{best_prob:.3f}</b><br>"
            f"Śr. długość przerwy: <b>{avg_gap:.0f} dni</b><br>"
            f"Operatorów w historii: <b>{operators_seen}</b>",
            accent="#4ade80",
        ), unsafe_allow_html=True)

    contact_date = None
    if pd.notna(pred_next):
        contact_date = pd.Timestamp(pred_next) - pd.DateOffset(months=12)
        contact_str = contact_date.strftime("%B %Y")
        st.markdown(action_box(
            "SUGEROWANY KONTAKT",
            f"Wyślij pierwszą ofertę: <b>{contact_str}</b><br>"
            f"(12 miesięcy przed prognozowanym C-check'iem)<br><br>"
            f"Prognoza: <b>{pred_str}</b> ({pred_q})",
            accent="#ef4444",
        ), unsafe_allow_html=True)

    st.markdown(action_box(
        "DLACZEGO LOTAMS",
        "✔ Specjalizacja B737-NG / MAX<br>"
        "✔ EASA Part-145 certyfikat<br>"
        "✔ EPWA — najlepszy dostęp dla linii CEE<br>"
        "✔ Krótsze kolejki vs HAM / MUC / IST<br>"
        "✔ Konkurencyjna cena dla flot 10-50+ samolotów",
        accent="#8b5cf6",
    ), unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    '<p style="color:#475569;font-size:0.75rem;">'
    'Dane: EUROCONTROL OPDI · Klasyfikacja ADS-B = sygnał pośredni, nie dokumentacja MRO.</p>',
    unsafe_allow_html=True,
)
