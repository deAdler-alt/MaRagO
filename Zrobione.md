# MRO Prediction Platform — Handoff

**Klient:** LOTAMS (Warszawa) · **Scope:** B737 w geograficznej Europie · **Deadline:** koniec hackathonu

Wszystko co musisz wiedzieć żeby przejąć projekt. Czytaj od góry, sekcje "Co dalej" + "Jak uruchomić" są najważniejsze.

---

## Stan na teraz (TL;DR)

✅ **Zrobione (kroki 1–10 z roadmapy):**
- Pipeline ETL + detekcja gapów + klasyfikacja regułowa
- Dashboard v2 z confidence levels (HIGH/MEDIUM/LOW)
- Geograficzny filtr Europy (32 prefiksy ICAO, bez Izraela/Rosji/Bliskiego Wsch.)
- Feature engineering (48 kolumn, 16 nowych features pod ML)
- **LightGBM classifier — AUC 0.975 na holdout** (fix leakage reguły 3) ✨
- **Per-aircraft historical interval** (`predict.py`) — avg 507 dni zamiast głupiego +24 mies.
- **Streamlit dashboard** (`app/`) — 3 widoki z CSS, kolorową tabelą, timeline, alertami sprzedażowymi

⏳ **Co dalej (krok 11):**
- Pitch deck + demo script

**Budżet czasu pozostały:** ~2h (pitch + demo script)

---

## Liczby (najświeższe wyniki)

Po przefiltrowaniu do geograficznej Europy + treningu ML:

| Metryka | Wartość |
|---|---|
| Lotów B737 w EU | 7,085,279 |
| Unikalnych samolotów | 2,761 |
| Kandydatów C-check (gap 14–60d, ades w EU) | 3,651 |
| Pseudo-labele: pozytywne (HIGH+MEDIUM) | 974 |
| Pseudo-labele: negatywne (LOW + reguły 1-3) | 674 (+111 z reguły 3) |
| Pseudo-labele: unlabeled (do predykcji) | 2,003 |
| **Test AUC (holdout 2025-07 → 2026-04)** | **0.975** (realniejszy po fix leakage) |
| **Precision@100 na holdout** | **1.000** (100/100) |
| **Precision@200 na holdout** | **0.950** (190/200) |
| Per-aircraft interwał (avg) | 507 dni (16.6 mies.) |
| Samolotów z per-aircraft historią | 456 |
| Operatorów z interwałem | 65 |
| Samolotów w dashboardzie | 1,684 |
| Klienci LOTAMS w EPWA (historycznie) | 37 |

**ML działa.** Top 20 LOW kandydatów z najwyższą c_check_probability to realne C-checki w LTBA/LTAI/EGBB/EHAM których reguły nie złapały (głównie Turkish, SunExpress, JAF/TUI, KLM). Dokładnie ta wartość ponad reguły o której roadmap mówiła w kroku 8.

---

## Architektura

```
data/*.parquet (OPDI, 40 plików, 2023-01 → 2026-04, ~1.6 GB)
        ↓
  pipeline.load_b737_eu()          ← filtr B737 + geograficzna EU
        ↓
  pipeline.detect_gaps()           ← gapy między lotami per icao24
        ↓
  pipeline.classify_check()        ← reguły A/B/C/D wg długości
        ↓
  features.get_c_check_candidates()  ← C-check w EU + confidence (HIGH/MED/LOW)
        ↓
  features.build_features()        ← 16 nowych features (gap, aircraft, pre/post, operator, historical)
        ↓
  train_classifier.assign_pseudo_labels()  ← pozytywy HIGH+MED, negatywy LOW+heurystyki
        ↓
  train_classifier.train_lgbm()    ← LightGBM binary, time-based holdout
        ↓
  predictions.csv (3651 × c_check_probability ∈ [0, 1])
        ↓
  [TODO Krok 9] per-aircraft interval predykcja next C-check
        ↓
  [TODO Krok 10] Streamlit dashboard
        ↓
  [TODO Krok 11] Pitch
```

---

## Pliki w projekcie

