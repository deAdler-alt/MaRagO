# PITCH DECK — MRO Intelligence Platform
## Instrukcja dla generatora prezentacji (Gamma.app / PowerPoint / Canva AI)

> **Uwaga do LLM-generatora:** Każdy slajd zawiera kompletną specyfikację layoutu, tekstu i elementów wizualnych.
> Nie zmieniaj liczb — są zweryfikowane z logów systemu. Zachowaj dark theme na wszystkich slajdach.
> Język: polski (z angielskimi terminami technicznymi). Ton: pewny, konkretny, oparty na danych.

---

## PARAMETRY GLOBALNE

```
Kolorystyka:
  Tło główne:    #0f172a (bardzo ciemny granat)
  Tło kart:      #1e293b (ciemny granat)
  Bordering:     #334155 (stalowy)
  Tekst główny:  #f1f5f9 (biały złamany)
  Tekst subtext: #94a3b8 (szary)
  Akcent RED:    #ef4444 (pilność / C-check teraz)
  Akcent AMBER:  #f59e0b (6 mies. / uwaga)
  Akcent BLUE:   #3b82f6 (dane / info)
  Akcent GREEN:  #22c55e (model / ok)
  Akcent VIOLET: #8b5cf6 (ML / innowacja)

Font:
  Tytuł slajdu:  Inter Bold 40–48px lub Poppins SemiBold
  Body:          Inter Regular 18–22px
  Subtext/label: Inter 13–15px, kolor #94a3b8
  Liczby KPI:    Inter ExtraBold 52–64px

Wymiary: 16:9, 1920×1080px lub ekwiwalent

Logo: ✈️ + "MRO Intelligence" — lewy górny róg każdego slajdu (12px, kolor #475569)
Numer slajdu: prawy dolny róg (mały, #334155)
```

---

## SLAJD 1 — PROBLEM

**Tytuł:** `2 000+ samolotów B737 w Europie.`
**Podtytuł:** `Który potrzebuje serwisu jako następny?`

**Layout:** Pełne ciemne tło `#0f172a`. Tytuł wycentrowany u góry (font biały, duży). Trzy karty pain-points w rzędzie poniżej (każda `#1e293b`, border-left `#ef4444`). Prawa kolumna: ikona samolotu ✈️ z wielkim `?` nakładanym na sylwetkę, kolor `#ef4444`.

**Trzy karty pain-points (lewa 2/3 szerokości):**

| Ikona | Nagłówek | Treść |
|---|---|---|
| ⏱️ | Godziny ręcznej pracy | Handlowiec przeszukuje FlightRadar, LinkedIn, portale branżowe — 3–5 godz./tydzień. Bez systemu. |
| 🔕 | Spóźniona reakcja | Gdy samolot znika z trasy → jest już u konkurencji w Hamburgu lub Stambule. LOTAMS dowiaduje się za późno. |
| 📝 | Oferty z powietrza | Każda wycena MRO = ręczne zebranie danych flotowych, historii przeglądów, kalkulacji zakresu. Godziny. |

**Footer microtext** (dół slajdu, `#475569`, 13px):
`LOTAMS — Lot Aircraft Maintenance Services · Warszawa Okęcie (EPWA) · EASA Part-145`

**Wskazówka dla generatora:** Tło powinno mieć subtelny gradient od `#0f172a` do `#0d1526`. Karty rzucają cień. NIE używaj białego tła.

---

## SLAJD 2 — INSIGHT: SYGNAŁ W DANYCH

**Tytuł:** `Samolot mówi kiedy idzie na serwis`
**Podtytuł:** `— przez ślad ADS-B`

**Layout:** 60% lewa — tabela. 40% prawa — timeline wizualizacja.

**Tabela (dark, lewa kolumna — pełna specyfikacja):**

```
Nagłówki kolumn: Typ | Częstotliwość | Przerwa ADS-B | Wartość dla LOTAMS

WIERSZ 1: A-check | co 500-600h | 1-3 dni | ✗ LOTAMS nie wykonuje
          Kolor: #1e293b, tekst #64748b (szary — brak zainteresowania)

WIERSZ 2: B-check | co 4-8 mies. | 4-5 dni | ⚠ Rzadki, linie go pomijają
          Kolor: #1e293b, tekst #94a3b8

WIERSZ 3: C-check ★ | co 2-3 lata | 3-6 TYGODNI | ★ GŁÓWNY PRODUKT LOTAMS
          Kolor: #1e3a8a (ciemny niebieski), border #3b82f6 GRUBA, tekst biały
          Bold: "Tu są pieniądze. Tu jest kontrakt."

WIERSZ 4: D-check | co 12 lat | 1-3 miesiące | Rzadki, złomowanie
          Kolor: #1e293b, tekst #64748b
```

