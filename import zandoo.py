import requests
from pathlib import Path
import pandas as pd

Path("data").mkdir(exist_ok=True)
months = ['20220701_20220731', '20220801_20220831', '20220901_20220930',
          '20221001_20221031', '20221101_20221130', '20221201_20221231']

for m in months:
    fname = f"flightlist_{m}.csv.gz"
    if not Path(f"data/{fname}").exists():
        url = f"https://zenodo.org/records/7923702/files/{fname}"
        print(f"Pobieram {fname}...")
        r = requests.get(url, stream=True)
        with open(f"data/{fname}", "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
print("Gotowe")