| Plik | Co robi | Status |
|---|---|---|
| `download_opdi.py` | Pobiera 40 plików parquet z eurocontrol.int | ✅ |
| `inspect_opdi.py` | Walidacja schematu pierwszego pliku | ✅ |
| `pipeline.py` | Core ETL: load → detect_gaps → classify_check → build_dashboard | ✅ |
| `features.py` | Feature engineering — 16 nowych kolumn pod ML | ✅ |
| `train_classifier.py` | LightGBM binary classifier + predykcja prob | ✅ |
| `predict.py` | Per-aircraft historical interval → predictions_with_interval.csv | ✅ |
| `app/main.py` | Streamlit home — KPI karty + problem statement | ✅ |
| `app/pages/01_fleet.py` | Fleet Priority — kolorowa tabela z filtrami | ✅ |
| `app/pages/02_aircraft.py` | Aircraft Detail — timeline C-checków + historia | ✅ |
| `app/pages/03_alerts.py` | Commercial Alerts — per-operator + szablony e-mail | ✅ |
| `pitch/deck.pptx` | Slajdy | ⏳ TODO (krok 11) |
| `requirements.txt` | pandas, pyarrow, requests, streamlit, plotly, sklearn, lightgbm | ✅ |
| `ROADMAP.md` | Pełny plan kroków 1–11 ze szczegółami | ✅ (źródło prawdy) |
| `HANDOFF.md` | Ten plik | ✅ |

---

## Output (regenerowany przy każdym uruchomieniu)

Wszystkie pliki w `output/` są nadpisywane przy każdym `python pipeline.py` / `features.py` / `train_classifier.py`:

| Plik | Z którego skryptu | Zawartość |
|---|---|---|
| `pipeline_log.txt` | pipeline.py | Cały output terminala (Tee) |
| `dashboard.csv` | pipeline.py | 1684 samolotów × kolumny dashboardu |
| `lotams_clients.csv` | pipeline.py | 37 klientów LOTAMS |
| `top_priority_now.csv` | pipeline.py | Samoloty w oknie decyzyjnym (TERAZ + 6m + 12m) |
| `features_log.txt` | features.py | Coverage + sanity check by confidence |
| `features.csv` | features.py | 3651 kandydatów × 48 kolumn |
| `classifier_log.txt` | train_classifier.py | AUC, precision@k, feature importance, top 20 LOW |
| `predictions.csv` | train_classifier.py | **3651 × c_check_probability** (główny output ML) |
| `feature_importance.csv` | train_classifier.py | Ranking 17 features po gain |

---

## Jak uruchomić od zera

```powershell
# 1. Instalacja
pip install -r requirements.txt

# 2. Pobranie danych (jednorazowo, ~1.6GB, w tle)
python download_opdi.py

# 3. Sanity check schematu
python inspect_opdi.py

# 4. Pipeline + dashboard (1-2 min)
python pipeline.py

# 5. Feature engineering (1-2 min)
python features.py

# 6. ML classifier (2-3 min)
python train_classifier.py
```

Każdy z punktów 4–6 jest niezależny ale każdy wymaga `data/` z parquetami. `train_classifier.py` woła `load_b737_eu` + `build_features` wewnętrznie, więc działa bez wcześniejszych runów.

Wszystkie skrypty mają `_Tee` (duplikacja stdout do terminal + plik). Output w `output/`.

---

## Decyzje techniczne — zostaw jak jest

Te decyzje są przemyślane i przegadane. **Nie zmieniaj bez bardzo dobrego powodu**:

### Filtr geograficznej Europy (`EUROPE_AIRPORT_PREFIXES` w `pipeline.py`)

**32 prefiksy IN:** EB ED EE EF EG EH EI EK EL EN EP ES EV EY (Europa Płn./Skandynawia/Bałtyki) + LA LB LC LD LE LF LG LH LI LJ LK LM LO LP LQ LR LS LT LU LW LY LZ (Europa Płd./Środkowa/Bałkany/Turcja) + BI BK (Islandia/Kosowo) + UK (Ukraina) + DA DT GM HE HL (Afryka Płn.)