**Prawa kolumna — timeline samolotu:**
Prosta pozioma oś czasu z kolorowymi blokami:
```
[■■■■■ loty ■■■■■] [□□□□ C-check w MRO □□□□] [■■■■■ loty ■■■■■]
  niebieski-green          czerwony blok             niebieski-green
                    ↑
           "3-6 tygodni — sygnał ADS-B"
           "lokalizacja: Warszawa, Hamburg, Stambuł"
```

**Callout box** (prawa strona, kolor `#7f1d1d`, border `#ef4444`):
```
🎯 Cel systemu
Wykryć ten blok 12–18 miesięcy
PRZED jego nastąpieniem.
Okno decyzyjne handlowca.
```

---

## SLAJD 3 — ARCHITEKTURA

**Tytuł:** `Pipeline: 7 milionów lotów → sygnał → predykcja`

**Layout:** Ciemne tło. Centralny element: poziomy diagram flow z 4 krokami. Subtitle pod diagramem. KPI strip na dole.

**Diagram flow (4 bloki, strzałki między):**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  📡 DANE        │ →  │  🔍 GAP          │ →  │  🤖 LightGBM   │ →  │  📊 DASHBOARD   │
│                 │    │  DETECTION       │    │  CLASSIFIER    │    │                  │
│ EUROCONTROL     │    │                  │    │                │    │  Streamlit       │
│ OPDI            │    │  14–60 dni       │    │  48 features   │    │  4 widoki        │
│                 │    │  przerwy         │    │  AUC = 0.975   │    │  Fleet/Timeline  │
│ 40 parquetów    │    │  +lokalizacja    │    │  P@100 = 100%  │    │  Alerts/Insights │
│ 2023→2026       │    │  MRO_HUBS        │    │                │    │                  │
│ B737 EU only    │    │  HIGH/MED/LOW    │    │                │    │                  │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
  Kolor: #1e3a8a         Kolor: #78350f          Kolor: #4c1d95         Kolor: #14532d
  Border: #3b82f6        Border: #f59e0b          Border: #8b5cf6        Border: #22c55e
```

**KPI strip pod diagramem (5 mini-liczb w rzędzie):**
```
7 085 279 lotów   |   2 761 samolotów   |   40 parquetów   |   48 ML features   |   batch < 15 min
```
*(kolor `#64748b`, font mały, separator `|` w `#334155`)*

**Microtext footer:**
`Dane: EUROCONTROL OPDI (nie OpenSky — lepszy coverage EU, pełne loty bez rate-limitów)`

**Wskazówka dla generatora:** Bloki powinny mieć zaokrąglone rogi (border-radius 8px), subtelny glow na border. Strzałki: jasne, animowane jeśli możliwe (pptx: motion path).

---

## SLAJD 4 — LICZBY

**Tytuł:** `Co znaleźliśmy w danych`

**Layout:** Ciemne tło. 5 dużych kart KPI (2 rzędy: 3 na górze + 2 na dole, wycentrowane). Każda karta: wielka liczba, label, subtext.

**Karty KPI (specyfikacja każdej):**

```
KARTA 1 (górny rząd, lewa):
  Liczba: 2 761
  Label: Samolotów B737 w Europie
  Sub: aktywnie monitorowanych
  Bg: #1e293b | Border-top: #3b82f6

KARTA 2 (górny rząd, środek):
  Liczba: 434
  Label: 🔴 KONTAKT TERAZ
  Sub: 119 zaległych + 315 w oknie 0–6 mies.
  Bg: #7f1d1d | Border-top: #ef4444
  Tekst: #fef2f2

KARTA 3 (górny rząd, prawa):
  Liczba: 617
  Label: 🟡 KONTAKT W 6 MIES.
  Sub: Wchodzą w okno — czas na outreach
  Bg: #78350f | Border-top: #f59e0b
  Tekst: #fef3c7

KARTA 4 (dolny rząd, lewa):
  Liczba: 37
  Label: ⭐ Klienci LOTAMS
  Sub: Historyczne gappy w EPWA wykryte automatycznie
  Bg: #1e3a8a | Border-top: #60a5fa
  Tekst: #eff6ff

KARTA 5 (dolny rząd, prawa):
  Liczba: 507 dni
  Label: Średni interwał C-check
  Sub: Z danych 456 samolotów (per-aircraft)
  Bg: #1e293b | Border-top: #8b5cf6
  Tekst: #f1f5f9
```

