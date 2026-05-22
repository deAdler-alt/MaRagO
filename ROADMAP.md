# MRO Prediction Platform – Roadmapa Hackathonu

**Klient:** LOTAMS (Warszawa) · **Scope:** B737 w Europie · **Deadline:** koniec hackathonu

## Cel projektu

Zbudować dashboard, który dla każdego Boeinga 737 w Europie:

1. Wykrywa historyczne C-checki na podstawie przerw w danych ADS-B
2. Klasyfikuje typ przeglądu (A/B/C/D vs storage/AOG)
3. Przewiduje datę następnego C-checka
4. Wyświetla tabelę priorytetową dla handlowca: który samolot wpadnie w okno decyzyjne (6–18 mies. przed terminem) i kiedy się odezwać

**Wartość biznesowa:** zamiast ręcznego przeszukiwania portali (godziny tygodniowo per handlowiec), system codziennie wskazuje top samolotów do kontaktu, sortuje po dacie i sugeruje pierwszy kontakt z 6-mies. wyprzedzeniem względem konkurencji.

## Architektura wysokopoziomowa

```
OPDI Parquet (40 mies., 5M+ lotów B737 EU)
        ↓
  load_b737_eu()           ← filtr typecode + EU
        ↓
  detect_gaps()            ← przerwy per icao24
        ↓
  classify_check()         ← reguły A/B/C/D
        ↓
  build_dashboard()        ← confidence levels (HIGH/MED/LOW)
        ↓
  ML classifier (LGBM)     ← pseudo-labels z reguł → klasyfikator real vs not
        ↓
  Per-aircraft interval    ← lepsza predykcja niż +24mies
        ↓
  Streamlit app            ← 3 widoki: priorytet / timeline / alert
        ↓
  Pitch + demo
```

## Status

### Zrobione

- [x] Setup projektu, requirements.txt
- [x] Identyfikacja OPDI jako źródła danych (2022-01 → 2026-04)
- [x] `download_opdi.py` – ściąganie parquet z eurocontrol.int
- [x] `inspect_opdi.py` – walidacja schematu
- [x] `pipeline.py` – load, gap detection, klasyfikacja regułowa, dashboard v1
- [x] Walidacja na 29+ plikach: 5.1M+ lotów, 2755 samolotów (zgodne z brief "2000+")
- [x] Dashboard v2 – confidence (HIGH/MEDIUM/LOW), is_active, reforecast dla zaległych

### W trakcie

- [ ] Sanity check outputu dashboard v2

### Do zrobienia

- [ ] Feature engineering pod ML
- [ ] LightGBM classifier (pseudo-labelling)
- [ ] Per-aircraft historical interval
- [ ] Streamlit dashboard (3 widoki)
- [ ] Pitch deck + demo script

## Roadmapa szczegółowa

### Krok 1–5: Pipeline (✅ DONE, ~3h)

Setup + data + pipeline regułowy. Pomijam dalsze szczegóły, wszystko działa.

### Krok 6: Dashboard v2 (🔄 ~30 min)

Wprowadzone w build_dashboard:

- **Confidence levels:**
  - `HIGH` = STRICT_MRO_HUB (EPWA, LBSF, LKMT, LROP, LZIB, LIRA, LPPT) + `stayed_put=True`
  - `MEDIUM` = inne MRO huby (EHAM, LTBA, LTFM, EDDH itd.) – mogą być huby operacyjne
  - `LOW` = długi gap (3-6 tyg.) ale w nieznanym miejscu – te idą do ML jako ambiguous

- **is_active:** samolot widziany w ostatnich 6 mies. Jeżeli nie – `priorytet = "Nieaktywny"` (sprzedany/wyleased/wycofany)

- **Reforecast:** dla aktywnych samolotów z zaległą predykcją (`mies_do_next < -3`) – zakładamy że miały C-check którego nie złapaliśmy. Predict = ostatni lot + 12 mies.