**Świadomie OUT:** Izrael (LL), Syria (OS), Liban (OL), Armenia (UD), Gruzja (UG), Azerbejdżan (UB), Rosja (UU/UL/etc), Białoruś (UM), Bliski Wschód (O*), Sub-Saharan Africa.

Zakres ustalony z mentorem hackathonu: "~2-3 tys. km od Warszawy + Skandynawia + Afryka Płn. + Turcja, bez sankcji, bez kontrowersyjnych".

Filtr stosowany w dwóch miejscach:
1. **Load** (`load_b737_eu`) — OR: przynajmniej jeden koniec w EU. Nie zmieniaj na AND — utworzy sztuczne gapy dla operatorów EU-NA (Turkish, Royal Air Maroc itd.).
2. **C-check candidates** (`get_c_check_candidates`) — `ades` MUSI być w EU. Dashboard pokazuje tylko gapy gdzie MRO odbywa się w Europie.

### Confidence levels (`pipeline.MRO_HUBS` i `STRICT_MRO_HUBS`)

**STRICT (11 dedykowanych MRO, samo wylądowanie + gap 14-60d = HIGH):**
EPWA, LBSF, LKMT, LROP, LZIB, LIRA, LPPT, EGPK, EDLP, EGSH, EGDX

**MRO_HUBS dodatkowe (10 hubów operacyjnych z MRO, MEDIUM gdy stayed_put):**
EDDH, EDDM, EIDW, LTBA, LTFM, LTFJ, LFLL, EHAM, LSGG, LGAV, LKPR, EDDN, EINN, LHBP, LFSB

Lista przeszła 2 rundy iteracji — ostateczna wersja. Świadomie pominięte: EGCC Manchester, EDDF Frankfurt, LFPG CDG, EGKK Gatwick (zbyt operacyjne, ryzyko fałszywych pozytywów ze storage zimowego TUI/SunExpress).

### Smart picker (build_dashboard)

Per samolot wybieramy najnowszy gap preferując HIGH > MEDIUM > LOW. Czyli jeśli samolot miał HIGH check w EPWA 2024-05 i potem LOW gap w 2025-08, bierzemy ten HIGH (LOW to pewnie storage/AOG). Implementacja: sort po (`_conf_rank`, `last_seen`) ascending, tail(1) per icao24.

### Features wyłączone z ML (leakage)

`at_strict_mro_hub`, `at_any_mro_hub`, `stayed_put`, `confidence` — to bezpośrednie komponenty reguły confidence. Włączenie → model wyuczy się reguły zamiast prawdziwych wzorców. Wszystkie inne features (17) są bezpieczne.

### Engine ML

LightGBM jako default, sklearn `HistGradientBoostingClassifier` jako fallback (oba obsługują NaN natywnie). Auto-detect przy starcie `train_classifier.py`. **Na Python 3.14 LightGBM działa** — sprawdzone.

---

## Co dalej (priorytetyzowane)

### Krok 9 — Per-aircraft historical interval (`predict.py`, ~1h)

Aktualnie w `pipeline.build_dashboard` predykcja next C-check = `ostatni_c_check + 24 miesiące` (głupie). Cel: użyć **realnego interwału tego samolotu/operatora**.

Wzór (z `features.mean_interval_prev_c_checks`):

```python
def predict_next_c_check_smart(candidates, c_check_probability_threshold=0.7):
    """Inteligentna predykcja next C-check per samolot."""
    # Filtruj do prawdziwych C-checków (po ML)
    real = candidates[candidates['c_check_probability'] > c_check_probability_threshold]
    
    for icao24 in real['icao24'].unique():
        history = real[real['icao24'] == icao24].sort_values('last_seen')
        if len(history) >= 2:
            # Mean interval z historii TEGO samolotu
            intervals = history['last_seen'].diff().dt.days.dropna()
            mean_interval = intervals.mean()
        elif operator_known:
            # Fallback: mean interval dla tego operatora
            mean_interval = operator_mean_interval[operator]
        else:
            mean_interval = 730  # 24 miesiące fallback
        
        predicted_next = history.iloc[-1]['last_seen'] + pd.Timedelta(days=mean_interval)
```

