import pandas as pd
import glob
import sys
from pathlib import Path

OUTPUT_DIR = Path('output')


class _Tee:
    """Duplikuje stdout do pliku + terminala. Każdy print idzie do obu strumieni."""
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()
    def flush(self):
        for s in self.streams:
            s.flush()

# Wszystkie warianty 737
B737_TYPES = ['B736', 'B737', 'B738', 'B739', 'B37M', 'B38M', 'B39M', 'B3XM']

# Europejskie ICAO prefiksy
EU_PREFIXES = ('E', 'L', 'B')

# Lotniska MRO ważne dla LOTAMS i konkurencji
MRO_HUBS = {
    # Dedykowane bazy MRO (też w STRICT poniżej)
    'EPWA': 'Warszawa - LOTAMS',
    'LBSF': 'Sofia - Lufthansa Technik Sofia',
    'LKMT': 'Ostrava - Job Air Technic',
    'LROP': 'Bukareszt - Romaero',
    'LZIB': 'Bratysława',
    'LPPT': 'Lizbona - TAP M&E',
    'LIRA': 'Rzym Ciampino - ATITECH',
    'EGPK': 'Prestwick - Ryanair Maintenance',
    'EDLP': 'Paderborn - ATS Maintenance',
    'EGSH': 'Norwich - KLM UK Engineering',
    'EGDX': 'St Athan - eCube Solutions / Boeing UK',
    # Operacyjne huby z MRO (HIGH tylko gdy stayed_put)
    'EDDH': 'Hamburg - Lufthansa Technik',
    'EDDM': 'München - Lufthansa Technik',
    'EIDW': 'Dublin - SR Technics',
    'LTBA': 'Istanbul ATA - Turkish Technic',
    'LTFM': 'Istanbul IST - Turkish Technic',
    'LTFJ': 'Istanbul SAW - Turkish Technic SAW',
    'LFLL': 'Lyon - AFI KLM E&M',
    'EHAM': 'Amsterdam - KLM E&M',
    'LSGG': 'Genewa - SR Technics',
    'LGAV': 'Ateny - Olympic Engineering',
    'LKPR': 'Praga - CSA Technics / Smartwings',
    'EDDN': 'Norymberga - LH CityLine Maintenance',
    'EINN': 'Shannon - Lufthansa Technik Shannon',
    'LHBP': 'Budapeszt - Lufthansa Technik Budapest',
    'LFSB': 'Bazylea - AMAC Aerospace',
}

# Strict subset - tu prawie na pewno C-check, nie zwykły parking
# (lotniska które NIE są dużymi hubami operacyjnymi B737 - mała szansa na fałszywy pozytyw)
# EGPK = Ryanair MRO (mało ruchu liniowego B737 poza Ryanairem)
# EDLP = ATS, mały regional, dedykowane MRO
# EGSH = KLM UK Engineering w Norwich, prawie zero ruchu liniowego B737
# EGDX = St Athan, dedykowane MRO (eCube/Boeing UK), brak ruchu liniowego
STRICT_MRO_HUBS = {'EPWA', 'LBSF', 'LKMT', 'LROP', 'LZIB', 'LIRA', 'LPPT',
                   'EGPK', 'EDLP', 'EGSH', 'EGDX'}


def load_b737_eu(data_dir="data"):
    """Wczytaj wszystkie parquety, filtruj do B737 w Europie."""
    files = sorted(glob.glob(f"{data_dir}/flight_list_*.parquet"))
    print(f"Wczytuję {len(files)} plików...")
    
    dfs = []
    for f in files:
        df = pd.read_parquet(f, filters=[('typecode', 'in', B737_TYPES)])
        eu_mask = (df['adep'].str.startswith(EU_PREFIXES, na=False) |
                   df['ades'].str.startswith(EU_PREFIXES, na=False))
        df = df[eu_mask].copy()
        dfs.append(df)
        print(f"  {f}: {len(df):,} B737 EU flights")
    
    combined = pd.concat(dfs, ignore_index=True)
    
    # WYMUŚ datetime - po concat może się zrobić mieszanka string/datetime
    combined['first_seen'] = pd.to_datetime(combined['first_seen'], errors='coerce')
    combined['last_seen'] = pd.to_datetime(combined['last_seen'], errors='coerce')
    
    # Wyrzuć wiersze gdzie konwersja się nie udała (były garbage stringi)
    before = len(combined)
    combined = combined.dropna(subset=['first_seen', 'last_seen']).copy()
    if before != len(combined):
        print(f"  Usunięto {before - len(combined)} wierszy z zepsutymi datami")
    
    print(f"\nDtypes po konwersji:")
    print(f"  first_seen: {combined['first_seen'].dtype}")
    print(f"  last_seen:  {combined['last_seen'].dtype}")
    print(f"\nŁącznie: {len(combined):,} lotów, {combined['icao24'].nunique()} unikalnych samolotów")
    return combined