**Sanity check przed kolejnym krokiem:**
- Samolotów w dashboardzie: 500–1500 (vs 233 w v1)
- Confidence: HIGH ~30%, MEDIUM ~50%, LOW ~20%
- TERAZ/6m/12m razem: ~30% floty (sensowne)

### Krok 7: Feature engineering (⏳ ~1.5h)

Nowy plik `features.py`. Dla każdego gapa dodać kolumny:

**Gap-level:**
- `gap_duration_days` (mamy)
- `gap_start_month` (1-12) – sezonowość storage
- `gap_start_dow` (0-6)
- `ades` / `next_adep`
- `at_strict_mro_hub`, `at_any_mro_hub`, `at_operator_main_base`
- `destination_country_matches_registration` (np. SP-LVB w EPWA = ✓)

**Aircraft-level:**
- `typecode` (B738/B73M/etc.)
- `registration_country` (z prefiksu)
- `aircraft_age_years` (z OPDI lub Airfleets – TODO jeśli czas)

**Pre-gap (60 dni przed):**
- `flights_per_day_pre_gap`
- `flights_per_day_trend` (slope ostatnie 30 dni)
- `distinct_airports_pre_gap`
- `avg_flight_duration_pre_gap_hours`

**Post-gap (30 dni po):**
- `same_operator_after` (icao_operator matches)
- `same_country_after`
- `days_to_first_flight_after`

**Operator-level:**
- `operator_fleet_size_in_data`
- `operator_typical_mro_for_b737` (najczęstszy MRO hub dla tego operatora)
- `gap_at_unusual_airport_for_operator` (boolean)

**Historyczne:**
- `num_previous_c_check_candidates_for_this_aircraft`
- `mean_interval_between_previous_c_checks` (jeśli ≥2 wcześniejszych)

### Krok 8: ML classifier (⏳ ~3h)

Nowy plik `train_classifier.py`.

**Cel:** binarna klasyfikacja `is_real_c_check` (1) vs `other_long_gap` (0).

**Pseudo-labelling:**

```
HIGH confidence → label = 1 (positive)
MEDIUM confidence + stayed_put + same_operator_after → label = 1
gap > 90 dni → label = 0 (storage/lease)
gap < 21 dni → label = 0 (probably AOG, not enough for full C-check)
at_operator_main_base + duration 20-40 days → label = 0 (probably parking)
different_operator_after → label = 0 (lease return)
ELSE → label = None (do predykcji, nie trening)
```

**Model:** LightGBM binarny, class_weight='balanced', stratified 5-fold CV.

**Output:** `c_check_probability` 0.0–1.0 dla każdego gapa.

**Walidacja dla pitchu:**
- Trening na 2023-01 → 2025-06
- Test na 2025-07 → 2026-04 (holdout time-based)
- Metryka: precision@k (top 100 predykcji – ile to faktyczne C-checki w holdout?)
- SHAP plot dla 3 najważniejszych features – do slajdu

### Krok 9: Per-aircraft historical interval (⏳ ~1h)

Funkcja `predict_next_c_check_smart()`:

```
Dla każdego samolotu:
  historical_c_checks = filter(confidence_HIGH gdzie c_check_probability > 0.7)
  
  if len(historical) >= 2:
      mean_interval = mean(diffs)
      predicted = last_check + mean_interval
  elif len(historical) == 1:
      operator_mean = mean(intervals for tego operatora)
      predicted = last_check + operator_mean
  else:
      predicted = last_check + 24_months  # fallback
```

To zastępuje głupie `+24 mies.` w build_dashboard.

### Krok 10: Streamlit dashboard (⏳ ~5-6h)

Nowy plik `app.py`. Trzy strony (sidebar nav):