`features.mean_interval_prev_c_checks` już to liczy expanding window per samolot. Wykorzystaj.

Output: `output/predictions_with_interval.csv` z kolumną `predicted_next_smart`.

### Krok 10 — Streamlit dashboard (`app.py`, ~5-6h, **najważniejsze**)

To gdzie produkt naprawdę się pokazuje. 3 widoki w sidebar nav:

**Strona 1: Priority List** (główny widok dla handlowca)
- Tabela z `top_priority_now.csv`: Rejestracja | Operator | Wiek | Ostatnie okno | Czas trwania | Typ | Prognoza | Priorytet | Confidence | **c_check_probability**
- Filtry: priorytet, kraj operatora, confidence threshold, operator
- Search po rejestracji
- Eksport CSV "dla handlowca"
- Kolory priorytetów: TERAZ=czerwony, 6m=żółty, 12m=zielony, Daleko=szary

**Strona 2: Aircraft Timeline** (po kliknięciu rejestracji)
- Plotly Gantt: zielone paski = okresy lotów, czerwone = wykryte C-checki, żółte = storage/AOG
- Metryki na górze: wiek, operator, łączne godziny lotu (proxy), historyczne C-checki
- Confidence threshold slider — pokazuje jak zmienia się klasyfikacja

**Strona 3: Sales Alerts**
- Filtrowany widok: priorytet TERAZ + 6 mies, confidence HIGH/MEDIUM OR c_check_probability > 0.7
- Sugerowana data pierwszego kontaktu = prognoza_next - 12 mies
- Per-operator grouping
- Email template generator (`mailto:`) z prefilled wiadomością

**Źródło danych:** `output/predictions.csv` (3651 wpisów) + `output/dashboard.csv` (1684 samolotów).

**Dodatki które dają punkt u Jury:**
- Mapa MRO hubów (Plotly mapbox)
- Heatmap "kiedy zaczynają się C-checki" (miesiące × operator)
- SHAP plot top features

### Krok 11 — Pitch deck + demo (`pitch/`, ~2h)

Slajdy (8–10), demo script 4 min. Szczegóły w `ROADMAP.md` sekcja "Krok 11".

**Kluczowe liczby dla pitchu (już mamy):**
- 2,761 samolotów B737 w EU
- 974 historycznych C-checków wykrytych regułami
- **AUC 0.983**, **Precision@100 = 1.0** na holdout
- 37 klientów LOTAMS historycznie
- Top 3 features: `gap_days`, `ades_country`, `flights_per_day_pre_gap`

---

## Gotchas / pułapki

1. **Python 3.14 na Windows** — większość paczek działa, ale `lightgbm` wymaga wheelsów. Jak nie pójdzie, `train_classifier.py` ma fallback na sklearn HistGradientBoosting.

2. **`icao_operator = NaN` w ~42% wpisów** — OPDI ma luki. Operator features (`operator_fleet_size`, `operator_typical_mro`) mają coverage ~57%. ML to wyłapie (NaN to też sygnał).

3. **`stayed_put` ma 57% trafień w STRICT MRO** — OPDI gubi ~43% loty ferry po C-check'u. To wbudowane w design: HIGH = sam strict MRO (bez stayed_put), MEDIUM = MRO + stayed_put.

4. **`same_operator_after` zawsze = 1.0** — OPDI bierze operator ze static aircraft DB, nie z konkretnego lotu. Feature ma niską importance gain (31), praktycznie nieinformatywna. Nie usuwaj — to jest "missing data signal".

5. **`predictions.csv` ma c_check_probability dla WSZYSTKICH 3651 kandydatów** włącznie z labelled samples. Dla Streamlit dashboardu używaj tej kolumny do sortowania/filtrowania zamiast surowego `confidence`.

6. **NOW = `2026-05-22`** zakodowane w `build_dashboard`. Zmień jak będziesz testować inną datę.

7. **Folder `output/` jest w `.gitignore`** — nie commituj, regeneruje się przy każdym runie.

