import pandas as pd

df = pd.read_csv("data/flightlist_20221201_20221231.csv.gz", compression='gzip')
print(df.shape)                              # (~2.5M, 10)
print(df.columns.tolist())                   # czy typecode/registration jest
print(df['typecode'].value_counts().head(10))  # czy B738 w top 3

# Filter do B737 w Europie (origin LUB destination zaczyna się na E/L/B)
b737 = df[df['typecode'].isin(['B737','B738','B739','B37M','B38M'])].copy()
eu_prefixes = ('E','L','B')  # E=ICAO Europa, L=ICAO South Europe, B=Baltic/Iceland
b737_eu = b737[
    b737['origin'].str.startswith(eu_prefixes, na=False) |
    b737['destination'].str.startswith(eu_prefixes, na=False)
]
print(f"B737 EU w grudniu 2022: {b737_eu['icao24'].nunique()} samolotów, {len(b737_eu)} lotów")