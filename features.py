import pandas as pd
import numpy as np
import re
import sys

from pipeline import (
    load_b737_eu, detect_gaps, classify_check,
    MRO_HUBS, STRICT_MRO_HUBS, EUROPE_AIRPORT_PREFIXES, OUTPUT_DIR,
    _Tee,
)


# === Mapowania prefiksów ===

# Prefiks rejestracji → kraj (kod ISO 3166-1 alfa-2)
REGISTRATION_TO_COUNTRY = {
    # Europa
    'SP': 'PL', 'D': 'DE', 'G': 'UK', 'F': 'FR', 'EI': 'IE',
    'LN': 'NO', 'LZ': 'BG', 'LY': 'LT', 'SE': 'SE', 'PH': 'NL',
    'OY': 'DK', 'OE': 'AT', 'OH': 'FI', 'OK': 'CZ', 'OM': 'SK',
    'OO': 'BE', 'I': 'IT', 'EC': 'ES', 'CS': 'PT', 'HA': 'HU',
    'YL': 'LV', 'S5': 'SI', 'SX': 'GR', 'LX': 'LU', 'HB': 'CH',
    'YR': 'RO', 'YU': 'RS', 'UR': 'UA',
    '9A': 'HR', '9H': 'MT',
    # Bliski Wschód
    'TC': 'TR', 'A4O': 'OM', 'A6': 'AE', 'A7': 'QA',
    '4X': 'IL', 'HZ': 'SA', 'JY': 'JO',
    # Afryka
    '7T': 'DZ', 'SU': 'EG', 'ET': 'ET',
    '5A': 'LY', 'CN': 'MA', 'TS': 'TN',
    # Inne
    'N': 'US', 'RA': 'RU', 'UP': 'KZ',
}

# Pierwsze 2 znaki kodu ICAO lotniska → kraj
# Pokrywa cały EUROPE_AIRPORT_PREFIXES + kilka spoza zakresu (gdyby się przemknęły)
ICAO_PREFIX_TO_COUNTRY = {
    # Europa Środkowa
    'EP': 'PL', 'ED': 'DE', 'LK': 'CZ', 'LZ': 'SK', 'LO': 'AT', 'LH': 'HU',
    # Europa Zachodnia
    'EG': 'UK', 'EI': 'IE', 'EH': 'NL', 'EB': 'BE', 'EL': 'LU',
    'LF': 'FR', 'LS': 'CH',
    # Europa Północna / Skandynawia / Bałtyki
    'EK': 'DK', 'EN': 'NO', 'ES': 'SE', 'EF': 'FI', 'EE': 'EE',
    'EV': 'LV', 'EY': 'LT', 'BI': 'IS',
    # Europa Południowa
    'LE': 'ES', 'LP': 'PT', 'LI': 'IT', 'LG': 'GR', 'LM': 'MT',
    'LB': 'BG', 'LR': 'RO', 'LJ': 'SI', 'LD': 'HR', 'LC': 'CY',
    # Bałkany
    'LA': 'AL', 'LQ': 'BA', 'LW': 'MK', 'LY': 'RS', 'BK': 'XK',
    'LU': 'MD',
    # Turcja + Ukraina
    'LT': 'TR', 'UK': 'UA',
    # Afryka Północna (w zakresie briefu)
    'DA': 'DZ', 'DT': 'TN', 'GM': 'MA', 'HE': 'EG', 'HL': 'LY',
    # Poza zakresem briefu, ale na wszelki wypadek (do flagowania "out of EU")
    'LL': 'IL', 'OE': 'SA', 'OM': 'AE', 'OT': 'QA', 'OO': 'OM',
    'HA': 'ET', 'UU': 'RU', 'UA': 'KZ',
}


# === Helper functions ===

def extract_registration_prefix(reg):
    """Wyciągnij prefiks państwowy z rejestracji.
    
    'SP-LWF' -> 'SP', 'D-ATUN' -> 'D', 'N737GG' -> 'N',
    '9A-XYZ' -> '9A', '0110' -> None (rejestracja wojskowa).
    """
    if pd.isna(reg) or not isinstance(reg, str):
        return None
    if '-' in reg:
        return reg.split('-')[0]
    # Bez myślnika - np. US 'N737GG': prefiks to litery na początku
    m = re.match(r'^([A-Za-z]+)', reg)
    return m.group(1) if m else None


