# MRO Prediction Platform

Dashboard dla LOTAMS — wczesne wykrywanie okien C-check na flocie Boeing 737 w Europie na podstawie przerw w aktywności lotniczej (EUROCONTROL OPDI + OpenSky).

## Problem

Handlowiec LOTAMS dowiaduje się o przeglądzie za późno — gdy samolot znika z trasy na 3–6 tygodni, kontrakt jest już u konkurencji (Lufthansa Technik, AFI KLM E&M, Turkish Technic). System wykrywa sygnał **6–18 miesięcy wcześniej** i generuje gotową notatkę sprzedażową.

---

## Szybki start

### 1. Środowisko

```bash
git clone <repo>
cd Samolot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Pipeline danych

```bash
# Pełne dane OPDI 2022-2024 (~30 miesięcy, 6.6M lotów, ok. 10-20 min na pierwszym uruchomieniu)
PYTHONPATH=$PWD python scripts/run_pipeline.py
```

Pipeline pobiera dane automatycznie z EUROCONTROL i cachuje je lokalnie w `data/eurocontrol/cache/`.
Kolejne uruchomienia korzystają z cache — zajmują kilka sekund.

### 3. Dashboard

```bash
PYTHONPATH=$PWD .venv/bin/streamlit run app/main.py
```

Otwórz: [http://localhost:8501](http://localhost:8501)

---

## Docker

```bash
# Zbuduj obraz
docker build -t mro-platform .

# Uruchom dashboard (dane montowane z hosta)
docker compose up app

# Uruchom pipeline w kontenerze (opcjonalnie)
docker compose --profile pipeline run pipeline
```

Dashboard dostępny pod [http://localhost:8501](http://localhost:8501).

> Dane OPDI pobrane lokalnie (`data/`) są montowane przez volume — pipeline nie musi ponownie ściągać plików po każdym starcie kontenera.

---

## Instrukcja użytkowania

### Strona główna

Trzy metryki na górze dają natychmiastowy obraz sytuacji:

- **Samolotów śledzi** — łączna liczba B737 w bazie
- **TERAZ** — samoloty w aktywnym oknie decyzyjnym
- **6 mies.** — samoloty wchodzące w okno w ciągu 6 miesięcy

### Zakładka Fleet Priority

Tabela wszystkich B737 posortowana według priorytetu C-check.

**Filtry:**

| Filtr | Opis |
|-------|------|
| Operator | Filtruj po linii lotniczej |
| Priorytet | TERAZ / 6 mies. / 12 mies. / Daleko |
| Min. confidence | Próg pewności predykcji (zalecane: ≥ 0.5) |
| Tylko historia C-check | Pokaż wyłącznie samoloty z potwierdzoną historią C-check |

**Kolumny tabeli:**

| Kolumna | Opis |
|---------|------|
| Rejestracja | Znak rejestracyjny samolotu |
| Operator | Linia lotnicza |
| Wiek | Wiek samolotu w latach |
| Ostatni check | Typ ostatniej wykrytej przerwy serwisowej |
| Prognoza C-check | Szacowany kwartał następnego C-check |
| Sugerowany kontakt | Sugerowana data pierwszego kontaktu handlowego |
| Priorytet | TERAZ / +6 mies. / +12 mies. / Daleko |
| Confidence | Pewność predykcji: HIGH ≥ 0.70, MEDIUM 0.40–0.69, LOW < 0.40 |

> **LOW confidence:** Samoloty bez historii C-check w danych mają confidence < 0.5 — prognoza szacunkowa. Podnieś próg filtra lub zaznacz "Tylko historia C-check" dla pewniejszych wyników.

Eksport do CSV — przycisk na dole strony.

### Zakładka Aircraft Detail

Szczegółowy widok pojedynczego samolotu.

1. Wybierz rejestrację z listy (domyślnie: najwyższy priorytet z historią C-check).
2. **Oś czasu** — niebieski = tygodnie aktywności lotniczej, kolorowe bloki = wykryte przerwy serwisowe:
   - Czerwony = C-check
   - Fioletowy = D-check
   - Żółty = B-check
   - Szary = A-check / nieznany
3. Panel **Prognoza** — kluczowe metryki: operator, wiek, ostatni check, kwartał C-check, priorytet, sugerowany kontakt, confidence.
4. Tabela **Historia przerw** — wszystkie wykryte zdarzenia z długością, typem i confidence.

### Zakładka Commercial Alerts

Lista alertów sprzedażowych dla samolotów w oknie decyzyjnym.

- Filtry: pasmo priorytetu (TERAZ / 6 mies. / 12 mies.) + min. confidence
- Każdy alert zawiera **gotową notatkę handlową** do skopiowania — kliknij wiersz.
- **Pobierz tygodniowy digest** — plik Markdown z listą alertów do wysłania mailowo/na Slack.
- **Pobierz CSV** — pełna lista do importu do CRM.

---

## Architektura

```
EUROCONTROL OPDI (Parquet)  ──┐
                               ├── merge icao24 ──► gap detection ──► classify ──► predict ──► priority score
