"""Per-aircraft historical interval prediction (krok 9 z roadmapy).

Zastępuje głupie `ostatni_c_check + 24 miesiące` z pipeline.build_dashboard
realnym interwałem per samolot lub per operator, obliczonym z historii
potwierdzonych C-checków (c_check_probability > 0.7).

Hierarchia fallbacków per samolot:
  1. per_aircraft  — >=2 potwierdzone C-checki tego samolotu, interwał >= 180d
  2. operator      — średnia interwałów per_aircraft u tego operatora
  3. global_mean   — średnia ze wszystkich per_aircraft (jeśli >= 20 samolotów)
  4. fallback      — FALLBACK_DAYS (24 miesiące)

Wejście:
    output/predictions.csv     — kandydaci z c_check_probability
    output/dashboard.csv       — 1 wiersz per samolot (bieżące prognoza_next)

Wyjście:
    output/predictions_with_interval.csv — dashboard + nowe kolumny smart

Uruchomienie:
    python predict.py
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

from pipeline import OUTPUT_DIR, _Tee

# ============================================================
# Konfiguracja
# ============================================================

PROB_THRESHOLD = 0.7      # próg potwierdzenia C-checka
MIN_INTERVAL_DAYS = 180   # < 6 mies. = dwa gapy z jednego przeglądu, odrzucamy
FALLBACK_DAYS = 730       # 24 miesiące — gdy brak jakiejkolwiek historii
NOW = pd.Timestamp("2026-05-22")
OVERDUE_GRACE_MONTHS = 3  # po ilu miesiącach spóźnienia stosujemy reforecast


# ============================================================
# Obliczanie interwałów
# ============================================================

def compute_per_aircraft_intervals(predictions, threshold=PROB_THRESHOLD):
    """Średni interwał między kolejnymi potwierdzonymi C-checkami per samolot.

    Filtrujemy interwały < MIN_INTERVAL_DAYS żeby nie wliczać podwójnych detekcji
    tego samego przeglądu (dwie kolejne LOW kandydatury blisko siebie).

    Returns: dict {icao24: mean_interval_days}
    """
    confirmed = (
        predictions[predictions['c_check_probability'] > threshold]
        .sort_values(['icao24', 'last_seen'])
        .copy()
    )
    per_aircraft = {}
    for icao24, group in confirmed.groupby('icao24'):
        if len(group) < 2:
            continue
        intervals = group['last_seen'].diff().dt.total_seconds().div(86400).dropna()
        intervals = intervals[intervals >= MIN_INTERVAL_DAYS]
        if not intervals.empty:
            per_aircraft[icao24] = float(intervals.mean())
    return per_aircraft


def compute_operator_intervals(predictions, per_aircraft, threshold=PROB_THRESHOLD):
    """Średni per_aircraft interwał per operator — fallback dla samolotów z 1 check'iem.

    Liczymy ze ZNANYCH per_aircraft interwałów u tego samego operatora,
    nie bezpośrednio z różnic dat (żeby nie dublować detekcji).

    Returns: dict {icao_operator: mean_interval_days}
    """
    if not per_aircraft:
        return {}
    confirmed = predictions[
        (predictions['c_check_probability'] > threshold) &
        predictions['icao_operator'].notna()
    ].copy()
    op_intervals = {}
    for op, group in confirmed.groupby('icao_operator'):
        ac_with_history = [
            per_aircraft[ac] for ac in group['icao24'].unique()
            if ac in per_aircraft
        ]
        if ac_with_history:
            op_intervals[op] = float(np.mean(ac_with_history))
    return op_intervals


# ============================================================
# Smart prediction
# ============================================================

def predict_smart(dashboard, predictions, threshold=PROB_THRESHOLD):
    """Wzbogaca dashboard o smart predykcję next C-checka.

    Dodaje kolumny:
        predicted_next_smart  — Timestamp
        mies_do_next_smart    — float (miesięcy do tej daty od NOW)
        priorytet_smart       — TERAZ / 6 mies. / 12 mies. / Daleko / Nieaktywny
        interval_days_used    — int (użyty interwał w dniach)
        interval_source       — per_aircraft | operator | global_mean | fallback
    """
    per_aircraft = compute_per_aircraft_intervals(predictions, threshold)
    op_intervals = compute_operator_intervals(predictions, per_aircraft, threshold)

    global_mean = float(np.mean(list(per_aircraft.values()))) if len(per_aircraft) >= 20 else None

    print(f"  per_aircraft interwałów:  {len(per_aircraft):4d} samolotów")
    print(f"  operator interwałów:      {len(op_intervals):4d} operatorów")
    if global_mean:
        print(f"  global_mean:              {global_mean:.0f} dni ({global_mean/30.44:.1f} mies.)")
    else:
        print(f"  global_mean: brak (< 20 samolotów), używamy fallback {FALLBACK_DAYS}d")
    print(f"  fallback:                 {FALLBACK_DAYS} dni ({FALLBACK_DAYS/30.44:.1f} mies.)")

    df = dashboard.copy()
    df['ostatni_c_check_dt'] = pd.to_datetime(df['ostatni_c_check'])

    intervals_out = []
    sources_out = []

    for _, row in df.iterrows():
        icao24 = row['icao24']
        op = row.get('icao_operator')

        if icao24 in per_aircraft:
            intervals_out.append(per_aircraft[icao24])
            sources_out.append('per_aircraft')
        elif pd.notna(op) and op in op_intervals:
            intervals_out.append(op_intervals[op])
            sources_out.append('operator')
        elif global_mean is not None:
            intervals_out.append(global_mean)
            sources_out.append('global_mean')
        else:
            intervals_out.append(float(FALLBACK_DAYS))
            sources_out.append('fallback')

    df['interval_days_used'] = np.round(intervals_out).astype(int)
    df['interval_source'] = sources_out

    raw_next = df['ostatni_c_check_dt'] + pd.to_timedelta(df['interval_days_used'], unit='D')

    # Reforecast: aktywny samolot z predykcją dawno w przeszłości = C-check przegapiony
    # Ustawiamy jako "zbliżający się" od połowy interwału temu
    overdue_cutoff = NOW - pd.Timedelta(days=OVERDUE_GRACE_MONTHS * 30)
    needs_reforecast = df['is_active'] & (raw_next < overdue_cutoff)
    raw_next[needs_reforecast] = NOW + pd.to_timedelta(
        (df.loc[needs_reforecast, 'interval_days_used'] * 0.5).round().astype(int), unit='D'
    )
    df['reforecasted_smart'] = needs_reforecast

    df['predicted_next_smart'] = raw_next

    df['mies_do_next_smart'] = (
        (df['predicted_next_smart'] - NOW).dt.total_seconds() / (86400 * 30.44)
    ).round(1)

    def _priorytet(row):
        if not row['is_active']:
            return 'Nieaktywny'
        m = row['mies_do_next_smart']
        if pd.isna(m):
            return 'Daleko'
        if m <= 0:
            return 'TERAZ (zaległe)'  # C-check termin minął — dzwoń natychmiast
        if m <= 6:
            return 'TERAZ'            # C-check za 0–6 mies. — ostatnie okno decyzyjne
        if m <= 12:
            return '6 mies.'          # C-check za 6–12 mies. — rozpocznij rozmowy
        if m <= 18:
            return '12 mies.'         # C-check za 12–18 mies. — obserwuj
        return 'Daleko'               # > 18 mies. — poza oknem decyzyjnym

    df['priorytet_smart'] = df.apply(_priorytet, axis=1)
    df = df.drop(columns=['ostatni_c_check_dt'])
    return df, per_aircraft, op_intervals


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    log_path = OUTPUT_DIR / 'predict_log.txt'
    log_file = open(log_path, 'w', encoding='utf-8')
    sys.stdout = _Tee(sys.__stdout__, log_file)

    print("=== Krok 9 - Per-aircraft historical interval ===")
    print(f"Threshold potwierdzenia C-checka: prob > {PROB_THRESHOLD}")
    print(f"Minimalna długość interwału:       {MIN_INTERVAL_DAYS}d")
    print(f"Fallback:                          {FALLBACK_DAYS}d ({FALLBACK_DAYS/30.44:.1f} mies.)")
    print(f"NOW:                               {NOW.date()}")

    predictions = pd.read_csv(
        OUTPUT_DIR / 'predictions.csv',
        parse_dates=['last_seen', 'next_first_seen'],
    )
    dashboard = pd.read_csv(OUTPUT_DIR / 'dashboard.csv')

    print(f"\nWczytano predictions.csv: {len(predictions):,} kandydatów")
    print(f"Wczytano dashboard.csv:   {len(dashboard):,} samolotów")
    prob_confirmed = (predictions['c_check_probability'] > PROB_THRESHOLD).sum()
    print(f"Potwierdzonych C-checków (prob > {PROB_THRESHOLD}): {prob_confirmed:,}")

    print(f"\n=== Obliczanie interwałów ===")
    result, per_ac, op_int = predict_smart(dashboard, predictions, PROB_THRESHOLD)

    # ---- Statystyki interwałów per źródło ----
    print(f"\n=== Źródła interwałów ===")
    src_counts = result['interval_source'].value_counts()
    for src, cnt in src_counts.items():
        pct = cnt / len(result) * 100
        print(f"  {src:12s}: {cnt:5d} samolotów ({pct:.1f}%)")

    print(f"\n=== Interwały per źródło (dni) ===")
    src_stats = (
        result.groupby('interval_source')['interval_days_used']
        .agg(['count', 'mean', 'std', 'min', 'max'])
        .round(0).astype(int)
    )
    print(src_stats.to_string())

    # ---- Porównanie priorytetów ----
    print(f"\n=== Porównanie: priorytet oryginalny vs smart ===")
    order = ['TERAZ (zaległe)', 'TERAZ', '6 mies.', '12 mies.', 'Daleko', 'Nieaktywny']
    comp = pd.crosstab(
        pd.Categorical(result['priorytet'], categories=order, ordered=True),
        pd.Categorical(result['priorytet_smart'], categories=order, ordered=True),
        margins=True,
    )
    print(comp.to_string())

    # ---- Top kandydaci do kontaktu (smart priority) ----
    print(f"\n=== Top 20 samolotów do kontaktu [TERAZ/6mies., HIGH/MEDIUM, smart] ===")
    top = result[
        result['priorytet_smart'].isin(['TERAZ (zaległe)', 'TERAZ', '6 mies.']) &
        result['confidence'].isin(['HIGH', 'MEDIUM']) &
        result['is_active']
    ].sort_values('mies_do_next_smart').head(20)
    display_cols = [
        'registration', 'icao_operator', 'confidence',
        'ostatni_c_check', 'interval_days_used', 'interval_source',
        'predicted_next_smart', 'mies_do_next_smart', 'priorytet_smart',
    ]
    top_display = top[display_cols].copy()
    top_display['predicted_next_smart'] = top_display['predicted_next_smart'].dt.strftime('%Y-%m-%d')
    print(top_display.round(1).to_string(index=False))

    # ---- Per-operator summary ----
    print(f"\n=== Per-operator: ile samolotów w oknie TERAZ/6mies. (smart) ===")
    active_priority = result[
        result['priorytet_smart'].isin(['TERAZ (zaległe)', 'TERAZ', '6 mies.']) &
        result['is_active'] &
        result['icao_operator'].notna()
    ]
    op_summary = (
        active_priority.groupby('icao_operator')
        .agg(
            samoloty=('registration', 'count'),
            confidence_high=('confidence', lambda x: (x == 'HIGH').sum()),
            avg_interval=('interval_days_used', 'mean'),
            interval_source=('interval_source', lambda x: x.mode()[0] if not x.empty else 'fallback'),
        )
        .sort_values('samoloty', ascending=False)
        .head(20)
    )
    op_summary['avg_interval'] = op_summary['avg_interval'].round(0).astype(int)
    print(op_summary.to_string())

    # ---- Zapis ----
    out_path = OUTPUT_DIR / 'predictions_with_interval.csv'
    result.to_csv(out_path, index=False, encoding='utf-8')

    print(f"\n=== Zapisano ===")
    print(f"  {log_path}")
    print(f"  {out_path}  ({len(result)} samolotów × {result.shape[1]} kolumn)")
    print(f"\n  Nowe kolumny dodane do dashboard:")
    new_cols = ['interval_days_used', 'interval_source', 'predicted_next_smart',
                'mies_do_next_smart', 'priorytet_smart', 'reforecasted_smart']
    for c in new_cols:
        print(f"    {c}")

    sys.stdout = sys.__stdout__
    log_file.close()
