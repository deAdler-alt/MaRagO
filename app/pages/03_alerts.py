"""Strona 3: Commercial Alerts — centrum dowodzenia sprzedaży."""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import sys
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.data_loader import (
    load_dashboard,
    load_lotams_clients,
    PRIORITY_EMOJI,
    CONFIDENCE_EMOJI,
    priority_sort_key,
)
from app.style import (
    GLOBAL_CSS,
    kpi_card,
    section_header,
    page_header,
    action_box,
)

st.set_page_config(page_title="Commercial Alerts | MRO Intelligence", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Dane ─────────────────────────────────────────────────────────────────────
dashboard = load_dashboard()
lotams_clients = load_lotams_clients()

if dashboard.empty:
    st.error("Brak danych. Uruchom pipeline.")
    st.stop()

# ── Filtry ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtry alertów")
    st.caption("Zawęź do konkretnego segmentu")

    band_opts = ["TERAZ (zaległe)", "TERAZ", "6 mies.", "12 mies."]
    band_filter = st.multiselect(
        "Pasmo priorytetu",
        band_opts,
        default=["TERAZ (zaległe)", "TERAZ", "6 mies."],
        format_func=lambda p: f"{PRIORITY_EMOJI.get(p, '⚪')} {p}",
    )

    conf_filter = st.multiselect(
        "Confidence",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM"],
        format_func=lambda c: f"{CONFIDENCE_EMOJI.get(c, '⚪')} {c}",
    )

    active_only = st.checkbox("Tylko aktywne samoloty", value=True)
    highlight_lotams = st.checkbox("Wyróżnij klientów LOTAMS", value=True,
                                   help="Samoloty z historycznym gap w EPWA (Warszawa)")

    st.markdown("---")
    st.markdown(action_box(
        "STRATEGIA KONTAKTU",
        "Kontakt zalecany <b>12 miesięcy przed</b> prognozowanym C-check'iem.<br>"
        "⭐ = historyczny klient LOTAMS — priorytet A1.<br>"
        "HIGH + TERAZ = kontaktuj <b>dziś</b>.",
        accent="#ef4444",
    ), unsafe_allow_html=True)

# ── Filtrowanie ───────────────────────────────────────────────────────────────
alerts = dashboard.copy()
if active_only and "is_active" in alerts.columns:
    alerts = alerts[alerts["is_active"]]
if band_filter:
    alerts = alerts[alerts["priorytet_smart"].isin(band_filter)]
# Filtr confidence: reguły lokalizacji LUB ML probability > 0.7 (zgodnie z roadmapą)
if conf_filter and "confidence" in alerts.columns:
    conf_mask = alerts["confidence"].isin(conf_filter)
    if "c_check_probability" in alerts.columns:
        conf_mask = conf_mask | (alerts["c_check_probability"].fillna(0) >= 0.7)
    alerts = alerts[conf_mask]

alerts["_sort_key"] = priority_sort_key(alerts["priorytet_smart"])
alerts = alerts.sort_values(["_sort_key", "mies_do_next_smart"]).drop(columns=["_sort_key"])

if highlight_lotams and not lotams_clients.empty and "registration" in lotams_clients.columns:
    lotams_regs = set(lotams_clients["registration"].dropna())
    alerts["_is_lotams"] = alerts["registration"].isin(lotams_regs)
else:
    alerts["_is_lotams"] = False

if "predicted_next_smart" in alerts.columns:
    alerts["contact_date"] = (
        pd.to_datetime(alerts["predicted_next_smart"], errors="coerce")
        - pd.DateOffset(months=12)
    )

# ── Nagłówek ─────────────────────────────────────────────────────────────────
st.markdown(page_header(
    "Commercial Alerts",
    "Samoloty B737 w oknie decyzyjnym C-check · Centrum dowodzenia sprzedaży LOTAMS",
    "📣",
), unsafe_allow_html=True)

# ── PANEL 1: 4 duże KPI tiles ────────────────────────────────────────────────
n_all      = len(alerts)
n_teraz    = len(alerts[alerts["priorytet_smart"].isin(["TERAZ (zaległe)", "TERAZ"])])
n_szesc    = len(alerts[alerts["priorytet_smart"] == "6 mies."])
n_lotams   = int(alerts["_is_lotams"].sum())
n_high     = len(alerts[alerts["confidence"] == "HIGH"]) if "confidence" in alerts.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card(str(n_all), "Aktywne alerty", "po zastosowanych filtrach",
    bg="#1e293b", accent="#3b82f6"), unsafe_allow_html=True)
