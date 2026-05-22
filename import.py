import pandas as pd

url = "https://www.eurocontrol.int/performance/data/download/OPDI/v002/flight_list/flight_list_202401.parquet"
df = pd.read_parquet(url)  # pyarrow ssie bezpośrednio z URL
print(df.shape)
print(df.columns)
print(df.head())

print(df.shape)
print(df.columns.tolist())
print(df.dtypes)
print(df.head(3))
print(f"Unikalnych icao24: {df['icao24'].nunique()}")

import pandas as pd

acdb = pd.read_csv("https://s3.opensky-network.org/data-samples/metadata/aircraftDatabase.csv",
                  low_memory=False)
print(acdb['typecode'].value_counts().head(10))  # sprawdź czy B738 jest top

b737 = acdb[acdb['typecode'].isin(['B737','B738','B739'])][
    ['icao24','registration','typecode','operator','built']
].copy()
print(f"B737 w bazie OpenSky: {len(b737)}")  # spodziewaj się kilku tysięcy

# Lowercase icao24 dla pewności (OPDI vs OpenSky bywa case-sensitive)
df['icao24'] = df['icao24'].str.lower()
b737['icao24'] = b737['icao24'].str.lower()

flights_b737 = df.merge(b737, on='icao24', how='inner')
print(f"Lotów B737 w tym miesiącu: {len(flights_b737)}")
print(f"Unikalnych samolotów: {flights_b737['icao24'].nunique()}")
print(flights_b737[['registration','operator','typecode']].drop_duplicates().head(20))

print(acdb.shape)
print(acdb.columns.tolist())
print(acdb['typecode'].value_counts().head(15) if 'typecode' in acdb.columns else "NO typecode column!")
print(f"\nb737 rows: {len(b737)}")
print(f"flights_b737 columns: {flights_b737.columns.tolist()}")