**Subtext pod kartami (wycentrowany, `#475569`, 14px):**
`Dane: EUROCONTROL OPDI 2023-01 → 2026-04 · Tylko aktywne B737 · Europa (ICAO EU + TR + EG + MA)`

---

## SLAJD 5 — ML MAGIC

**Tytuł:** `LightGBM — jak model wykrywa C-check`

**Layout:** Lewa 45%: metryki w ciemnych kartach. Prawa 55%: feature importance horizontal bar chart.

**Lewa strona — metryki (4 karty pionowo):**

```
METRYKA 1: AUC = 0.975
  Sub: Time-based holdout (test ≥ 2025-07-01)
  Kolor: #4c1d95 | border #8b5cf6

METRYKA 2: Precision@100 = 100%
  Sub: Pierwsze 100 predykcji — zero błędów
  Kolor: #14532d | border #22c55e

METRYKA 3: Precision@200 = 95%
  Sub: 190 z 200 top predykcji prawidłowych
  Kolor: #14532d | border #4ade80

METRYKA 4: 974 C-checków w treningu
  Sub: Pseudo-labels: HIGH+MEDIUM confidence
  Kolor: #1e293b | border #3b82f6
```

**Prawa strona — Feature Importance (horizontal bar chart, dark theme):**

```
Bar chart — top 7 features (od największego do najmniejszego):

gap_days                    ████████████████████████ 3475
ades_country                ███████████████████████  3097
flights_per_day_pre_gap     ████████                 1011
avg_flight_duration_hours   ██████                    745
same_country_after          █████                     663
distinct_airports_pre_gap   ████                      575
operator_fleet_size         ████                      514

Kolory barów: gradient od #8b5cf6 (pierwsze) do #3b82f6 (ostatnie)
Tło: #1e293b
Oś X: #94a3b8
Tytuł wykresu: "Feature Importance (gain)" #94a3b8 14px
```

**Callout (pod wykresem, prawa):**
```
💡 "Gap w Ankarze + samolot latał 3.5 lotu/dzień przed przerwą
    + ta sama flaga po przerwie = prawdopodobnie C-check"
```
*(kolor `#1e3a8a`, border `#3b82f6`, font italic, 14px)*

---

## SLAJD 6 — DEMO

**Tytuł:** `Demo — Live System`

**Layout:** Pełnoekranowy zrzut Fleet Priority page (dark Streamlit theme). Nad nim semi-transparent overlay z tekstem. Alternatywnie: podział 50/50 — lewa: screenshot, prawa: lista co zobaczymy.

**Overlay/header tekst:**
`"Fleet Priority — 1 684 samolotów B737, posortowanych wg okna C-check"`

**Lista demo kroków (prawa strona, jeśli split layout):**
```
01  Fleet Priority — lista czerwona/żółta/niebieska
    Slider ML probability, filtr kraj, export CSV

02  Aircraft Timeline — Gantt samolotu
    Zielone = loty, niebieskie = C-check, żółte = storage/AOG
    Historia 3 lat w jednym widoku

03  Commercial Alerts → Szablony
    Generuj ofertę e-mail dla SP-LVD (LOT)
    mailto: link → klient pocztowy gotowy
```

**Nota dla generatora:**
Wstaw placeholder: `[SCREENSHOT FLEET PRIORITY]` — zamień na prawdziwy screenshot przed prezentacją.
Tło: `#0f172a`. Tekst "01 / 02 / 03" w kółkach kolor `#ef4444`.

---

## SLAJD 7 — WALIDACJA

**Tytuł:** `Jak to walidowaliśmy — rzetelnie`

**Layout:** Dwa bloki obok siebie. Lewa: timeline walidacji. Prawa: confusion matrix + precision@k.

**Lewa — timeline walidacji:**
```
Oś czasu pionowa:

2023-01  ●──────────────────────── TRENING ──────────────────────────●  2025-06-30
                     [7 085 279 lotów · 736 pos + 465 neg labeled]

2025-07  ●──── TEST (HOLDOUT) ────●  2026-04
              [447 labeled · nigdy nie widziany w treningu]
              AUC = 0.975
              P@100 = 100%
              P@200 = 95%
```
*(linia trening kolor `#3b82f6`, linia test kolor `#ef4444`)*

