# MRO Intelligence Platform — LOTAMS

Platforma BI do wykrywania okien C-check samolotów Boeing 737 w Europie na podstawie danych telemetrycznych ADS-B (EUROCONTROL OPDI). Służy handlowcom LOTAMS do identyfikacji potencjalnych klientów przed ich decyzją o wyborze zakładu MRO.

## Szybki start

```bash
pip install -r requirements.txt

# 1. Pobierz dane OPDI (ok. 1.6 GB, można uruchomić w tle)
python download_opdi.py

# 2. Pipeline ETL + cechy ML + model + predykcje
python pipeline.py
python features.py
python train_classifier.py
python predict.py

# 3. Uruchom dashboard
streamlit run app/main.py
```

Wszystkie outputy trafiają do `output/` i są nadpisywane przy każdym uruchomieniu.

## Architektura

```
data/                       # Surowe parquety OPDI (2023-01 → 2026-04)
│
├── pipeline.py             # ETL: loty B737 → gapy serwisowe → dashboard.csv
├── features.py             # 48 cech ML per gap (intensity, location, history…)
├── train_classifier.py     # LightGBM binary classifier (C-check vs. nie)
├── predict.py              # Per-aircraft interwał → predictions_with_interval.csv
│
output/                     # Pliki CSV generowane przez pipeline
│   ├── predictions_with_interval.csv   # Główne wejście dashboardu
│   ├── predictions.csv                 # Surowe predykcje per gap
│   ├── dashboard.csv                   # Fallback (bez interwałów)
│   ├── features.csv                    # Feature matrix
│   ├── feature_importance.csv          # LightGBM gain per feature
│   └── lotams_clients.csv              # Historyczni klienci EPWA
│
app/
│   ├── main.py             # Executive Overview (KPI tiles, donut, top 10)
│   ├── data_loader.py      # Warstwa danych z cache (@st.cache_data)
│   ├── style.py            # Globalny CSS + komponenty HTML (dark theme)
│   └── pages/
│       ├── 01_fleet.py     # Fleet Priority — pełna lista z filtrami
│       ├── 02_aircraft.py  # Aircraft Deep Dive — historia i timeline per samolot
│       ├── 03_alerts.py    # Commercial Alerts — centrum sprzedaży + generator e-mail
│       └── 04_insights.py  # ML Insights — mapa MRO, sezonowość, feature importance
│
src/                        # Moduły używane przez testy i scripts/run_pipeline.py
tests/                      # Testy jednostkowe (pytest)
scripts/                    # Helper: run_pipeline.py / run_pipeline.sh
```

## Dashboard — strony

| Strona | Opis |
|---|---|
| **Executive Overview** | Przegląd KPI: liczba TERAZ / 6 mies. / HIGH confidence. Donut priorytetów + metodologia. |
| **Fleet Priority** | Pełna lista B737 z filtrami (priorytet, confidence, kraj, operator, ML probability). |
| **Aircraft Deep Dive** | Gantt timeline przerw serwisowych per samolot + kontekst sprzedażowy. |
| **Commercial Alerts** | Lista alertów + per-operator + generator szablonu e-mail + tygodniowy digest. |
| **ML Insights** | Mapa MRO Europy, heatmapa sezonowości, histogram predykcji, feature importance. |

## Metryki modelu

- **2 761** unikalnych B737 w Europie geograficznej
- **3 651** kandydatów na C-check (gapy 14–60 dni w EU, 2023–2026)
- LightGBM: **AUC 0.975**, **Precision@200 = 0.950** (time-based holdout 2025-07 → 2026-04)
- Per-aircraft interwał: 456 samolotów z własną historią, 65 operatorów
- **37** historycznych klientów LOTAMS wykrytych (gap w EPWA Warszawa)

## Priorytety C-check

| Symbol | Pasmo | Znaczenie |
|---|---|---|
| 🚨 TERAZ (zaległe) | < 0 mies. | Prognozowany C-check minął — zadzwoń dziś |
| 🔴 TERAZ | 0–6 mies. | Ostatnie okno decyzyjne — wyślij ofertę teraz |
| 🟡 6 mies. | 6–12 mies. | Idealne okno prospectingowe |
| 🔵 12 mies. | 12–18 mies. | Obserwuj, buduj relację |
| ⚪ Daleko | > 18 mies. | Baza do przyszłości |
| ⬛ Nieaktywny | — | Nie latał > 6 mies. |

## Confidence (pewność wykrycia C-check)

| Symbol | Znaczenie |
|---|---|
| 🟢 HIGH | Przerwa w dedykowanym MRO (EPWA, LKMT, LBSF…) — niemal pewny C-check |
| 🟡 MEDIUM | Hub z możliwościami MRO (EHAM, LTBA…) — prawdopodobny C-check |
| 🔴 LOW | ML ocenił jako C-check mimo nieznaną lokalizację |

## Dane

Dane: EUROCONTROL OPDI · 7M+ lotów B737 EU · styczeń 2023 → kwiecień 2026.  
Klasyfikacja ADS-B to sygnał pośredni, nie dokumentacja MRO.