def registration_country(reg):
    """Kraj operatora z prefiksu rejestracji (sprawdza od najdłuższego prefiksu)."""
    prefix = extract_registration_prefix(reg)
    if prefix is None:
        return None
    for length in [3, 2, 1]:
        sub = prefix[:length]
        if sub in REGISTRATION_TO_COUNTRY:
            return REGISTRATION_TO_COUNTRY[sub]
    return None


def airport_country(icao_code):
    """Kraj lotniska z 2-literowego prefiksu kodu ICAO."""
    if pd.isna(icao_code) or not isinstance(icao_code, str) or len(icao_code) < 2:
        return None
    return ICAO_PREFIX_TO_COUNTRY.get(icao_code[:2])


# === Feature groups ===

def add_gap_features(candidates):
    """Cechy kalendarzowe i lokalizacja gapa."""
    print("  Liczę gap features...")
    out = candidates.copy()
    out['gap_start_month'] = out['last_seen'].dt.month
    out['gap_start_dow'] = out['last_seen'].dt.dayofweek
    out['gap_start_year'] = out['last_seen'].dt.year
    out['at_strict_mro_hub'] = out['ades'].isin(STRICT_MRO_HUBS)
    out['at_any_mro_hub'] = out['ades'].isin(MRO_HUBS.keys())
    out['ades_country'] = out['ades'].apply(airport_country)
    return out


def add_aircraft_features(candidates):
    """Cechy samolotu - kraj rejestracji, dopasowanie do destynacji."""
    print("  Liczę aircraft features...")
    out = candidates.copy()
    out['registration_prefix'] = out['registration'].apply(extract_registration_prefix)
    out['registration_country'] = out['registration'].apply(registration_country)
    out['destination_country_matches_registration'] = (
        out['ades_country'] == out['registration_country']
    )
    return out


def _build_aircraft_dict(df):
    """Zbuduj raz słownik {icao24: DataFrame z lotami}. Wielokrotnie wykorzystywany."""
    return {ac: g for ac, g in df.groupby('icao24', sort=False)}


def add_pre_gap_features(candidates, aircraft_dict, window_days=60):
    """Aktywność samolotu w `window_days` dni przed gapem."""
    print(f"  Liczę pre-gap features (okno {window_days}d)...")
    n = len(candidates)
    fpd = np.full(n, np.nan)
    dist = np.full(n, np.nan)
    dur = np.full(n, np.nan)
    
    candidates_reset = candidates.reset_index(drop=True)
    
    for i, row in candidates_reset.iterrows():
        ac_df = aircraft_dict.get(row['icao24'])
        if ac_df is None or len(ac_df) == 0:
            continue
        gap_start = row['last_seen']
        window_start = gap_start - pd.Timedelta(days=window_days)
        ac_last = ac_df['last_seen'].values
        mask = (ac_last >= np.datetime64(window_start)) & (ac_last <= np.datetime64(gap_start))
        pre_count = int(mask.sum())
        if pre_count == 0:
            fpd[i] = 0
            dist[i] = 0
            continue
        fpd[i] = pre_count / window_days
        dist[i] = len(set(ac_df['ades'].values[mask]))
        # Czas trwania lotu (w godzinach)
        ac_first = ac_df['first_seen'].values
        durations_sec = (ac_last[mask] - ac_first[mask]).astype('timedelta64[s]').astype(np.float64)
        dur[i] = (durations_sec / 3600).mean()
    
    out = candidates_reset.copy()
    out['flights_per_day_pre_gap'] = fpd
    out['distinct_airports_pre_gap'] = dist
    out['avg_flight_duration_pre_gap_hours'] = dur
    return out


