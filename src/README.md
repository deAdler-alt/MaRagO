# src/ — Moduły pomocnicze

Paczka Python z logiką pipeline'u, klasyfikacji i scoringu.
Używana przez `app/` (Streamlit) i `scripts/`.

## Struktura

```
src/
├── config.py          # load_config() — czyta config.yaml
├── ingest/
│   ├── opdi.py        # Pobieranie danych z EUROCONTROL OPDI (parquet)
│   └── demo.py        # 6 przykładowych samolotów do testów bez danych
├── features/
│   └── gaps.py        # detect_gaps() — detekcja przerw w aktywności ADS-B
├── models/
│   ├── classify_check.py   # Klasyfikacja gap → A/B/C/D check + confidence
│   └── predict_ccheck.py   # Predykcja next C-check per samolot (reguły)
├── pipeline/
│   └── build.py       # run_pipeline() — full pipeline → parquet output
└── scoring/
    └── priority.py    # assign_priority() — TERAZ/6mies/12mies/Daleko
```

## Relacja do głównego pipeline

Główny ML pipeline (root skrypty):

```
pipeline.py → features.py → train_classifier.py → predict.py → output/*.csv
```

Streamlit (`app/`) czyta z `output/predictions_with_interval.csv`.
Moduły `src/` są alternatywną implementacją do szybkiego testowania na danych demo.

## Demo mode

```python
# config.yaml
data_mode: demo  # zamiast opdi
```

Uruchamia pipeline na 6 syntetycznych samolotach z `src/ingest/demo.py`.
Przydatne do development/testowania bez ~1.6 GB danych OPDI.
