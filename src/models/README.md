# src/models — Klasyfikacja C-checków i predykcja

## Pliki

### `classify_check.py`
Reguły klasyfikacji przerwy → typ check'a.

```
Długość przerwy   → check_type + confidence score
  1–3 dni         → A-check
  4–5 dni         → B-check
  21–55 dni       → C-check      ← główny produkt LOTAMS
  ≥ 60 dni        → D-check
```

Boosting confidence jeśli lotnisko jest w `mro_hubs` lub `strict_mro_hubs` (z config.yaml).

### `predict_ccheck.py`
Predykcja daty następnego C-checka per samolot (reguły + heurystyki).

Algorytm:
1. Znajdź ostatni wykryty C-check per samolot
2. Oblicz interwał na podstawie `base_interval_months` (27 mies. default)
3. Korekta: starszy samolot (≥12 lat) → interwał krótszy (−12%)
4. Korekta: wysokie/niskie wykorzystanie → ±3 mies.
5. Reforecast: jeśli aktywny samolot ma przeterminowaną prognozę → `ostatni lot + 12 mies.`

**Ten moduł zastąpiony przez `predict.py`** (root) w głównym pipeline ML.
`predict.py` używa per-aircraft interwałów z historii potwierdzonych C-checków
(c_check_probability > 0.7) zamiast stałego `base_interval_months`.

## Relacja do głównego pipeline

```
src/models/          →  src/pipeline/build.py  →  data/processed/predictions.parquet
train_classifier.py  →  predict.py             →  output/predictions_with_interval.csv  ← Streamlit używa tego
```

Oba dają ten sam wynik koncepcyjnie, ale `predict.py` ma:
- LightGBM c_check_probability (AUC 0.975)
- Per-aircraft interwał z danych historycznych (nie stała 27 mies.)
- 3 651 kandydatów vs ~1 684 w uproszczonym pipeline