def detect_gaps(df):
    """Wykryj przerwy między lotami per samolot."""
    df = df.sort_values(['icao24', 'first_seen']).reset_index(drop=True)
    
    # Shift następnego lotu tego samego samolotu
    df['next_first_seen'] = df.groupby('icao24')['first_seen'].shift(-1)
    df['next_adep'] = df.groupby('icao24')['adep'].shift(-1)
    
    # Gap = czas od końca lotu do startu następnego
    df['gap_hours'] = (df['next_first_seen'] - df['last_seen']).dt.total_seconds() / 3600
    df['gap_days'] = df['gap_hours'] / 24
    
    # Czy samolot wrócił do tego samego lotniska po przerwie (sygnał: stał w miejscu)
    df['stayed_put'] = (df['ades'] == df['next_adep'])
    
    return df


def classify_check(row):
    """Klasyfikacja regułowa (na razie - ML dorzucimy później)."""
    g = row['gap_days']
    if pd.isna(g) or g < 1:
        return None
    if g < 4:
        return 'A-check'
    if g < 14:
        return 'B-check'
    if g <= 60:
        return 'C-check'
    if g <= 120:
        return 'D-check'
    return 'storage'


def build_dashboard(df):
    """Zbuduj tabelę priorytetową z confidence levels."""
    NOW = pd.Timestamp("2026-05-22")
    SIX_MONTHS_AGO = NOW - pd.DateOffset(months=6)
    
    # Wszystkie kandydaci na C-check (bez ostrego filtra MRO+stayed_put)
    candidates = df[
        (df['check_type'] == 'C-check') &
        (df['gap_days'] > 0)
    ].copy()
    
    # Klasyfikacja confidence - to będą pseudo-labele dla ML
    candidates['at_strict_mro'] = candidates['ades'].isin(STRICT_MRO_HUBS)
    candidates['at_any_mro'] = candidates['ades'].isin(MRO_HUBS.keys())
    candidates['mro_facility'] = candidates['ades'].map(MRO_HUBS).fillna(
        candidates['ades'].fillna('Unknown')
    )
    
    def confidence(row):
        # HIGH: STRICT MRO hub - lotnisko gdzie B737 nie operuje liniowo
        # (EPWA, LBSF, LKMT, LROP, LZIB, LIRA, LPPT). Sam fakt 14-60 dni postoju
        # tutaj = niemal pewny C-check. stayed_put nadmiarowy (po check'u często
        # ferry flight nie wpada w ADS-B i next_adep wygląda jak baza operatora).
        if row['at_strict_mro']:
            return 'HIGH'
        # MEDIUM: hub operacyjny (Sofia, Istanbul, Amsterdam itd.) + samolot
        # rzeczywiście stał (kolejny lot z tego samego lotniska)
        if row['at_any_mro'] and row['stayed_put']:
            return 'MEDIUM'
        # LOW: hub operacyjny bez stayed_put LUB gap w nieznanym miejscu
        # - ambiguous, do weryfikacji przez ML w kroku 8
        return 'LOW'
    candidates['confidence'] = candidates.apply(confidence, axis=1)
    
    # SMART PICKER: per samolot wybieramy ostatni gap PREFERUJĄC wyższe confidence.
    # Czyli: jak był HIGH (np. EPWA 2024-05) i potem LOW (random 20-dni 2025-08),
    # to bierzemy ten HIGH - bo to prawdziwy C-check, a LOW to pewnie storage/AOG.
    # Sortuję ASC po (rank, last_seen), tail(1) bierze najwyższy rank, najnowszą datę.
    conf_rank = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    candidates['_conf_rank'] = candidates['confidence'].map(conf_rank)
    last_c = (candidates.sort_values(['_conf_rank', 'last_seen'])
              .groupby('icao24').tail(1)
              .drop('_conf_rank', axis=1)
              .copy())
    
    # Czy samolot jeszcze lata? Sprawdź z PEŁNEGO df (nie tylko C-checków)
    last_flight = df.groupby('icao24')['last_seen'].max()
    last_c['last_flight_seen'] = last_c['icao24'].map(last_flight)
    last_c['is_active'] = last_c['last_flight_seen'] >= SIX_MONTHS_AGO
    
    # Predykcja: ostatni C-check + 24 miesiące
    last_c['predicted_next'] = last_c['last_seen'] + pd.DateOffset(months=24)
    last_c['months_to_next'] = ((last_c['predicted_next'] - NOW).dt.days / 30).round(1)
    
    # KLUCZOWE: dla aktywnych samolotów z zaległą predykcją - REFORECAST
    # Znaczy że miały C-check którego nie złapaliśmy (np. w nieznanym MRO)
    # Predykuj na bazie ostatniego lotu: założenie że teraz lecą po check, następny za 24mies
    needs_reforecast = last_c['is_active'] & (last_c['months_to_next'] < -3)
    last_c.loc[needs_reforecast, 'predicted_next'] = (
        last_c.loc[needs_reforecast, 'last_flight_seen'] + pd.DateOffset(months=12)
    )
    last_c.loc[needs_reforecast, 'months_to_next'] = (
        (last_c.loc[needs_reforecast, 'predicted_next'] - NOW).dt.days / 30
    ).round(1)
    last_c['reforecasted'] = needs_reforecast
    
    def priority(row):
        if not row['is_active']:
            return 'Nieaktywny'
        m = row['months_to_next']
        if m < -3: return 'Status nieznany'  # nadal stare po reforecaście
        if m <= 0: return 'TERAZ (zaległe)'
        if m <= 6: return 'TERAZ'
        if m <= 12: return '6 mies.'
        if m <= 18: return '12 mies.'
        return 'Daleko'
    last_c['priorytet'] = last_c.apply(priority, axis=1)
    
    # Sortowanie po priorytecie
    order = {'TERAZ': 0, 'TERAZ (zaległe)': 1, '6 mies.': 2, '12 mies.': 3,
             'Daleko': 4, 'Status nieznany': 5, 'Nieaktywny': 6}
    last_c['_order'] = last_c['priorytet'].map(order)
    last_c = last_c.sort_values(['_order', 'months_to_next']).drop('_order', axis=1)
    
    return last_c[[
        'registration', 'icao_operator', 'icao24', 'typecode',
        'last_seen', 'gap_days', 'mro_facility', 'confidence',
        'predicted_next', 'months_to_next', 'priorytet',
        'is_active', 'reforecasted'
    ]].rename(columns={
        'last_seen': 'ostatni_c_check',
        'gap_days': 'czas_dni',
        'predicted_next': 'prognoza_next',
        'months_to_next': 'mies_do_next'
    })

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    log_path = OUTPUT_DIR / 'pipeline_log.txt'
    log_file = open(log_path, 'w', encoding='utf-8')
    sys.stdout = _Tee(sys.__stdout__, log_file)
    
    df = load_b737_eu()
    
    print("\n=== Detekcja gapów ===")
    df = detect_gaps(df)
    df['check_type'] = df.apply(classify_check, axis=1)
    print(df['check_type'].value_counts())
    
    print("\n=== Rozkład confidence dla WSZYSTKICH gapów C-check ===")
    # Liczę confidence raz globalnie żeby pokazać proporcje przed groupby per aircraft
    all_c = df[(df['check_type'] == 'C-check') & (df['gap_days'] > 0)].copy()
    all_c['at_strict_mro'] = all_c['ades'].isin(STRICT_MRO_HUBS)
    all_c['at_any_mro'] = all_c['ades'].isin(MRO_HUBS.keys())
    def _conf(r):
        if r['at_strict_mro']: return 'HIGH'
        if r['at_any_mro'] and r['stayed_put']: return 'MEDIUM'
        return 'LOW'
    all_c['confidence'] = all_c.apply(_conf, axis=1)
    print(f"Wszystkie gapy 14-60 dni: {len(all_c)}")
    print(all_c['confidence'].value_counts())
    print(f"  HIGH %: {(all_c['confidence']=='HIGH').mean()*100:.1f}")
    print(f"  MED  %: {(all_c['confidence']=='MEDIUM').mean()*100:.1f}")
    print(f"  LOW  %: {(all_c['confidence']=='LOW').mean()*100:.1f}")
    
    # Diagnostyka stayed_put w STRICT MRO - czy OPDI gubi loty pozycjonujące?
    # Jeśli stayed_put% wysoki (>70%) - ADS-B działa OK, stayed_put to dobry filtr
    # Jeśli niski (<50%) - OPDI gubi ferry flighty, stayed_put jest zbyt restrykcyjne
    strict_gaps = all_c[all_c['at_strict_mro']]
    if len(strict_gaps) > 0:
        sp_rate = strict_gaps['stayed_put'].mean() * 100
        print(f"\n  stayed_put% w STRICT MRO: {sp_rate:.1f}% (z {len(strict_gaps)} gapów)")
        print(f"  → jeśli <50%: OPDI gubi ferry flighty po C-check'u, stayed_put jest zbyt strict dla MEDIUM")
    
    # Per-airport breakdown - top 15 lotnisk gdzie B737 mają gapy 14-60 dni
    print(f"\n  TOP 15 lotnisk z gapami C-check (do weryfikacji listy MRO):")
    top_ades = all_c['ades'].value_counts().head(15)
    for ades, cnt in top_ades.items():
        in_strict = '★STRICT' if ades in STRICT_MRO_HUBS else ('●MRO' if ades in MRO_HUBS else '·LOW')
        facility = MRO_HUBS.get(ades, '')
        print(f"    {ades}: {cnt:4d} {in_strict}  {facility}")
    
    print("\n=== Dashboard ===")
    dashboard = build_dashboard(df)
    
    print(f"\nSamolotów w dashboardzie: {len(dashboard)}")
    print(f"\nRozkład priorytetów:")
    print(dashboard['priorytet'].value_counts())
    print(f"\nRozkład confidence (per samolot, ostatni gap):")
    print(dashboard['confidence'].value_counts())
    print(f"\nReforecast (samoloty gdzie zgadliśmy że miał check którego nie złapaliśmy): "
          f"{dashboard['reforecasted'].sum()}")
    
    print("\n=== TOP 20 priorytet TERAZ (aktywne, świeże predykcje) ===")
    active_now = dashboard[
        (dashboard['priorytet'].isin(['TERAZ', '6 mies.', '12 mies.'])) &
        (dashboard['is_active'])
    ].head(20)
    print(active_now[['registration', 'icao_operator', 'typecode', 'ostatni_c_check',
                      'czas_dni', 'mro_facility', 'confidence', 
                      'prognoza_next', 'mies_do_next', 'priorytet']].to_string())
    
    print(f"\n=== Klienci LOTAMS (historycznie w EPWA) ===")
    lotams = dashboard[dashboard['mro_facility'].str.contains('LOTAMS', na=False)]
    print(f"Łącznie: {len(lotams)}")
    print(lotams[['registration', 'icao_operator', 'ostatni_c_check', 
                  'prognoza_next', 'priorytet']].head(15).to_string())
    
    # === Zapis wyników do output/ (nadpisuje przy każdym uruchomieniu) ===
    dashboard_path = OUTPUT_DIR / 'dashboard.csv'
    lotams_path = OUTPUT_DIR / 'lotams_clients.csv'
    top_now_path = OUTPUT_DIR / 'top_priority_now.csv'
    
    dashboard.to_csv(dashboard_path, index=False, encoding='utf-8')
    lotams.to_csv(lotams_path, index=False, encoding='utf-8')
    # Tabela alertowa dla handlowca: TERAZ + 6m + 12m, aktywne
    top_now = dashboard[
        (dashboard['priorytet'].isin(['TERAZ', 'TERAZ (zaległe)', '6 mies.', '12 mies.'])) &
        (dashboard['is_active'])
    ]
    top_now.to_csv(top_now_path, index=False, encoding='utf-8')
    
    print(f"\n=== Zapisano wyniki ===")
    print(f"  {log_path}            (cały output terminala)")
    print(f"  {dashboard_path}      ({len(dashboard)} samolotów, pełna tabela)")
    print(f"  {lotams_path}  ({len(lotams)} klientów LOTAMS)")
    print(f"  {top_now_path}  ({len(top_now)} samolotów w oknie decyzyjnym)")
    
    sys.stdout = sys.__stdout__
    log_file.close()