def add_post_gap_features(candidates, aircraft_dict, window_days=30):
    """Zachowanie samolotu w `window_days` dni po gapie."""
    print(f"  Liczę post-gap features (okno {window_days}d)...")
    n = len(candidates)
    # Float NaN zamiast object - LightGBM przyjmuje float (NaN OK), nie przyjmuje object
    same_op = np.full(n, np.nan, dtype=np.float64)
    same_country = np.full(n, np.nan, dtype=np.float64)
    
    candidates_reset = candidates.reset_index(drop=True)
    
    for i, row in candidates_reset.iterrows():
        ac_df = aircraft_dict.get(row['icao24'])
        if ac_df is None or len(ac_df) == 0:
            continue
        gap_end = row['next_first_seen']
        if pd.isna(gap_end):
            continue
        window_end = gap_end + pd.Timedelta(days=window_days)
        # Pierwsze loty od gap_end - sortujemy po first_seen na wszelki wypadek
        ac_first = ac_df['first_seen'].values
        mask = (ac_first >= np.datetime64(gap_end)) & (ac_first <= np.datetime64(window_end))
        if not mask.any():
            continue
        post = ac_df.loc[mask].sort_values('first_seen')
        first_post = post.iloc[0]
        # same_operator_after - 1.0 jeśli ten sam, 0.0 jeśli inny, NaN jeśli brak danych
        pre_op = row.get('icao_operator')
        post_op = first_post.get('icao_operator')
        if pd.notna(post_op) and pd.notna(pre_op):
            same_op[i] = 1.0 if post_op == pre_op else 0.0
        # same_country_after (porównanie do kraju rejestracji samolotu)
        reg_country = registration_country(row.get('registration'))
        post_adep_country = airport_country(first_post.get('adep'))
        if reg_country and post_adep_country:
            same_country[i] = 1.0 if post_adep_country == reg_country else 0.0
    
    out = candidates_reset.copy()
    out['same_operator_after'] = same_op
    out['same_country_after'] = same_country
    return out


def add_operator_features(candidates, df):
    """Cechy operatora: fleet size, typowy MRO, czy gap w typowym MRO."""
    print("  Liczę operator features...")
    out = candidates.copy()
    
    # Fleet size: ilu samolotów operator obsługuje w naszych danych
    fleet = df.groupby('icao_operator')['icao24'].nunique()
    out['operator_fleet_size'] = out['icao_operator'].map(fleet)
    
    # Typowy MRO operatora = mode(ades) wśród WSZYSTKICH jego C-check kandydatów
    # (włącznie z LOW - bo ML i tak nie wie który był prawdziwym C-check'iem)
    def _mode_safe(s):
        m = s.mode()
        return m.iloc[0] if not m.empty else None
    op_typical = candidates.groupby('icao_operator')['ades'].agg(_mode_safe)
    out['operator_typical_mro'] = out['icao_operator'].map(op_typical)
    out['gap_at_operator_typical_mro'] = (out['ades'] == out['operator_typical_mro'])
    
    return out


def add_historical_features(candidates):
    """Poprzednie C-checki tego samolotu (sortowanie po dacie)."""
    print("  Liczę historical features...")
    out = candidates.sort_values(['icao24', 'last_seen']).copy()
    
    # Numer porządkowy gapa w historii samolotu (0 = pierwszy w danych)
    out['c_check_seq'] = out.groupby('icao24').cumcount()
    out['num_previous_c_checks'] = out['c_check_seq']
    
    # Interwał (dni) między tym gapem a poprzednim gapem tego samolotu
    out['prev_gap_last_seen'] = out.groupby('icao24')['last_seen'].shift(1)
    out['interval_to_previous_days'] = (
        (out['last_seen'] - out['prev_gap_last_seen']).dt.total_seconds() / 86400
    )
    
    # Średni interwał ze wszystkich PRZED tym gapem (expanding window, shifted)
    out['mean_interval_prev_c_checks'] = (
        out.groupby('icao24')['interval_to_previous_days']
        .transform(lambda x: x.expanding().mean().shift(1))
    )
    
    out = out.drop(columns=['prev_gap_last_seen'])
    return out


# === Top-level ===

def get_c_check_candidates(df):
    """Wyciągnij kandydatów na C-check + dorzuć pseudo-label confidence z reguł.
    
    Wymóg geograficzny: gap musi się zdarzyć w EUROPE_AIRPORT_PREFIXES
    (Europa Zach./Środk. + Skandynawia + Bałkany + Turcja + Afryka Płn. + Ukraina).
    """
    candidates = df[
        (df['check_type'] == 'C-check') &
        (df['gap_days'] > 0) &
        (df['ades'].str[:2].isin(EUROPE_AIRPORT_PREFIXES))
    ].copy()
    
    candidates['at_strict_mro'] = candidates['ades'].isin(STRICT_MRO_HUBS)
    candidates['at_any_mro'] = candidates['ades'].isin(MRO_HUBS.keys())
    candidates['mro_facility'] = candidates['ades'].map(MRO_HUBS).fillna(
        candidates['ades'].fillna('Unknown')
    )
    
    def _conf(r):
        if r['at_strict_mro']:
            return 'HIGH'
        if r['at_any_mro'] and r['stayed_put']:
            return 'MEDIUM'
        return 'LOW'
    candidates['confidence'] = candidates.apply(_conf, axis=1)
    
    return candidates


