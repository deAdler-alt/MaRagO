import requests
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

Path("data").mkdir(exist_ok=True)

start = datetime(2023, 1, 1)
end = datetime(2026, 4, 1)

current = start
while current <= end:
    yyyymm = current.strftime('%Y%m')
    fname = f"flight_list_{yyyymm}.parquet"
    fpath = Path("data") / fname
    
    if not fpath.exists():
        url = f"https://www.eurocontrol.int/performance/data/download/OPDI/v002/flight_list/{fname}"
        print(f"Pobieram {fname}...")
        try:
            r = requests.get(url, stream=True, timeout=60)
            if r.status_code == 200:
                with open(fpath, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                print(f"  OK ({fpath.stat().st_size / 1e6:.1f} MB)")
            else:
                print(f"  FAIL status={r.status_code}")
        except Exception as e:
            print(f"  ERROR: {e}")
    else:
        print(f"{fname} już jest, pomijam")
    
    current += relativedelta(months=1)

print("Gotowe.")