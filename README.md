# MRO Prediction Platform

System wykrywania C-checków samolotów B737 w Europie na podstawie danych ADS-B (OPDI) + predykcja następnego C-check'a per samolot. Dla handlowców LOTAMS.

## Quickstart

pip install -r requirements.txt
```
python download_opdi.py     # ~1.6 GB, w tle
python inspect_opdi.py      # sanity check schematu
python pipeline.py          # ETL + dashboard regułowy
python features.py          # 48 kolumn featurów pod ML
python train_classifier.py  # LightGBM, AUC ~0.98 na holdout
python predict.py           # per-aircraft interval → predictions_with_interval.csv
```

Wszystkie outputy → `output/` (nadpisywane przy każdym runie).

## Stan projektu i przekazanie

**→ Przeczytaj [`Zrobione.md`](Zrobione.md)** ← stan na teraz, co dalej, decyzje techniczne, gotchas.

**→ [`ROADMAP.md`](ROADMAP.md)** ← pełny plan kroków 1–11 z architekturą i kontekstem biznesowym.

## Aktualne metryki (kroki 8–9 done)

- 2,761 unikalnych B737 w geograficznej Europie
- 3,651 kandydatów na C-check (gapy 14-60 dni w EU)
- LightGBM: **AUC ~0.97**, **Precision@100 ≈ 1.000** na time-based holdout
- 37 historycznych klientów LOTAMS wykrytych
- Per-aircraft interval: 456 samolotów z własną historią, 65 operatorów, globalny avg 507d (16.6 mies.)