OpenSky aircraftDatabase.csv ──┘
```

| Moduł | Plik | Rola |
|-------|------|------|
| Ingest | `src/ingest/opdi.py` | Pobieranie OPDI, filtr B737, cache Parquet |
| Gaps | `src/features/gaps.py` | Wykrywanie przerw ≥ 48h bez lotów |
| Classify | `src/models/classify_check.py` | Klasyfikacja A/B/C/D-check z długości przerwy + MRO boost |
| Predict | `src/models/predict_ccheck.py` | Prognoza daty C-check + okno kontaktu + reforecast |
| Priority | `src/scoring/priority.py` | Scoring TERAZ / 6 mies. / 12 mies. / Daleko |
| Pipeline | `src/pipeline/build.py` | Orkiestracja kroków |
| UI | `app/` | Streamlit: 3 strony |

### Klasyfikacja przerw

| Typ | Długość przerwy | Uwagi |
|-----|----------------|-------|
| A-check | 1–3 dni | Krótka, często na bazie operatora |
| B-check | 4–5 dni | Coraz rzadszy |
| C-check ⭐ | 21–55 dni | Główny produkt LOTAMS |
| D-check | ≥ 60 dni | Raz na ~12 lat |
| unknown | poza zakresami | Wykluczone z predykcji |

### Confidence scoring

Confidence (0–1) odzwierciedla pewność klasyfikacji:

- Bazowy score z podobieństwa długości przerwy do środka zakresu dla danego typu.
- **+0.15** gdy przerwa kończy się lub zaczyna przy strict MRO hub (EPWA, LBSF, LKMT, LROP, LZIB, LIRA, LPPT) — lotniska gdzie C-check jest prawie pewny (brak operacyjnego ruchu regularnego).
- **Reforecast**: jeśli samolot aktywny (lot w ostatnich 180 dniach danych) a prognoza C-check jest > 3 miesiące w przeszłości → data przeliczana jako `last_flight + 12 miesięcy`, confidence cap = 0.40.

---

## Konfiguracja

Wszystkie parametry w [`config.yaml`](config.yaml) — bez dotykania kodu:

```yaml
opdi:
  months:                        # Lista miesięcy YYYYMM do pobrania/cachowania
    - "202201"
    - "202406"                   # Dodaj nowe miesiące tutaj

checks:
  c_check: [21, 55]              # Zakres dni dla C-check
  min_gap_hours: 48              # Minimalna przerwa do analizy

mro_hubs:                        # Lotniska MRO (boost confidence dla C-check)
  - EPWA                         # Warszawa - LOTAMS
  - EDDH                         # Hamburg - Lufthansa Technik

strict_mro_hubs:                 # Nie hub operacyjny — prawie pewny C-check (+0.15)
  - EPWA

ccheck:
  base_interval_months: 27       # Bazowy interwał C-check
  contact_window_start_months: 18  # Okno kontaktu: 18 mies. przed C-check
  contact_window_end_months: 6     # Koniec okna: 6 mies. przed C-check
```

---

## Źródła danych

| Źródło | Rola | Licencja |
|--------|------|----------|
| [EUROCONTROL OPDI](https://www.eurocontrol.int/performance/data/download/OPDI/) | Loty IFR w Europie (Parquet) | Publiczne (Performance Review) |
| [OpenSky aircraftDatabase.csv](https://opensky-network.org/datasets/metadata/) | Metadane B737: operator, typecode, rok budowy | CC BY 4.0 |

---

## Testy

```bash
pytest tests/ -v
```

5 testów jednostkowych pokrywających: klasyfikację przerw, wykrywanie MRO hubów, gap detection, predykcję C-check.

---

## Co zostało do zrobienia

### Krótkoterminowe (1–2 tygodnie po hackathonie)

- [ ] **Aktualizacja danych OPDI** — dodać miesiące `202407` → `202512` do `config.yaml`. Format identyczny, wystarczy rozszerzyć listę `months` i uruchomić pipeline.
- [ ] **Automatyczna aktualizacja miesięczna** — cron job / GitHub Action: `PYTHONPATH=$PWD python scripts/run_pipeline.py` raz w miesiącu po publikacji nowych danych EUROCONTROL.
- [ ] **Uzupełnienie brakujących operatorów** — ~15% samolotów ma `operator = NaN` (brak w OpenSky DB). Lookup table dla top 20 operatorów B737 w Europie (Ryanair, easyJet, Wizz Air, LOT, etc.).
- [ ] **Per-aircraft interwał C-check** — zamiast stałego 27 miesięcy dla wszystkich, wyliczyć rzeczywisty interwał z historii każdego samolotu (dotyczy ~343 samolotów z HIGH confidence).

### Średnioterminowe (1–3 miesiące)

- [ ] **ML classifier (LightGBM)** — zastąpić regułowe progi klasyfikatorem trenowanym na labeled gaps. Szkic w `Samolot-Maciek/pipeline.py`. Retro-walidacja na 2022→2023 daje 85.6% recall — weryfikacja na 2023→2024.
- [ ] **Filtr 737 MAX vs. NG** — rozróżnić 737 MAX (B38M/B39M) od NG (B737/B738/B739). Różne interwały C-check i różna wartość handlowa dla LOTAMS.
- [ ] **Alerty push** — gdy samolot wejdzie w pasmo TERAZ: webhook Slack lub e-mail przez SendGrid. FastAPI endpoint jako backend.
- [ ] **Historia ręczna** — formularz w UI do wpisania potwierdzonego C-check z dokumentacji (override dla jednego samolotu, zapis do lokalnego JSON).

### Długoterminowe (roadmapa)

- [ ] **React + Django** — migracja frontendu z Streamlit: pełna aplikacja webowa z auth, rolami (handlowiec / manager) i REST API. Uzgodniono jako next step po hackathonie.
- [ ] **CRM integration** — eksport alertów bezpośrednio do Salesforce / HubSpot przez API.
- [ ] **Rozszerzenie na inne typy** — Airbus A320, Boeing 787 — analogiczna metodologia, inne progi C-check.
- [ ] **Confidence v2** — dodać `icao_operator` z OPDI + historię lotnisk serwisowych per operator jako cechy do scoringu.

---

## Disclaimer

Klasyfikacja opiera się na **przerwach w danych lotniczych ADS-B/OPDI** — sygnał pośredni, nie dokumentacja MRO. Prognoza nie zastępuje kontaktu z operatorem ani dokumentacji technicznej samolotu.
