# src/scoring — Priorytetyzacja i ranking

## Co tu jest

**`priority.py`** — przypisuje każdemu samolotowi pasmo priorytetu i urgency score.

## Jak działa scoring

```
contact_window_start = next_ccheck_date − 18 mies.
contact_window_end   = next_ccheck_date − 6 mies.

TERAZ     → samolot w oknie kontaktowym LUB < 3 mies. do C-checka
6 mies.   → 0–9 mies. do contact_window_start
12 mies.  → 9–18 mies. do contact_window_start
Daleko    → > 18 mies.
```

`urgency_score` (0–100): wyższy = pilniejszy. Używany do sortowania listy.

## Dlaczego 6–18 miesięcy?

C-check trwa 3–6 tygodni i wymaga:
- slotu w hangarze (planowanie 6–12 mies. naprzód)
- zamówienia komponentów (lead time 3–6 mies.)
- negocjacji kontraktu (1–3 mies.)

Jeśli handlowiec dzwoni gdy samolot już wjechał do hangaru — jest za późno.
Optimum: **12 miesięcy przed** prognozowanym C-checkiem.

## Parametry (config.yaml)

```yaml
ccheck:
  contact_window_start_months: 18  # kiedy zaczyna się okno decyzyjne
  contact_window_end_months: 6     # kiedy kończy się (zbyt późno)
```

## Relacja do ML pipeline

Ten moduł (`src/scoring/`) jest używany przez `src/pipeline/build.py`.
Główny pipeline ML (`train_classifier.py` + `predict.py`) oblicza priorytety
bezpośrednio w `predict.py` i zapisuje do `output/predictions_with_interval.csv`.
Streamlit dashboard (`app/`) czyta z tego pliku.
