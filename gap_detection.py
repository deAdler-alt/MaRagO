import pandas as pd
import glob

# Wczytaj wszystkie 6 miesięcy
files = sorted(glob.glob("data/flightlist_2022*.csv.gz"))
df = pd.concat([pd.read_csv(f, compression='gzip') for f in files], ignore_index=True)

# Parsuj timestampy
df['firstseen'] = pd.to_datetime(df['firstseen'], utc=True)
df['lastseen'] = pd.to_datetime(df['lastseen'], utc=True)

# Filter do B737 w Europie
EU_PREFIXES = ('E', 'L', 'B')
b737 = df[
    df['typecode'].isin(['B737','B738','B739','B37M','B38M']) &
    (df['origin'].str.startswith(EU_PREFIXES, na=False) |
     df['destination'].str.startswith(EU_PREFIXES, na=False))
].copy()

# Sortuj chronologicznie per samolot
b737 = b737.sort_values(['icao24', 'firstseen']).reset_index(drop=True)

# Gap = czas między końcem tego lotu a początkiem następnego dla tego samego samolotu
b737['next_firstseen'] = b737.groupby('icao24')['firstseen'].shift(-1)
b737['next_origin'] = b737.groupby('icao24')['origin'].shift(-1)
b737['gap_hours'] = (b737['next_firstseen'] - b737['lastseen']).dt.total_seconds() / 3600
b737['gap_days'] = b737['gap_hours'] / 24

print(b737['gap_days'].describe())
print("\nGapy > 7 dni:")
print(b737[b737['gap_days'] > 7]['gap_days'].describe())

def classify_check(row):
    g = row['gap_days']
    if pd.isna(g) or g < 1:
        return None
    if g < 4:
        return 'A-check'
    if g < 14:
        return 'B-check'
    if g <= 60:                   # 3-6 tygodni jak w briefie LOTAMS
        return 'C-check'
    if g <= 120:                  # 1-3 miesiące
        return 'D-check'
    return 'storage/leased-out'   # >4 miesięcy = już nie przegląd, to inny biznes

b737['check_type'] = b737.apply(classify_check, axis=1)

# Ile czego widzimy
print(b737['check_type'].value_counts())

# Wszystkie C-check candidates z lokalizacją gdzie się zaczęły
c_checks = b737[b737['check_type'] == 'C-check'].copy()
c_checks['gap_location'] = c_checks['destination']  # lotnisko gdzie samolot przyleciał przed przerwą
print("\nTop 15 lokalizacji C-check:")
print(c_checks['gap_location'].value_counts().head(15))

# Hardcodowana lista europejskich MRO huba (rozszerzona)
MRO_HUBS = {
    'EPWA': 'Warszawa Okęcie - LOTAMS',
    'EDDH': 'Hamburg - Lufthansa Technik',
    'EDDM': 'München - Lufthansa Technik',
    'EIDW': 'Dublin - SR Technics / Lufthansa Technik',
    'LBSF': 'Sofia - Lufthansa Technik Sofia',
    'LTBA': 'Istanbul Atatürk - Turkish Technic',
    'LTFM': 'Istanbul IST - Turkish Technic',
    'LROP': 'Bukareszt Otopeni - Romaero',
    'LKMT': 'Ostrava - Job Air Technic',
    'EHAM': 'Amsterdam - KLM E&M',
    'LSGG': 'Genewa - SR Technics',
    'LFMN': 'Nicea - Sabena Technics',
    'LIRA': 'Rzym Ciampino - ATITECH',
    'EGNX': 'East Midlands - 2 Excel Aviation',
    'LGAV': 'Ateny - Olympic Engineering',
}

# Strict EU filter: oba lotniska w EU + prawidłowy 4-literowy kod ICAO
def is_eu_icao(code):
    if pd.isna(code) or len(str(code)) != 4:
        return False
    return str(code).isalpha() and str(code)[0] in ('E', 'L', 'B')

b737_strict = b737[
    b737['origin'].apply(is_eu_icao) & b737['destination'].apply(is_eu_icao)
].copy()

# Przelicz gapy ponownie na zacieśnionym dataset
b737_strict = b737_strict.sort_values(['icao24', 'firstseen']).reset_index(drop=True)
b737_strict['next_firstseen'] = b737_strict.groupby('icao24')['firstseen'].shift(-1)
b737_strict['gap_days'] = (b737_strict['next_firstseen'] - b737_strict['lastseen']).dt.total_seconds() / 86400
b737_strict['check_type'] = b737_strict.apply(classify_check, axis=1)

# C-checks w prawdziwych MRO hubach
c_checks_real = b737_strict[
    (b737_strict['check_type'] == 'C-check') &
    (b737_strict['gap_days'] > 0) &                          # wywal ujemne
    (b737_strict['destination'].isin(MRO_HUBS.keys()))       # tylko prawdziwe MRO
].copy()

