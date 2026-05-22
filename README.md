# MRO Prediction Platform

Dashboard dla LOTAMS: wczesne wykrywanie okien C-check na flocie Boeing 737 w Europie na podstawie przerw w aktywności lotniczej (EUROCONTROL OPDI + OpenSky).

## Problem

Handlowiec LOTAMS dowiaduje się o przeglądzie za późno — gdy samolot znika z trasy na 3–6 tygodni, kontrakt jest już u konkurencji (Lufthansa Technik, AFI KLM E&M, Turkish Technic). System daje sygnał **6–18 miesięcy wcześniej**.

## Szybki start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Demo (6 samolotów z briefu — szybkie)
python scripts/run_pipeline.py --demo

# Pełne dane OPDI (6 miesięcy, ~5–15 min)
python scripts/run_pipeline.py --rebuild-flights

# Dashboard
streamlit run app/main.py
```

Alternatywnie: `./scripts/run_pipeline.sh demo` lub `./scripts/run_pipeline.sh opdi`

## Architektura

```
OPDI parquet (EUROCONTROL)  ──┐
                               ├── merge icao24 ──► gaps ──► classify ──► predict ──► priority
OpenSky aircraftDatabase.csv ──┘
```

| Moduł | Plik | Rola |
|-------|------|------|
| Ingest | `src/ingest/opdi.py` | Pobranie OPDI, filtr B737, cache |
| Gaps | `src/features/gaps.py` | Wykrywanie przerw bez lotów |
| Classify | `src/models/classify_check.py` | A/B/C/D-check z długości przerwy |
| Predict | `src/models/predict_ccheck.py` | Prognoza C-check + okno kontaktu |
| Priority | `src/scoring/priority.py` | TERAZ / 6m / 12m / Daleko |
| UI | `app/` | Streamlit: tabela, timeline, alerty |

## Konfiguracja

[`config.yaml`](config.yaml):

- `data_mode`: `opdi` | `demo`
- `opdi.months`: lista miesięcy YYYYMM
- `checks`: progi dni dla A/B/C/D-check
- `mro_hubs`: lotniska MRO (WAW, HAM, IST…)

## Źródła danych

| Źródło | URL | Rola |
|--------|-----|------|
| EUROCONTROL OPDI | `eurocontrol.int/.../flight_list_YYYYMM.parquet` | Loty w Europie |
| OpenSky | `aircraftDatabase.csv` | Filtr B737, operator, rok `built` |

## Disclaimer

Klasyfikacja opiera się na **przerwach w danych lotniczych** — sygnał pośredni, nie potwierdzenie dokumentacji MRO. Skupiamy się na **C-check** jako głównym produkcie LOTAMS.

## Testy

```bash
pytest tests/ -v
```

## Eksploracja schema OPDI

```bash
python -m src.ingest.opdi --explore
# lub
python import.py --explore
```
