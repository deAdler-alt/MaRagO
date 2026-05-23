"""Warstwa danych dla Streamlit — czyta z output/ CSV zamiast data/processed/ parquet.

Wszystkie funkcje mają @st.cache_data żeby nie przeładowywać przy każdym widgecie.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"

PRIORITY_ORDER = ["TERAZ (zaległe)", "TERAZ", "6 mies.", "12 mies.", "Daleko", "Nieaktywny"]
PRIORITY_EMOJI = {
    "TERAZ (zaległe)": "🔴",
    "TERAZ": "🔴",
    "6 mies.": "🟡",
    "12 mies.": "🟢",
    "Daleko": "⚪",
    "Nieaktywny": "⬛",
}
CONFIDENCE_EMOJI = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}
PRIORITY_BG = {
    "TERAZ (zaległe)": "#fef2f2",
    "TERAZ": "#fef2f2",
    "6 mies.": "#fefce8",
    "12 mies.": "#f0fdf4",
    "Daleko": "#f8fafc",
    "Nieaktywny": "#f1f5f9",
}


@st.cache_data(ttl=300)
def load_dashboard() -> pd.DataFrame:
    """1 wiersz per samolot — z predictions_with_interval.csv jeśli dostępny, else dashboard.csv."""
    smart_path = OUTPUT_DIR / "predictions_with_interval.csv"
    fallback_path = OUTPUT_DIR / "dashboard.csv"

    if smart_path.exists():
        df = pd.read_csv(smart_path, parse_dates=["ostatni_c_check", "predicted_next_smart"])
    elif fallback_path.exists():
        df = pd.read_csv(fallback_path, parse_dates=["ostatni_c_check"])
        df["predicted_next_smart"] = pd.to_datetime(df["prognoza_next"], errors="coerce")
        df["priorytet_smart"] = df.get("priorytet", "Daleko")
        df["mies_do_next_smart"] = df.get("mies_do_next", None)
        df["interval_days_used"] = 730
        df["interval_source"] = "fallback"
    else:
        return pd.DataFrame()

    # Unifikacja kolumn dla bezpieczeństwa
    if "priorytet_smart" not in df.columns and "priorytet" in df.columns:
        df["priorytet_smart"] = df["priorytet"]
    if "mies_do_next_smart" not in df.columns and "mies_do_next" in df.columns:
        df["mies_do_next_smart"] = df["mies_do_next"]

    return df


@st.cache_data(ttl=300)
def load_candidates() -> pd.DataFrame:
    """Wszystkie kandydaci na C-check (3651 wierszy) z c_check_probability."""
    path = OUTPUT_DIR / "predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["last_seen", "next_first_seen"])


@st.cache_data(ttl=300)
def load_lotams_clients() -> pd.DataFrame:
    path = OUTPUT_DIR / "lotams_clients.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def priority_sort_key(priority_series: pd.Series) -> pd.Series:
    order = {v: i for i, v in enumerate(PRIORITY_ORDER)}
    return priority_series.map(order).fillna(99)


def format_priority(p: str) -> str:
    emoji = PRIORITY_EMOJI.get(p, "⚪")
    return f"{emoji} {p}"


def format_confidence(c: str) -> str:
    emoji = CONFIDENCE_EMOJI.get(c, "⚪")
    return f"{emoji} {c}"


def months_label(months: float | None) -> str:
    if months is None or pd.isna(months):
        return "—"
    if months < 0:
        return f"zaległe ({months:.1f}m)"
    if months < 1:
        return "< 1 mies."
    return f"{months:.1f} mies."


# Szacowany rok pierwszego lotu per wariant B737
# Źródło: Boeing delivery statistics (typ → zakres produkcji → mediana)
_TYPECODE_GENERATION = {
    # 737 MAX
    "B37M": ("737 MAX 7",  2019),
    "B38M": ("737 MAX 8",  2018),
    "B39M": ("737 MAX 9",  2018),
    "B3XM": ("737 MAX 10", 2023),
    # 737 NG
    "B736": ("737-600 NG", 2004),
    "B737": ("737-700 NG", 2007),
    "B738": ("737-800 NG", 2010),
    "B739": ("737-900 NG", 2012),
    "B73H": ("737-800 NG", 2010),
    "B73M": ("737-700 NG", 2007),
    "B73C": ("737-800 NG", 2010),
    "B73W": ("737-800 NG", 2010),
    # 737 Classic
    "B733": ("737-300 CL", 1992),
    "B734": ("737-400 CL", 1993),
    "B735": ("737-500 CL", 1994),
}
_NOW_YEAR = 2026


def enrich_with_generation(df: pd.DataFrame) -> pd.DataFrame:
    """Dodaje kolumny 'generacja' i 'wiek_est' do DataFrame z kolumną typecode."""
    if "typecode" not in df.columns:
        return df
    df = df.copy()
    df["generacja"] = df["typecode"].map(
        lambda t: _TYPECODE_GENERATION.get(str(t).upper(), (str(t), None))[0]
    )
    df["wiek_est"] = df["typecode"].map(
        lambda t: (
            f"~{_NOW_YEAR - _TYPECODE_GENERATION[str(t).upper()][1]} lat"
            if str(t).upper() in _TYPECODE_GENERATION
            else "—"
        )
    )
    return df