c2.markdown(kpi_card(str(n_teraz), "🔴 DZIAŁAJ TERAZ", "0–6 mies. do C-check",
    bg="#7f1d1d", accent="#ef4444", text_color="#fef2f2"), unsafe_allow_html=True)
c3.markdown(kpi_card(str(n_szesc), "🟡 Zaplanuj w Q", "6–12 mies. do C-check",
    bg="#78350f", accent="#fbbf24", text_color="#fef3c7"), unsafe_allow_html=True)
c4.markdown(kpi_card(f"⭐ {n_lotams}", "Klienci LOTAMS", "Historyczne gappy w EPWA",
    bg="#1e3a8a", accent="#60a5fa", text_color="#eff6ff"), unsafe_allow_html=True)

st.markdown("<div style='margin:10px 0'></div>", unsafe_allow_html=True)

# ── PANEL 2: Tabela + operator chart ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Lista alertów", "🏢 Per operator", "📧 Szablony kontaktu"])

# ──────────────────── TAB 1: Lista ────────────────────────────────────────────
with tab1:
    st.markdown(section_header(
        "LISTA ALERTÓW — CO ROBIĆ",
        f"Posortowane wg priorytetu · {n_all} samolotów · Czerwone = działaj teraz",
        accent="#ef4444",
    ), unsafe_allow_html=True)

    SHOW_COLS = {
        "priorytet_smart":    "Priorytet",
        "registration":       "Rejestracja",
        "icao_operator":      "Operator",
        "confidence":         "Conf.",
        "ostatni_c_check":    "Ostatni C-check",
        "predicted_next_smart": "Prognoza C-check",
        "mies_do_next_smart": "Za (mies.)",
        "contact_date":       "Kontakt od",
        "mro_facility":       "Ostatnie MRO",
        "interval_source":    "Źródło int.",
    }
    exist = {k: v for k, v in SHOW_COLS.items() if k in alerts.columns}
    tbl = alerts[list(exist.keys())].rename(columns=exist).copy()

    if "Priorytet" in tbl.columns:
        tbl["Priorytet"] = tbl["Priorytet"].map(lambda p: f"{PRIORITY_EMOJI.get(p, '⚪')} {p}")
    if "Conf." in tbl.columns:
        tbl["Conf."] = tbl["Conf."].map(lambda c: f"{CONFIDENCE_EMOJI.get(c, '⚪')} {c}")
    for dc in ["Ostatni C-check", "Prognoza C-check", "Kontakt od"]:
        if dc in tbl.columns:
            tbl[dc] = pd.to_datetime(tbl[dc], errors="coerce").dt.strftime("%b %Y")
    if "Za (mies.)" in tbl.columns:
        tbl["Za (mies.)"] = tbl["Za (mies.)"].round(1)

    # Oznaczenie klientów LOTAMS
    if "_is_lotams" in alerts.columns and "Rejestracja" in tbl.columns:
        lotams_idx = alerts[alerts["_is_lotams"]].index
        tbl.loc[tbl.index.isin(lotams_idx), "Rejestracja"] = (
            "⭐ " + tbl.loc[tbl.index.isin(lotams_idx), "Rejestracja"]
        )

    def _alert_row_style(row):
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

    styled = tbl.style.apply(_alert_row_style, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True, height=520)

    col_dl, _ = st.columns([2, 8])
    with col_dl:
        csv_out = alerts.drop(columns=["_is_lotams"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("📥 Eksport CSV", csv_out, "mro_alerts.csv", "text/csv")

# ──────────────────── TAB 2: Per operator ─────────────────────────────────────
with tab2:
    st.markdown(section_header(
        "PER-OPERATOR: ILE SAMOLOTÓW W OKNIE",
        "Pogrupowane wg operatora ICAO · Sortowanie wg liczby samolotów",
        accent="#fbbf24",
    ), unsafe_allow_html=True)

    if "icao_operator" not in alerts.columns or alerts["icao_operator"].isna().all():
        st.info("Brak danych operatora.")
    else:
        op_data = alerts[alerts["icao_operator"].notna()].copy()
        op_summary = (
            op_data.groupby("icao_operator")
            .agg(
                Samoloty=("registration", "count"),
                HIGH=("confidence", lambda x: (x == "HIGH").sum()),
                MEDIUM=("confidence", lambda x: (x == "MEDIUM").sum()),
                Najbliższy=("mies_do_next_smart", "min"),
                Śr_interwał=("interval_days_used", "mean"),
            )
            .reset_index()
            .rename(columns={"icao_operator": "Operator"})
            .sort_values("Samoloty", ascending=False)
        )
        op_summary["Najbliższy"] = op_summary["Najbliższy"].round(1)
        op_summary["Śr_interwał"] = op_summary["Śr_interwał"].round(0).astype("Int64")

        col_chart, col_tbl = st.columns([3, 2])

        with col_chart:
            top15 = op_summary.head(15).sort_values("Samoloty", ascending=True)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=top15["Operator"], x=top15["HIGH"],
                name="🟢 HIGH",
                orientation="h", marker_color="#16a34a",
                text=top15["HIGH"], textposition="inside",
                textfont=dict(color="white"),
            ))
            fig.add_trace(go.Bar(
                y=top15["Operator"], x=top15["MEDIUM"],
                name="🟡 MEDIUM",
                orientation="h", marker_color="#d97706",
                text=top15["MEDIUM"], textposition="inside",
                textfont=dict(color="white"),
            ))
            fig.update_layout(
                barmode="stack",
                title=dict(text="Top 15 operatorów — samoloty w oknie C-check",
                           font=dict(color="#94a3b8", size=12)),
                xaxis=dict(title="Samoloty", color="#94a3b8", gridcolor="#334155"),
                yaxis=dict(color="#94a3b8"),
                paper_bgcolor="#1e293b",
                plot_bgcolor="#1e293b",
                font=dict(color="#cbd5e1", size=11),
                legend=dict(orientation="h", y=-0.15, font=dict(color="#94a3b8")),
                height=420,
                margin=dict(l=100, r=20, t=40, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_tbl:
            st.markdown(
                '<p style="color:#94a3b8;font-size:0.8rem;margin:0 0 6px;">Tabela per operator</p>',
                unsafe_allow_html=True,
            )
            st.dataframe(op_summary.head(20), use_container_width=True, hide_index=True, height=400)

# ──────────────────── TAB 3: Szablony ─────────────────────────────────────────
with tab3:
    st.markdown(section_header(
        "GENERATOR SZABLONU E-MAIL",
        "Wybierz samolot → kliknij Generuj → wklej do klienta pocztowego lub CRM",
        accent="#8b5cf6",
    ), unsafe_allow_html=True)

    reg_list = alerts["registration"].dropna().tolist()
    if not reg_list:
        st.warning("Brak alertów z wybranym filtrem — zmień filtry w sidebarze.")
    else:
        col_sel, col_meta = st.columns([2, 3])

        with col_sel:
            selected_reg = st.selectbox("Wybierz rejestrację", reg_list)

        row_a = alerts[alerts["registration"] == selected_reg].iloc[0]

        pred_q = "—"
        if pd.notna(row_a.get("predicted_next_smart")):
            dt = pd.Timestamp(row_a["predicted_next_smart"])
            pred_q = f"Q{(dt.month-1)//3+1} {dt.year}"
            pred_str_t = dt.strftime("%B %Y")
        else:
            pred_str_t = "—"

        contact_str = "—"
        if pd.notna(row_a.get("contact_date")):
            contact_str = pd.Timestamp(row_a["contact_date"]).strftime("%B %Y")

        last_str_t = "—"
        if pd.notna(row_a.get("ostatni_c_check")):
            last_str_t = pd.Timestamp(row_a["ostatni_c_check"]).strftime("%B %Y")

        operator  = row_a.get("icao_operator", "?")
        typecode  = row_a.get("typecode", "B737")
        gap_days  = row_a.get("czas_dni", "?")
        mro       = row_a.get("mro_facility", "nieznane MRO")
        confidence_t = row_a.get("confidence", "LOW")
        interval_t   = row_a.get("interval_days_used", 730)
        source_t     = row_a.get("interval_source", "szacunkowy")
        priority_t   = row_a.get("priorytet_smart", "—")
        is_lotams_t  = bool(row_a.get("_is_lotams", False))

        with col_meta:
            lbl = "⭐ Historyczny klient LOTAMS" if is_lotams_t else "Nowy potencjalny klient"
            st.markdown(action_box(
                lbl,
                f"Operator: <b>{operator}</b> · Typ: <b>{typecode}</b><br>"
                f"Priorytet: <b>{priority_t}</b> · Confidence: <b>{confidence_t}</b><br>"
                f"Sugerowany kontakt: <b>{contact_str}</b><br>"
                f"Prognoza C-check: <b>{pred_str_t}</b> ({pred_q})",
                accent="#fbbf24" if is_lotams_t else "#3b82f6",
            ), unsafe_allow_html=True)

        template = f"""Temat: Oferta C-check — {selected_reg} ({operator})

Dzień dobry,

Piszę do Państwa z propozycją współpracy dotyczącej samolotu {selected_reg} ({typecode}) \
operowanego przez {operator}.

Na podstawie analizy danych telemetrycznych ADS-B (EUROCONTROL OPDI) szacujemy, że następny \
C-check tego samolotu przypada na {pred_q} ({pred_str_t}). Średni interwał między \
przeglądami C dla tego samolotu/operatora wynosi {interval_t:.0f} dni (źródło: {source_t}).

Ostatnia wykryta przerwa serwisowa: {last_str_t} · {gap_days} dni · {mro}.

LOTAMS Warsaw (EPWA) oferuje dla Państwa floty B737:
 - Specjalizację Boeing 737-600/700/800/900/MAX (EASA Part-145)
 - Dostępność slotów w hangarze Warszawa Okęcie
 - Certyfikowany czas C-check: konkurencyjny vs Hamburg, Monachium, Stambuł
 - Bezpośrednie połączenia lotnicze dla załóg technicznych

Czy mogę zaproponować termin rozmowy wstępnej w celu omówienia możliwości rezerwacji slotu?

Z poważaniem,
[Imię i nazwisko]
LOTAMS — Lot Aircraft Maintenance Services
[tel.] | [email] | lotams.com
Warszawa Okęcie, EPWA

---
*Prognoza oparta na danych EUROCONTROL OPDI (sygnał ADS-B). Nie zastępuje dokumentacji MRO.*"""

        st.code(template, language=None)

        col_dl1, col_dl2, _ = st.columns([2, 3, 5])
        with col_dl1:
            st.download_button(
                "📋 Pobierz szablon (.txt)",
                template.encode("utf-8"),
                f"kontakt_{selected_reg}.txt",
                "text/plain",
            )
        with col_dl2:
            subject = urllib.parse.quote(f"Oferta C-check — {selected_reg} ({operator})")
            body_short = urllib.parse.quote(template[:500])
            mailto_url = f"mailto:?subject={subject}&body={body_short}"
            st.markdown(
                f'<a href="{mailto_url}" target="_blank" style="'
                "display:inline-block;padding:8px 16px;background:#1e3a8a;color:#eff6ff;"
                "border-radius:6px;text-decoration:none;font-size:0.85rem;"
                'border:1px solid #3b82f6;font-weight:500;">'
                "📧 Otwórz w kliencie pocztowym</a>",
                unsafe_allow_html=True,
            )

# ── Tygodniowy digest ─────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)

col_dl_digest, col_summary = st.columns([2, 5])

with col_summary:
    st.markdown(section_header(
        "TYGODNIOWY DIGEST DLA ZESPOŁU SPRZEDAŻY",
        "Markdown do wklejenia na Slack / Teams / e-mail",
        accent="#3b82f6",
    ), unsafe_allow_html=True)

n_zaleg_d = len(alerts[alerts["priorytet_smart"] == "TERAZ (zaległe)"])
n_teraz_d = len(alerts[alerts["priorytet_smart"] == "TERAZ"])
n_szesc_d = len(alerts[alerts["priorytet_smart"] == "6 mies."])
n_lotams_d = int(alerts["_is_lotams"].sum())

digest_lines = [
    "# ✈️ MRO Weekly Intelligence Digest — LOTAMS",
    f"**Wygenerowano:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')} UTC",
    "",
    "## Stan alertów",
    f"| Priorytet | Samolotów |",
    f"|---|---|",
    f"| 🚨 TERAZ (zaległe) | {n_zaleg_d} |",
    f"| 🔴 TERAZ (0–6 mies.) | {n_teraz_d} |",
    f"| 🟡 6 mies. (6–12 mies.) | {n_szesc_d} |",
    f"| ⭐ Klienci LOTAMS | {n_lotams_d} |",
    "",
    "## Top 20 priorytetów",
    "",
]

for _, r in alerts.head(20).iterrows():
    star = "⭐ " if r.get("_is_lotams") else ""
    pq = "—"
    if pd.notna(r.get("predicted_next_smart")):
        dt = pd.Timestamp(r["predicted_next_smart"])
        pq = f"Q{(dt.month-1)//3+1} {dt.year}"
    digest_lines.append(
        f"- {star}**{r['registration']}** ({r.get('icao_operator', '?')}) "
        f"· {PRIORITY_EMOJI.get(r['priorytet_smart'], '⚪')} {r['priorytet_smart']} "
        f"· conf: {r.get('confidence', '?')} · prognoza: {pq}"
    )

digest_lines += ["", "---",
    "_Dane: EUROCONTROL OPDI · B737 EU · Klasyfikacja ADS-B = sygnał pośredni_"]
digest = "\n".join(digest_lines)

with col_dl_digest:
    st.download_button(
        "📥 Pobierz digest (Markdown)",
        digest.encode("utf-8"),
        "mro_weekly_digest.md",
        "text/markdown",
    )
