"""Warstwa danych dla Streamlit — czyta z output/ CSV zamiast data/processed/ parquet."""

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

# Prefiksy rejestracji → kraj (ICAO registration prefix standard)
_REG_PREFIX_TO_COUNTRY = {
    "SP": "🇵🇱 Polska",
    "EI": "🇮🇪 Irlandia",
    "G":  "🇬🇧 Wielka Brytania",
    "TC": "🇹🇷 Turcja",
    "OE": "🇦🇹 Austria",
    "D":  "🇩🇪 Niemcy",
    "F":  "🇫🇷 Francja",
    "I":  "🇮🇹 Włochy",
    "EC": "🇪🇸 Hiszpania",
    "CS": "🇵🇹 Portugalia",
    "OH": "🇫🇮 Finlandia",
    "OY": "🇩🇰 Dania",
    "SE": "🇸🇪 Szwecja",
    "LN": "🇳🇴 Norwegia",
    "OK": "🇨🇿 Czechy",
    "OM": "🇸🇰 Słowacja",
    "HA": "🇭🇺 Węgry",
    "YR": "🇷🇴 Rumunia",
    "LZ": "🇧🇬 Bułgaria",
    "SX": "🇬🇷 Grecja",
    "YU": "🇷🇸 Serbia",
    "9A": "🇭🇷 Chorwacja",
    "OO": "🇧🇪 Belgia",
    "PH": "🇳🇱 Holandia",
    "LX": "🇱🇺 Luksemburg",
    "EW": "🇧🇾 Białoruś",
    "UR": "🇺🇦 Ukraina",
    "TF": "🇮🇸 Islandia",
    "SU": "🇪🇬 Egipt",
    "CN": "🇲🇦 Maroko",
}


def extract_registration_country(reg: str) -> str:
    """Zwraca kraj rejestracji na podstawie prefiksu (SP-LVB → 🇵🇱 Polska)."""
    if not isinstance(reg, str):
        return "Nieznany"
    prefix = reg.split("-")[0] if "-" in reg else reg[:2]
    # Sprawdź najpierw dłuższe (2-znakowe) prefiksy żeby G- nie kolidowało z GA-
    for p in sorted(_REG_PREFIX_TO_COUNTRY.keys(), key=len, reverse=True):
        if prefix.upper() == p or reg.upper().startswith(p + "-"):
            return _REG_PREFIX_TO_COUNTRY[p]
    return "Inne"


@st.cache_data(ttl=300)
def load_dashboard() -> pd.DataFrame:
    """1 wiersz per samolot — z predictions_with_interval.csv + c_check_probability z predictions.csv."""
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

    # Unifikacja kolumn
    if "priorytet_smart" not in df.columns and "priorytet" in df.columns:
        df["priorytet_smart"] = df["priorytet"]
    if "mies_do_next_smart" not in df.columns and "mies_do_next" in df.columns:
        df["mies_do_next_smart"] = df["mies_do_next"]

    # Dołącz c_check_probability z predictions.csv (max per samolot)
    pred_path = OUTPUT_DIR / "predictions.csv"
    if pred_path.exists() and "c_check_probability" not in df.columns:
        pred = pd.read_csv(pred_path, usecols=["icao24", "c_check_probability"])
        best_prob = (
            pred.groupby("icao24")["c_check_probability"]
            .max()
            .reset_index()
        )
        df = df.merge(best_prob, on="icao24", how="left")

    # Kraj rejestracji z prefiksu
    if "registration" in df.columns:
        df["registration_country"] = df["registration"].map(extract_registration_country)

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
    return f"{PRIORITY_EMOJI.get(p, '⚪')} {p}"


def format_confidence(c: str) -> str:
    return f"{CONFIDENCE_EMOJI.get(c, '⚪')} {c}"


def months_label(months: float | None) -> str:
    if months is None or pd.isna(months):
        return "—"
    if months < 0:
        return f"zaległe ({months:.1f}m)"
    if months < 1:
        return "< 1 mies."
    return f"{months:.1f} mies."


# ── Wiek i generacja samolotu (szacunek z typecode) ───────────────────────────

_TYPECODE_GENERATION = {
    "B37M": ("737 MAX 7",  2019),
    "B38M": ("737 MAX 8",  2018),
    "B39M": ("737 MAX 9",  2018),
    "B3XM": ("737 MAX 10", 2023),
    "B736": ("737-600 NG", 2004),
    "B737": ("737-700 NG", 2007),
    "B738": ("737-800 NG", 2010),
    "B739": ("737-900 NG", 2012),
    "B73H": ("737-800 NG", 2010),
    "B73M": ("737-700 NG", 2007),
    "B73C": ("737-800 NG", 2010),
    "B73W": ("737-800 NG", 2010),
    "B733": ("737-300 CL", 1992),
    "B734": ("737-400 CL", 1993),
    "B735": ("737-500 CL", 1994),
}
_NOW_YEAR = 2026


def enrich_with_generation(df: pd.DataFrame) -> pd.DataFrame:
    """Dodaje kolumny 'generacja' i 'wiek_est' na podstawie typecode."""
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
