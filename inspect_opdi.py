import pandas as pd
import glob

files = sorted(glob.glob("data/flight_list_*.parquet"))
if not files:
    print("Brak plików jeszcze, poczekaj na download")
else:
    print(f"Znaleziono {len(files)} plików")
    df = pd.read_parquet(files[0])
    print(f"\n=== Plik: {files[0]} ===")
    print(f"Wierszy: {len(df):,}")
    print(f"\nKolumny: {df.columns.tolist()}")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nPierwszy wiersz:")
    for col, val in df.iloc[0].items():
        print(f"  {col}: {val}")
    
    if 'model' in df.columns:
        print(f"\n=== TOP 20 modeli ===")
        print(df['model'].value_counts().head(20))
        b737 = df[df['model'].str.contains('737', na=False, case=False)]
        print(f"\nB737 w tym miesiącu: {len(b737):,} lotów, {b737['icao24'].nunique()} samolotów")