def build_features(df, candidates):
    """Pełen pipeline feature engineering. Zwraca enriched candidates DataFrame."""
    print(f"\n=== Feature engineering ===")
    print(f"Kandydatów na C-check: {len(candidates):,}")
    
    aircraft_dict = _build_aircraft_dict(df)
    print(f"Słownik samolotów: {len(aircraft_dict):,} icao24")
    
    c = candidates.copy()
    c = add_gap_features(c)
    c = add_aircraft_features(c)
    c = add_pre_gap_features(c, aircraft_dict, window_days=60)
    c = add_post_gap_features(c, aircraft_dict, window_days=30)
    c = add_operator_features(c, df)
    c = add_historical_features(c)
    
    return c


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    log_path = OUTPUT_DIR / 'features_log.txt'
    log_file = open(log_path, 'w', encoding='utf-8')
    sys.stdout = _Tee(sys.__stdout__, log_file)
    
    df = load_b737_eu()
    print("\n=== Detekcja gapów ===")
    df = detect_gaps(df)
    df['check_type'] = df.apply(classify_check, axis=1)
    
    candidates = get_c_check_candidates(df)
    print(f"\nRozkład confidence (pseudo-label):")
    print(candidates['confidence'].value_counts())
    
    features = build_features(df, candidates)
    
    print(f"\n=== Wymiary features ===")
    print(f"Wierszy: {len(features):,}")
    print(f"Kolumn:  {features.shape[1]}")
    
    print(f"\n=== Coverage (% non-null) per nowa kolumna ===")
    new_cols = [
        'gap_start_month', 'gap_start_dow', 'ades_country',
        'registration_country', 'destination_country_matches_registration',
        'flights_per_day_pre_gap', 'distinct_airports_pre_gap',
        'avg_flight_duration_pre_gap_hours',
        'same_operator_after', 'same_country_after',
        'operator_fleet_size', 'operator_typical_mro', 'gap_at_operator_typical_mro',
        'num_previous_c_checks', 'interval_to_previous_days',
        'mean_interval_prev_c_checks',
    ]
    for col in new_cols:
        if col in features.columns:
            non_null = features[col].notna().sum()
            pct = non_null / len(features) * 100
            print(f"  {col:48s}: {non_null:5d} ({pct:5.1f}%)")
    
    print(f"\n=== Statystyki numerical features ===")
    num_cols = ['gap_days', 'flights_per_day_pre_gap', 'distinct_airports_pre_gap',
                'avg_flight_duration_pre_gap_hours', 'operator_fleet_size',
                'num_previous_c_checks', 'mean_interval_prev_c_checks']
    print(features[num_cols].describe().round(2).to_string())
    
    print(f"\n=== Sanity check: features vs confidence (mean per group) ===")
    sanity_cols = ['gap_days', 'flights_per_day_pre_gap', 'distinct_airports_pre_gap',
                   'destination_country_matches_registration',
                   'gap_at_operator_typical_mro', 'same_operator_after',
                   'operator_fleet_size']
    means_by_conf = features.groupby('confidence')[sanity_cols].mean().round(2)
    print(means_by_conf.to_string())
    print("  ↑ HIGH/MEDIUM powinny mieć wyższe gap_at_operator_typical_mro,")
    print("     same_operator_after i destination_country_matches_registration niż LOW")
    
    # Zapis
    features_path = OUTPUT_DIR / 'features.csv'
    features.to_csv(features_path, index=False, encoding='utf-8')
    
    print(f"\n=== Zapisano ===")
    print(f"  {log_path}")
    print(f"  {features_path}  ({len(features):,} kandydatów × {features.shape[1]} kolumn)")
    
    sys.stdout = sys.__stdout__
    log_file.close()