**Strona 1: Priority List** (główny widok)
- Tabela z kolumnami: Rejestracja | Operator | Wiek | Ostatnie okno | Czas trwania | Typ | Prognoza | Priorytet | Confidence
- Filtry: priorytet, kraj operatora, confidence, operator
- Search: po rejestracji
- Eksport CSV "dla handlowca"
- Kolory priorytetów: TERAZ=czerwony, 6m=żółty, 12m=zielony, Daleko=szary

**Strona 2: Aircraft Timeline** (po kliknięciu rejestracji)
- Plotly Gantt: zielone paski = okresy lotów, czerwone = wykryte C-checki, żółte = storage/AOG
- Metryki na górze: wiek, operator, łączne godziny lotu (proxy), historyczne C-checki
- Confidence próg slider – pokazuje jak zmienia się klasyfikacja

**Strona 3: Sales Alerts**
- Filtrowany widok: priorytet TERAZ + 6 mies, confidence HIGH/MEDIUM
- Sugerowana data pierwszego kontaktu = prognoza_next - 12 mies
- Per-operator grouping
- Email template generator (mailto:) z prefilled wiadomością

**Bonus jeśli czas:**
- Mapa MRO hubów (Plotly mapbox, bubble size = liczba C-checków)
- Heatmap "kiedy zaczynają się C-checki" (miesiące × operator)
- Confidence threshold slider globalny

### Krok 11: Pitch deck + demo (⏳ ~2h)

Slidy (8–10):

1. **Problem** – fragmenty z briefu LOTAMS (godziny ręcznej pracy, late detection)
2. **Insight** – ADS-B gap → check type, z grafiką jak briefu (tabela A/B/C/D)
3. **Architektura** – diagram pipeline (data → ML → dashboard)
4. **Liczby** – 2755 samolotów, X klientów LOTAMS historycznie wykrytych, Y w oknie TERAZ
5. **ML magic** – jak działa klasyfikator + SHAP feature importance
6. **Demo** – live walkthrough Streamlit (priority → timeline → sales alert)
7. **Walidacja** – precision@100 na holdout 2025-07 → 2026-04
8. **Roadmap produkcyjny** – live mode (OpenSky API), API dla CRM, expand na A320/A330
9. **Team & Q&A**

**Demo script** (3 min):
1. Otwórz priority list – pokaż liczbę samolotów TERAZ
2. Pokaż konkretny SP-* (LOT) wpadający w okno – timeline
3. Filtr "tylko HIGH confidence + 6 mies." – pokaż listę dla handlowca
4. Eksport CSV – "tak to wygląda dla działu sprzedaży"
5. Wróć do operator view – "Ryanair: 47 samolotów, X w oknie decyzyjnym, główne MRO: Sofia"

## Stack techniczny

- **Python 3.14** (Windows, lokalnie)
- **Pandas + PyArrow** – data manipulation, parquet
- **LightGBM** – klasyfikator (fallback: sklearn RandomForest jeśli LGBM nie działa na 3.14)
- **Streamlit** – UI
- **Plotly** – wykresy (Gantt, mapy, heatmaps)
- **Dane:** OPDI flight list (EUROCONTROL × OpenSky)

## Pliki w projekcie

```
samolot/
├── data/                          # parquet z OPDI (~10GB)
├── download_opdi.py               # ✅ ściąganie danych
├── inspect_opdi.py                # ✅ walidacja schematu
├── pipeline.py                    # ✅ core pipeline (load + gaps + classify + dashboard)
├── features.py                    # ⏳ feature engineering pod ML
├── train_classifier.py            # ⏳ pseudo-labelling + LGBM training
├── predict.py                     # ⏳ per-aircraft interval + scoring
├── app.py                         # ⏳ Streamlit dashboard
├── requirements.txt               # ✅
├── ROADMAP.md                     # ← ten plik
└── pitch/
    ├── deck.pptx                  # ⏳ slajdy
    └── demo_script.md             # ⏳ skrypt demo
```

## Kluczowe insighty merytoryczne