c_checks_real['mro_facility'] = c_checks_real['destination'].map(MRO_HUBS)

print(f"\nC-checks w prawdziwych MRO hubs: {len(c_checks_real)}")
print(c_checks_real['destination'].value_counts())
print(f"\nUnikalnych samolotów z C-check: {c_checks_real['icao24'].nunique()}")
print(f"\nUnikalnych operatorów: {c_checks_real['callsign'].str[:3].nunique()}")

# Pokaz top samolotów które dostały C-check w Warszawie - to są REALNI klienci LOTAMS
print("\n=== KLIENCI LOTAMS (C-check w Warszawie) ===")
lotams = c_checks_real[c_checks_real['destination'] == 'EPWA']
print(lotams[['registration','icao24','lastseen','gap_days','callsign']].head(20))

import pandas as pd

# Mapowanie ICAO operator → czytelna nazwa
OPERATOR_MAP = {
    'LOT': 'LOT Polish Airlines',
    'ENT': 'Enter Air',
    'TVS': 'Smartwings',
    'TUI': 'TUI fly',
    'JAF': 'TUI fly Belgium',
    'RYR': 'Ryanair', 'RUK': 'Ryanair UK',
    'WZZ': 'Wizz Air',
    'EZY': 'easyJet', 'EJU': 'easyJet Europe',
    'BEL': 'Brussels Airlines',
    'PGT': 'Pegasus', 'THY': 'Turkish Airlines',
    'SUN': 'SunExpress',
    'NOZ': 'Norwegian', 'NSZ': 'Norwegian',
    'KLM': 'KLM',
    'DLH': 'Lufthansa',
    'AEE': 'Aegean',
    'IBE': 'Iberia',
    'AFR': 'Air France',
    'BAW': 'British Airways',
    'AUA': 'Austrian',
    'SWR': 'Swiss',
    'TAP': 'TAP Portugal',
    'CSA': 'Czech Airlines',
    'MAS': 'Malaysia Airlines',  # zdarzają się ferry flights
    'PLF': 'Polish Air Force',
}

# Dla każdego samolotu - tylko ostatni wykryty C-check (deduplikacja)
last_c_check = (c_checks_real
    .sort_values('lastseen')
    .groupby('icao24')
    .tail(1)
    .copy())

# Wyciągnij ICAO operator code z callsign
last_c_check['operator_icao'] = last_c_check['callsign'].str[:3]
last_c_check['operator'] = last_c_check['operator_icao'].map(OPERATOR_MAP).fillna(last_c_check['operator_icao'])

# Predykcja next C-check: ostatni + 24 miesiące (typowy interval)
last_c_check['last_c_check_date'] = last_c_check['lastseen']
last_c_check['predicted_next_c_check'] = last_c_check['last_c_check_date'] + pd.DateOffset(months=24)

# Ile miesięcy do okna decyzyjnego (6-18 miesięcy przed terminem)
# "TERAZ" = predicted minus 6 miesięcy <= teraz (czyli już w oknie)
NOW = pd.Timestamp("2026-05-22", tz="UTC")
last_c_check['months_to_next'] = (
    (last_c_check['predicted_next_c_check'] - NOW).dt.days / 30
).round(1)

def priority(months):
    if months < 0:           # już po terminie
        return 'TERAZ (zaległe)'
    if months <= 6:           # w oknie decyzyjnym
        return 'TERAZ'
    if months <= 12:
        return '6 mies.'
    if months <= 18:
        return '12 mies.'
    return 'Daleko'

last_c_check['priorytet'] = last_c_check['months_to_next'].apply(priority)

# Finalna tabela do dashboardu
dashboard = last_c_check[[
    'registration', 'operator', 'icao24',
    'last_c_check_date', 'gap_days', 'destination',
    'predicted_next_c_check', 'months_to_next', 'priorytet'
]].rename(columns={
    'destination': 'mro_facility',
    'gap_days': 'czas_trwania_dni',
    'last_c_check_date': 'ostatnie_okno',
    'predicted_next_c_check': 'prognoza_c_check'
}).sort_values('months_to_next')

# Pokaz top 20 priorytetowych
print("\n=== TOP 20 PRIORYTETOWYCH SAMOLOTÓW ===")
print(dashboard.head(20).to_string())

# Statystyki dla pitchu
print(f"\n=== STATYSTYKI ===")
print(f"Łącznie samolotów w bazie: {len(dashboard)}")
print(f"W priorytecie TERAZ: {(dashboard['priorytet'].str.contains('TERAZ')).sum()}")
print(f"W ciągu 6 mies: {(dashboard['priorytet'] == '6 mies.').sum()}")
print(f"Klienci LOTAMS (Warszawa): {(dashboard['mro_facility'] == 'EPWA').sum()}")
print(f"\nRozkład operatorów (top 10):")
print(dashboard['operator'].value_counts().head(10))