**Prawa — Confusion Matrix + precision:**
```
CONFUSION MATRIX (test holdout):
┌──────────────┬──────────────┐
│ TN = 186     │ FP = 23      │  ← fałszywe alarmy
├──────────────┼──────────────┤
│ FN = 10      │ TP = 228     │  ← znalezione C-checki
└──────────────┴──────────────┘
Precision = 90.8% | Recall = 95.8%
```

**Callout bottom:**
`⭐ 37 historycznych klientów LOTAMS — wszystkie wykryte automatycznie z EPWA gap`

---

## SLAJD 8 — ROADMAP

**Tytuł:** `Co dalej — droga na produkcję`

**Layout:** 3 kolumny (fazy czasowe). Każda kolumna: nagłówek fazy + lista punktów.

**Kolumna 1 — "TERAZ (hackathon)"** *(kolor `#22c55e`)*
```
✅ Batch pipeline EUROCONTROL OPDI
✅ LightGBM AUC 0.975
✅ Dashboard 4 widoki (Streamlit)
✅ Per-aircraft interval hierarchy
✅ Email templates + mailto: link
✅ Mapa MRO Europe (40 airports)
```

**Kolumna 2 — "NASTĘPNY SPRINT"** *(kolor `#f59e0b`)*
```
🔄 Live mode: OpenSky Network API
   (drop-in replacement, ten sam kod)
🔄 Codziennie odświeżane predykcje
🔄 REST API dla CRM / Salesforce
🔄 Push notification "nowy TERAZ"
```

**Kolumna 3 — "SKALA"** *(kolor `#8b5cf6`)*
```
🚀 Rozszerzenie: A320 / A330
🚀 Więcej operatorów (Middle East, Africa)
🚀 Integration z AMOS/OASES MRO system
🚀 LLM-generowane oferty sprzedażowe
```

**Footer:**
`Stack: Python · pandas · LightGBM · Streamlit · Plotly · EUROCONTROL OPDI`

---

## SLAJD 9 — TEAM & Q&A

**Tytuł:** `Zespół`

**Layout:** Karty team memberów (2–4 osoby, zależnie od liczby w teamie). Każda: avatar (okrąg), imię, rola. Pod nimi: duże Q&A.

**Karty teamowe (placeholder — wypełnij przed prezentacją):**
```
[IMIĘ 1]          [IMIĘ 2]          [IMIĘ 3]          [IMIĘ 4]
[ROLA 1]          [ROLA 2]          [ROLA 3]          [ROLA 4]
ML / Data Eng     Backend / ETL     Frontend / UX     Biznes / Pitch
```
*(karty `#1e293b`, avatar placeholder kółko `#334155`)*

**Duże Q&A sekcja:**
```
Wielka czcionka:  "Q & A"
                  kolor: #ef4444, font 80px bold
```

**Bottom strip:**
```
GitHub: [link]  |  Demo: streamlit run app/main.py  |  Data: EUROCONTROL OPDI
```

---

## BONUS: SLAJD TYTUŁOWY (opcjonalny, przed slajdem 1)

**Tytuł główny:** `MRO Intelligence Platform`
**Podtytuł:** `Wczesne wykrywanie C-checków Boeing 737 · Europa · LOTAMS`
**Visual:** Sylwetka samolotu B737 (ciemna, duża) na tle mapy Europy z punktami MRO (świecące kółka). Tło: gradient `#0f172a → #0d1526`.
**Hackathon badge:** `✈️ MRO Hackathon 2026`

---

## NOTATKI DLA GENERATORA PREZENTACJI

1. **NIE** używaj białego tła — dark theme przez cały deck
2. **NIE** zamieniaj liczb na przybliżenia — każda liczba jest zweryfikowana
3. Każdy slajd powinien mieć `✈️ MRO Intelligence` jako watermark logo (lewy górny, mały)
4. Przejście między slajdami: fade lub slide (bez fancy efektów)
5. Screenshoty demo: zrób je z uruchomionego `streamlit run app/main.py` — szczególnie Fleet Priority i Aircraft Timeline
6. Slajd 5 (ML): wykres feature importance generuj z `output/feature_importance.csv` kolumna `importance_gain`
7. Forma prezentacji: 4 minuty total → slajdy 1-5 + część demo to ~2 min pitch, slajd 6 = 2 min live demo