- **C-check ma interwał ~24 miesiące** – to jest nasz target prediction
- **6–18 miesięcy przed checkiem** = okno decyzyjne handlowca (kupują wcześnie żeby zaplanować slot w MRO)
- **EPWA = LOTAMS** – nasz klient. Inne MRO huby = konkurencja, ale wiedza o ich aktywności też ma wartość
- **Storage zimowy ≠ C-check** – charter (TUI, SunExpress) parkują flotę na zimę. Główny problem do rozwiązania przez ML
- **ADS-B gap nie zawsze = przegląd** – może być AOG, lease return, lub po prostu nie złapane przez sieć

## Decyzje techniczne i uzasadnienia

| Decyzja | Dlaczego |
|---|---|
| OPDI zamiast Zenodo flightlist | Świeże dane (do 04/2026), gotowe pola `registration` i `icao_operator` |
| LightGBM zamiast neural net | Tabular data, ~5K labeled samples, szybki, interpretowalny (SHAP) |
| Pseudo-labelling | Brak ground truth, ale reguły lokalizacja+czas+follow-up dają reasonable proxy |
| Streamlit zamiast React/Flask | 5h demo vs 15h. Hackathon = wybieramy szybkie |
| Strict EU filter (E/L/B) | OPDI ma już bbox Europy, ale dodatkowe zabezpieczenie przed śmieciami |
| Tylko B737 | Brief LOTAMS. Reszta floty = future scope |

## Risk register

- **Python 3.14 + LightGBM** – nowe Python, wheels mogą nie być gotowe. Fallback: sklearn RandomForestClassifier (gorszy ale na tabular wystarczy)
- **Część samolotów w `icao_operator = NaN`** – ~10-15% wpisów. Pokazujemy jako "Unknown" w UI
- **C-checki w nielistowanych MRO** – tracimy część rynku z confidence HIGH. ML powinien to wyłapać jako MEDIUM/LOW z wysokim prawdopodobieństwem
- **Time-based holdout może być za mały** – tylko 10 miesięcy danych "po treningu". Live demo jest ważniejsze niż dokładne metryki
- **Streamlit hosting na demo** – uruchom lokalnie + ngrok jeśli trzeba pokazać publicznie. NIE deployuj na cloud (zmarnowany czas)

## Budżet czasu (od teraz)

| Krok | Czas | Kumulatywnie |
|---|---|---|
| Krok 6 sanity check | 0:30 | 0:30 |
| Krok 7 features | 1:30 | 2:00 |
| Krok 8 ML classifier | 3:00 | 5:00 |
| Krok 9 per-aircraft interval | 1:00 | 6:00 |
| Krok 10 Streamlit | 5:30 | 11:30 |
| Krok 11 pitch + demo | 2:00 | 13:30 |
| Bufor / debugging | 3:00 | 16:30 |
| Sen / przerwy | 3:00 | 19:30 |

Mieścimy się w 24h z ~4h zapasu.

## Kolejność cięć (jeśli czas się ścina)

Jeżeli zostają < 4h do demo i nie wszystko gotowe:

1. **Tnij pierwsze**: bonus widoki (mapa, heatmap), per-operator email templates
2. **Potem**: per-aircraft interval prediction (zostaje `+24 mies.`)
3. **Potem**: SHAP plot (zostaje `feature_importances_` z LGBM)
4. **NIE tnij**: ML classifier (cała wartość ponad reguły), Streamlit z 1 widokiem priority list, pitch script
5. **Last resort**: zostaje notebook + screenshot + slajdy bez live demo

## Co zrobić ZA CHWILĘ

1. Odpalić zaktualizowany `pipeline.py` z dashboard v2
2. Sanity check outputu (zgodnie z krokiem 6 powyżej)
3. Jeśli OK – przechodzimy do Kroku 7 (features.py)
4. Jeśli nie OK – debugujemy razem
