import pandas as pd
import glob

# Wszystkie warianty 737
B737_TYPES = ['B736', 'B737', 'B738', 'B739', 'B37M', 'B38M', 'B39M', 'B3XM']

# Europejskie ICAO prefiksy
EU_PREFIXES = ('E', 'L', 'B')

# Lotniska MRO ważne dla LOTAMS i konkurencji
MRO_HUBS = {
    'EPWA': 'Warszawa - LOTAMS',
    'EDDH': 'Hamburg - Lufthansa Technik',
    'EDDM': 'München - Lufthansa Technik',
    'EIDW': 'Dublin - SR Technics',
    'LBSF': 'Sofia - Lufthansa Technik Sofia',
    'LTBA': 'Istanbul ATA - Turkish Technic',
    'LTFM': 'Istanbul IST - Turkish Technic',
    'LROP': 'Bukareszt - Romaero',
    'LKMT': 'Ostrava - Job Air Technic',
    'LZIB': 'Bratysława',
    'LPPT': 'Lizbona - TAP M&E',
    'LFLL': 'Lyon - AFI KLM E&M',
    'EHAM': 'Amsterdam - KLM E&M',
    'LSGG': 'Genewa - SR Technics',
    'LIRA': 'Rzym Ciampino - ATITECH',
    'LGAV': 'Ateny - Olympic Engineering',
}

# Strict subset - tu prawie na pewno C-check, nie zwykły parking
# (lotniska które NIE są dużymi hubami operacyjnymi B737)
STRICT_MRO_HUBS = {'EPWA', 'LBSF', 'LKMT', 'LROP', 'LZIB', 'LIRA', 'LPPT'}


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
        # HIGH: strict MRO + samolot wrócił na to lotnisko = pewny C-check
        if row['at_strict_mro'] and row['stayed_put']:
            return 'HIGH'
        # MEDIUM: w MRO hub, ale stayed_put nie potwierdzony (możliwy NaN w next_adep)
        if row['at_any_mro']:
            return 'MEDIUM'
        # LOW: gap w długości C-check, ale w nieznanym miejscu - może być AOG/storage
        return 'LOW'
    candidates['confidence'] = candidates.apply(confidence, axis=1)
    
    # Do dashboardu tylko HIGH + MEDIUM (LOW pójdzie do ML jako ambiguous)
    confirmed = candidates[candidates['confidence'].isin(['HIGH', 'MEDIUM'])]
    
    # Najnowszy potwierdzony C-check per samolot
    last_c = (confirmed.sort_values('last_seen')
              .groupby('icao24').tail(1).copy())
    
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
    df = load_b737_eu()
    
    print("\n=== Detekcja gapów ===")
    df = detect_gaps(df)
    df['check_type'] = df.apply(classify_check, axis=1)
    print(df['check_type'].value_counts())
    
    print("\n=== Dashboard ===")
    dashboard = build_dashboard(df)
    
    print(f"\nSamolotów w dashboardzie: {len(dashboard)}")
    print(f"\nRozkład priorytetów:")
    print(dashboard['priorytet'].value_counts())
    print(f"\nRozkład confidence:")
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