8. **`data/` ~1.6 GB** — nie commituj. `download_opdi.py` pobiera z eurocontrol.int.

9. **OPDI ma dane do 2026-04 włącznie** — przy update danych może być inny zakres.

10. **Reforecast w `build_dashboard`** — dla aktywnych samolotów z zaległą predykcją (`mies_do_next < -3`) ustawiamy `predicted_next = last_flight + 12 mies`. Założenie: miały C-check którego nie złapaliśmy. Zostaje w kolumnie `reforecasted=True`.

---

## Lista lotnisk-kandydatów do dalszego rozszerzenia (jak czas)

Z top 15 lotnisk gapów C-check, kandydaci do `MRO_HUBS` (lub nawet STRICT) których jeszcze nie dodaliśmy:

| ICAO | Lotnisko | Gapy | Komentarz |
|---|---|---|---|
| HEAZ | Cairo Almaza | 76 | Egipska baza wojskowa + EgyptAir MRO (?) — niepewne |
| LTFE | Bodrum-Milas | 74 | Sezonowe pasażerskie, raczej storage |
| LTAI | Antalya | 74 | Pegasus hub, ryzyko fałszywych pozytywów |
| LFPO | Paris Orly | 67 | AF maintenance, ale duży hub |
| EBBR | Brussels | 61 | Brussels Airlines hub, mieszane |

Świadomie zostawione na boku — ML i tak je obsługuje (top 20 LOW pokazuje że TC- LTAI/LTBA wpadają jako prob=1.0).

---

## Kontekst biznesowy (przypomnienie)

- **Klient:** LOTAMS, Warszawa — operator MRO, robi głównie B737 (LOT, TUI, charter)
- **EPWA = LOTAMS** w `MRO_HUBS`
- **6–18 miesięcy przed C-check'iem** = okno decyzyjne handlowca (kupują wcześnie żeby zaplanować slot w MRO)
- **C-check ~24 mies. interwał** — target prediction
- **Wartość biznesowa:** zamiast godzin tygodniowo per handlowiec ręcznie przeszukiwać portale, system codziennie wskazuje top samolotów do kontaktu

---

## Risk register (z roadmapy)

- **Python 3.14 + LightGBM** — działa, sprawdzone. ✅
- **`icao_operator = NaN`** — ~42% wpisów. Pokazujemy jako "Unknown" w UI. ML akceptuje NaN.
- **C-checki w nielistowanych MRO** — ML łapie je w LOW z wysoką prob (top 20 to potwierdza).
- **Time-based holdout** — tylko 10 miesięcy "po treningu". AUC 0.983 sugeruje że jest OK.
- **Streamlit hosting** — uruchom lokalnie + ngrok jeśli trzeba pokazać publicznie. NIE deployuj na cloud.

---

## Kolejność cięć jeśli czas się ścina

1. **Pierwsze**: bonus widoki Streamlit (mapa, heatmap), per-operator email templates
2. **Potem**: per-aircraft interval prediction (krok 9 — zostaje `+24 mies.` fallback)
3. **Potem**: SHAP plot (zostaje `feature_importance.csv` z LGBM gain)
4. **NIE tnij**: Streamlit z 1 widokiem priority list, pitch script
5. **Last resort**: zostaje notebook + screenshoty + slajdy bez live demo

---

## Najszybszy onboarding (5 min)

1. Otwórz `ROADMAP.md` — szczegółowy plan kroków
2. Otwórz `output/classifier_log.txt` — zobacz aktualne metryki ML
3. Otwórz `output/predictions.csv` w Excelu — popatrz na strukturę głównego outputu
4. Otwórz `output/top_priority_now.csv` — to widzi handlowiec
5. Otwórz `pipeline.py` — sekcja `EUROPE_AIRPORT_PREFIXES`, `MRO_HUBS`, `STRICT_MRO_HUBS`, `build_dashboard`
6. Otwórz `train_classifier.py` — `assign_pseudo_labels`, `FEATURE_COLS`, `train_lgbm`

Ze wszystkimi pytaniami → Maciek.
